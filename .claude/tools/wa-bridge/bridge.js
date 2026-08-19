#!/usr/bin/env node
/**
 * Hermes Agent WhatsApp Bridge
 *
 * Standalone Node.js process that connects to WhatsApp via Baileys
 * and exposes HTTP endpoints for the Python gateway adapter.
 *
 * Endpoints (matches gateway/platforms/whatsapp.py expectations):
 *   GET  /messages       - Long-poll for new incoming messages (DRAINS the queue)
 *   POST /send           - Send a message { chatId, message, replyTo? }
 *   POST /edit           - Edit a sent message { chatId, messageId, message }
 *   POST /send-media     - Send media natively { chatId, filePath, mediaType?, caption?, fileName? }
 *   POST /typing         - Send typing indicator { chatId }
 *   GET  /chat/:id       - Get chat info
 *   GET  /health         - Health check
 *
 * CLI extensions (added for tools/wa_client.py — read-only unless noted):
 *   GET  /qr                  - Current pairing QR (raw string + ASCII), null when paired
 *   GET  /chats               - Known chats w/ last message + unread (bridge-local store)
 *   GET  /chat/:id/messages   - Message history for one chat (bridge-local store)
 *   GET  /contacts            - Known contacts (bridge-local store)
 *   GET  /groups              - Groups the account participates in (live, groupFetchAllParticipating)
 *   GET  /search?q=           - Full-text search over the bridge-local message store
 *   POST /mark-read           - Mark chat/messages as read { chatId, messageIds? }
 *   GET  /media/:messageId    - Download media of a cached message to disk
 *   GET  /profile/:jid        - Profile picture / status / business profile / group metadata
 *
 * IMPORTANT — store semantics:
 *   Baileys 7.x removed `makeInMemoryStore`, so this bridge keeps its OWN
 *   lightweight store (chats/contacts/message text) persisted to disk.  It only
 *   contains what the socket has actually seen: messages that arrived while the
 *   bridge was running, plus whatever WhatsApp delivered through history sync
 *   (`syncFullHistory` is false by default → recent messages only).  It is NOT a
 *   full export of your phone's history.  Set WA_STORE=off to disable it.
 *
 * Usage:
 *   node bridge.js --port 3000 --session ~/.hermes/whatsapp/session
 *
 * Env (CLI extensions):
 *   WA_STORE=off              - disable the local store (search/chats return 501)
 *   WA_STORE_DIR              - store location (default: <session>/../store)
 *   WA_STORE_MAX_MESSAGES     - message cap in the store (default 5000)
 *   WA_RAW_CACHE_MAX          - in-memory raw messages kept for media download (default 500)
 *   WA_MEDIA_DIR              - download dir for GET /media (default: <store>/media)
 */

import { makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, downloadMediaMessage } from '@whiskeysockets/baileys';
import express from 'express';
import { Boom } from '@hapi/boom';
import pino from 'pino';
import path from 'path';
import { mkdirSync, readFileSync, writeFileSync, existsSync, readdirSync, unlinkSync } from 'fs';
import { randomBytes } from 'crypto';
import { execSync } from 'child_process';
import { tmpdir } from 'os';
import qrcode from 'qrcode-terminal';
import { matchesAllowedUser, parseAllowedUsers } from './allowlist.js';

// Parse CLI args
const args = process.argv.slice(2);
function getArg(name, defaultVal) {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 && args[idx + 1] ? args[idx + 1] : defaultVal;
}

const WHATSAPP_DEBUG =
  typeof process !== 'undefined' &&
  process.env &&
  typeof process.env.WHATSAPP_DEBUG === 'string' &&
  ['1', 'true', 'yes', 'on'].includes(process.env.WHATSAPP_DEBUG.toLowerCase());

const PORT = parseInt(getArg('port', '3000'), 10);
const SESSION_DIR = getArg('session', path.join(process.env.HOME || '~', '.hermes', 'whatsapp', 'session'));
const IMAGE_CACHE_DIR = path.join(process.env.HOME || '~', '.hermes', 'image_cache');
const DOCUMENT_CACHE_DIR = path.join(process.env.HOME || '~', '.hermes', 'document_cache');
const AUDIO_CACHE_DIR = path.join(process.env.HOME || '~', '.hermes', 'audio_cache');
const PAIR_ONLY = args.includes('--pair-only');
const WHATSAPP_MODE = getArg('mode', process.env.WHATSAPP_MODE || 'self-chat'); // "bot" or "self-chat"
const ALLOWED_USERS = parseAllowedUsers(process.env.WHATSAPP_ALLOWED_USERS || '');
const DEFAULT_REPLY_PREFIX = '⚕ *Hermes Agent*\n────────────\n';
const REPLY_PREFIX = process.env.WHATSAPP_REPLY_PREFIX === undefined
  ? DEFAULT_REPLY_PREFIX
  : process.env.WHATSAPP_REPLY_PREFIX.replace(/\\n/g, '\n');
const MAX_MESSAGE_LENGTH = parseInt(process.env.WHATSAPP_MAX_MESSAGE_LENGTH || '4096', 10);
const CHUNK_DELAY_MS = parseInt(process.env.WHATSAPP_CHUNK_DELAY_MS || '300', 10);

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function formatOutgoingMessage(message) {
  // In bot mode, messages come from a different number so the prefix is
  // redundant — the sender identity is already clear.  Only prepend in
  // self-chat mode where bot and user share the same number.
  if (WHATSAPP_MODE !== 'self-chat') return message;
  return REPLY_PREFIX ? `${REPLY_PREFIX}${message}` : message;
}

function splitLongMessage(message, maxLength = MAX_MESSAGE_LENGTH) {
  const text = String(message || '');
  if (!text) return [];
  if (!Number.isFinite(maxLength) || maxLength < 1 || text.length <= maxLength) {
    return [text];
  }

  const chunks = [];
  let remaining = text;
  while (remaining.length > maxLength) {
    let splitAt = remaining.lastIndexOf('\n', maxLength);
    if (splitAt < Math.floor(maxLength / 2)) {
      splitAt = remaining.lastIndexOf(' ', maxLength);
    }
    if (splitAt < 1) splitAt = maxLength;

    chunks.push(remaining.slice(0, splitAt).trimEnd());
    remaining = remaining.slice(splitAt).trimStart();
  }
  if (remaining) chunks.push(remaining);
  return chunks;
}

function trackSentMessageId(sent) {
  if (sent?.key?.id) {
    recentlySentIds.add(sent.key.id);
    if (recentlySentIds.size > MAX_RECENT_IDS) {
      recentlySentIds.delete(recentlySentIds.values().next().value);
    }
  }
}

function normalizeWhatsAppId(value) {
  if (!value) return '';
  return String(value).replace(':', '@');
}

function getMessageContent(msg) {
  const content = msg?.message || {};
  if (content.ephemeralMessage?.message) return content.ephemeralMessage.message;
  if (content.viewOnceMessage?.message) return content.viewOnceMessage.message;
  if (content.viewOnceMessageV2?.message) return content.viewOnceMessageV2.message;
  if (content.documentWithCaptionMessage?.message) return content.documentWithCaptionMessage.message;
  if (content.templateMessage?.hydratedTemplate) return content.templateMessage.hydratedTemplate;
  if (content.buttonsMessage) return content.buttonsMessage;
  if (content.listMessage) return content.listMessage;
  return content;
}

function getContextInfo(messageContent) {
  if (!messageContent || typeof messageContent !== 'object') return {};
  for (const value of Object.values(messageContent)) {
    if (value && typeof value === 'object' && value.contextInfo) {
      return value.contextInfo;
    }
  }
  return {};
}

mkdirSync(SESSION_DIR, { recursive: true });

// Build LID → phone reverse map from session files (lid-mapping-{phone}.json)
function buildLidMap() {
  const map = {};
  try {
    for (const f of readdirSync(SESSION_DIR)) {
      const m = f.match(/^lid-mapping-(\d+)\.json$/);
      if (!m) continue;
      const phone = m[1];
      const lid = JSON.parse(readFileSync(path.join(SESSION_DIR, f), 'utf8'));
      if (lid) map[String(lid)] = phone;
    }
  } catch {}
  return map;
}
let lidToPhone = buildLidMap();

const logger = pino({ level: 'warn' });

// ============================================================
// Bridge-local store (Baileys 7.x has no makeInMemoryStore)
// ============================================================
const STORE_ENABLED = !['0', 'false', 'off', 'no'].includes(
  String(process.env.WA_STORE || '').trim().toLowerCase()
);
const STORE_DIR = getArg('store', process.env.WA_STORE_DIR || path.join(SESSION_DIR, '..', 'store'));
const STORE_FILE = path.join(STORE_DIR, 'store.json');
const STORE_MAX_MESSAGES = parseInt(process.env.WA_STORE_MAX_MESSAGES || '5000', 10);
const RAW_CACHE_MAX = parseInt(process.env.WA_RAW_CACHE_MAX || '500', 10);
const MEDIA_DOWNLOAD_DIR = process.env.WA_MEDIA_DIR || path.join(STORE_DIR, 'media');

const store = {
  chats: new Map(),     // jid -> { id, name, isGroup, unreadCount, lastMessage, timestamp }
  contacts: new Map(),  // jid -> { id, name, notify, verifiedName, source }
  messages: [],         // capped array of light message records (oldest first)
};
// Raw Baileys messages kept in memory only — needed for media download and
// for building read receipts. Capped; older entries are evicted.
const rawMessages = new Map();

let storeDirty = false;
let storeSaveTimer = null;
let currentQR = null;
let currentQRAscii = null;
let currentQRAt = null;

function toEpochSeconds(value) {
  if (value === null || value === undefined) return 0;
  if (typeof value === 'number') return Math.floor(value);
  if (typeof value === 'string') return parseInt(value, 10) || 0;
  // Baileys sometimes hands back a Long ({ low, high, unsigned })
  if (typeof value === 'object') {
    if (typeof value.toNumber === 'function') {
      try { return Math.floor(value.toNumber()); } catch { return 0; }
    }
    if (typeof value.low === 'number') return value.low;
  }
  return 0;
}

function loadStore() {
  if (!STORE_ENABLED) return;
  try {
    if (!existsSync(STORE_FILE)) return;
    const data = JSON.parse(readFileSync(STORE_FILE, 'utf8'));
    for (const chat of data.chats || []) if (chat?.id) store.chats.set(chat.id, chat);
    for (const contact of data.contacts || []) if (contact?.id) store.contacts.set(contact.id, contact);
    if (Array.isArray(data.messages)) {
      store.messages = data.messages.slice(-STORE_MAX_MESSAGES);
    }
    console.log(`💾 Store loaded: ${store.chats.size} chats, ${store.contacts.size} contacts, ${store.messages.length} messages`);
  } catch (err) {
    console.warn('[bridge] Failed to load store (starting empty):', err.message);
  }
}

function saveStoreNow() {
  if (!STORE_ENABLED || !storeDirty) return;
  try {
    mkdirSync(STORE_DIR, { recursive: true });
    const payload = {
      savedAt: Date.now(),
      chats: Array.from(store.chats.values()),
      contacts: Array.from(store.contacts.values()),
      messages: store.messages.slice(-STORE_MAX_MESSAGES),
    };
    writeFileSync(STORE_FILE, JSON.stringify(payload), 'utf8');
    storeDirty = false;
  } catch (err) {
    console.warn('[bridge] Failed to save store:', err.message);
  }
}

function markStoreDirty() {
  if (!STORE_ENABLED) return;
  storeDirty = true;
  if (storeSaveTimer) return;
  storeSaveTimer = setTimeout(() => {
    storeSaveTimer = null;
    saveStoreNow();
  }, 5000);
  if (typeof storeSaveTimer.unref === 'function') storeSaveTimer.unref();
}

function upsertChat(jid, patch = {}) {
  if (!STORE_ENABLED || !jid) return null;
  const existing = store.chats.get(jid) || {
    id: jid,
    name: '',
    isGroup: jid.endsWith('@g.us'),
    unreadCount: 0,
    lastMessage: null,
    timestamp: 0,
  };
  const merged = { ...existing, ...patch };
  merged.id = jid;
  merged.isGroup = jid.endsWith('@g.us');
  if (!merged.name && existing.name) merged.name = existing.name;
  store.chats.set(jid, merged);
  markStoreDirty();
  return merged;
}

function upsertContact(jid, patch = {}) {
  if (!STORE_ENABLED || !jid) return;
  const existing = store.contacts.get(jid) || { id: jid, name: '', notify: '', verifiedName: '', source: '' };
  const merged = { ...existing };
  for (const [key, value] of Object.entries(patch)) {
    if (value !== undefined && value !== null && value !== '') merged[key] = value;
  }
  merged.id = jid;
  store.contacts.set(jid, merged);
  markStoreDirty();
}

function contactDisplayName(jid) {
  const contact = store.contacts.get(jid);
  if (contact) return contact.name || contact.notify || contact.verifiedName || '';
  return '';
}

/** Best-effort plain-text extraction for the store/search index. */
function extractText(messageContent) {
  const c = messageContent || {};
  return (
    c.conversation ||
    c.extendedTextMessage?.text ||
    c.imageMessage?.caption ||
    c.videoMessage?.caption ||
    c.documentMessage?.caption ||
    c.documentWithCaptionMessage?.message?.documentMessage?.caption ||
    c.buttonsResponseMessage?.selectedDisplayText ||
    c.listResponseMessage?.title ||
    c.templateButtonReplyMessage?.selectedDisplayText ||
    (c.reactionMessage?.text ? `[reaction ${c.reactionMessage.text}]` : '') ||
    ''
  );
}

function detectMediaType(messageContent) {
  const c = messageContent || {};
  if (c.imageMessage) return 'image';
  if (c.videoMessage) return 'video';
  if (c.pttMessage) return 'ptt';
  if (c.audioMessage) return 'audio';
  if (c.documentMessage || c.documentWithCaptionMessage) return 'document';
  if (c.stickerMessage) return 'sticker';
  return '';
}

function cacheRawMessage(msg) {
  const id = msg?.key?.id;
  if (!id) return;
  rawMessages.set(id, msg);
  while (rawMessages.size > RAW_CACHE_MAX) {
    const oldest = rawMessages.keys().next().value;
    rawMessages.delete(oldest);
  }
}

/**
 * Record a message into the local store. Never throws — the store is a
 * best-effort convenience layer and must not break message delivery.
 */
function recordMessage(msg, { bumpUnread = true } = {}) {
  if (!STORE_ENABLED) return;
  try {
    const key = msg?.key;
    if (!key?.id || !key.remoteJid) return;
    const chatId = key.remoteJid;
    if (chatId === 'status@broadcast') return;

    const content = getMessageContent(msg);
    const text = extractText(content);
    const mediaType = detectMediaType(content);
    if (!text && !mediaType) return;

    const senderId = key.participant || (key.fromMe ? normalizeWhatsAppId(sock?.user?.id) : chatId);
    const record = {
      id: key.id,
      chatId,
      senderId,
      senderName: msg.pushName || contactDisplayName(senderId) || String(senderId).replace(/@.*/, ''),
      fromMe: !!key.fromMe,
      text,
      mediaType,
      timestamp: toEpochSeconds(msg.messageTimestamp),
    };

    // Replace on re-delivery instead of duplicating
    const dupIdx = store.messages.findIndex((m) => m.id === record.id && m.chatId === record.chatId);
    if (dupIdx !== -1) {
      store.messages[dupIdx] = record;
    } else {
      store.messages.push(record);
      if (store.messages.length > STORE_MAX_MESSAGES) {
        store.messages.splice(0, store.messages.length - STORE_MAX_MESSAGES);
      }
    }

    cacheRawMessage(msg);

    if (!record.fromMe && msg.pushName) {
      upsertContact(senderId, { notify: msg.pushName, source: 'pushName' });
    }

    const chat = store.chats.get(chatId);
    const unread = record.fromMe
      ? 0
      : (bumpUnread ? (chat?.unreadCount || 0) + 1 : (chat?.unreadCount || 0));
    upsertChat(chatId, {
      name: chat?.name || (chatId.endsWith('@g.us') ? '' : (msg.pushName || contactDisplayName(chatId) || '')),
      unreadCount: unread,
      timestamp: record.timestamp,
      lastMessage: {
        id: record.id,
        text: record.text || (record.mediaType ? `[${record.mediaType}]` : ''),
        fromMe: record.fromMe,
        senderName: record.senderName,
        timestamp: record.timestamp,
      },
    });
    markStoreDirty();
  } catch (err) {
    if (WHATSAPP_DEBUG) console.warn('[bridge] recordMessage failed:', err.message);
  }
}

function storeCoverage() {
  const timestamps = store.messages.map((m) => m.timestamp).filter(Boolean);
  return {
    enabled: STORE_ENABLED,
    chats: store.chats.size,
    contacts: store.contacts.size,
    messages: store.messages.length,
    oldestTimestamp: timestamps.length ? Math.min(...timestamps) : null,
    newestTimestamp: timestamps.length ? Math.max(...timestamps) : null,
    note: 'Bridge-local store: only messages seen while the bridge was running plus whatever WhatsApp history-sync delivered. Not a full phone history export.',
  };
}

loadStore();

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    saveStoreNow();
    process.exit(0);
  });
}
process.on('exit', () => { try { saveStoreNow(); } catch {} });

// Message queue for polling
const messageQueue = [];
const MAX_QUEUE_SIZE = 100;

// Track recently sent message IDs to prevent echo-back loops with media
const recentlySentIds = new Set();
const MAX_RECENT_IDS = 50;

let sock = null;
let connectionState = 'disconnected';

async function startSocket() {
  const { state, saveCreds } = await useMultiFileAuthState(SESSION_DIR);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    logger,
    printQRInTerminal: false,
    browser: ['Hermes Agent', 'Chrome', '120.0'],
    syncFullHistory: false,
    markOnlineOnConnect: false,
    // Required for Baileys 7.x: without this, incoming messages that need
    // E2EE session re-establishment are silently dropped (msg.message === null)
    getMessage: async (key) => {
      // We don't maintain a message store, so return a placeholder.
      // This is enough for Baileys to complete the retry handshake.
      return { conversation: '' };
    },
  });

  sock.ev.on('creds.update', () => { saveCreds(); lidToPhone = buildLidMap(); });

  // ---- Store feeds (best effort; unknown events simply never fire) ----
  if (STORE_ENABLED) {
    sock.ev.on('messaging-history.set', ({ chats = [], contacts = [], messages = [] }) => {
      try {
        for (const chat of chats) {
          if (!chat?.id) continue;
          upsertChat(chat.id, {
            name: chat.name || chat.subject || '',
            unreadCount: typeof chat.unreadCount === 'number' ? chat.unreadCount : undefined,
            timestamp: toEpochSeconds(chat.conversationTimestamp) || undefined,
          });
        }
        for (const contact of contacts) {
          if (!contact?.id) continue;
          upsertContact(contact.id, {
            name: contact.name || '',
            notify: contact.notify || '',
            verifiedName: contact.verifiedName || '',
            source: 'history-sync',
          });
        }
        for (const msg of messages) recordMessage(msg, { bumpUnread: false });
        console.log(`💾 History sync: +${chats.length} chats, +${contacts.length} contacts, +${messages.length} messages`);
      } catch (err) {
        console.warn('[bridge] history sync store update failed:', err.message);
      }
    });

    sock.ev.on('chats.upsert', (chats) => {
      for (const chat of chats || []) {
        if (!chat?.id) continue;
        upsertChat(chat.id, {
          name: chat.name || chat.subject || '',
          unreadCount: typeof chat.unreadCount === 'number' ? chat.unreadCount : undefined,
          timestamp: toEpochSeconds(chat.conversationTimestamp) || undefined,
        });
      }
    });

    sock.ev.on('chats.update', (updates) => {
      for (const update of updates || []) {
        if (!update?.id) continue;
        const patch = {};
        if (update.name || update.subject) patch.name = update.name || update.subject;
        if (typeof update.unreadCount === 'number') patch.unreadCount = Math.max(0, update.unreadCount);
        if (update.conversationTimestamp) patch.timestamp = toEpochSeconds(update.conversationTimestamp);
        if (Object.keys(patch).length) upsertChat(update.id, patch);
      }
    });

    const onContacts = (contacts) => {
      for (const contact of contacts || []) {
        if (!contact?.id) continue;
        upsertContact(contact.id, {
          name: contact.name || '',
          notify: contact.notify || '',
          verifiedName: contact.verifiedName || '',
          source: 'contacts-event',
        });
      }
    };
    sock.ev.on('contacts.upsert', onContacts);
    sock.ev.on('contacts.update', onContacts);
  }

  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      currentQR = qr;
      currentQRAt = Date.now();
      // Capture the ASCII rendering too so GET /qr can serve it to the CLI.
      try {
        qrcode.generate(qr, { small: true }, (ascii) => { currentQRAscii = ascii; });
      } catch { currentQRAscii = null; }
      console.log('\n📱 Scan this QR code with WhatsApp on your phone:\n');
      qrcode.generate(qr, { small: true });
      console.log('\nWaiting for scan...\n');
    }

    if (connection === 'close') {
      const reason = new Boom(lastDisconnect?.error)?.output?.statusCode;
      connectionState = 'disconnected';

      if (reason === DisconnectReason.loggedOut) {
        console.log('❌ Logged out. Delete session and restart to re-authenticate.');
        process.exit(1);
      } else {
        // 515 = restart requested (common after pairing). Always reconnect.
        if (reason === 515) {
          console.log('↻ WhatsApp requested restart (code 515). Reconnecting...');
        } else {
          console.log(`⚠️  Connection closed (reason: ${reason}). Reconnecting in 3s...`);
        }
        setTimeout(startSocket, reason === 515 ? 1000 : 3000);
      }
    } else if (connection === 'open') {
      connectionState = 'connected';
      currentQR = null;
      currentQRAscii = null;
      console.log('✅ WhatsApp connected!');
      if (PAIR_ONLY) {
        console.log('✅ Pairing complete. Credentials saved.');
        // Give Baileys a moment to flush creds, then exit cleanly
        setTimeout(() => process.exit(0), 2000);
      }
    }
  });

  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    // In self-chat mode, your own messages commonly arrive as 'append' rather
    // than 'notify'. Accept both and filter agent echo-backs below.
    if (type !== 'notify' && type !== 'append') return;

    const botIds = Array.from(new Set([
      normalizeWhatsAppId(sock.user?.id),
      normalizeWhatsAppId(sock.user?.lid),
    ].filter(Boolean)));

    for (const msg of messages) {
      if (!msg.message) continue;

      // Feed the bridge-local store first: the CLI needs every chat/message,
      // independent of the gateway's mode/allowlist filtering below.
      recordMessage(msg);

      const chatId = msg.key.remoteJid;
      if (WHATSAPP_DEBUG) {
        try {
          console.log(JSON.stringify({
            event: 'upsert', type,
            fromMe: !!msg.key.fromMe, chatId,
            senderId: msg.key.participant || chatId,
            messageKeys: Object.keys(msg.message || {}),
          }));
        } catch {}
      }
      const senderId = msg.key.participant || chatId;
      const isGroup = chatId.endsWith('@g.us');
      const senderNumber = senderId.replace(/@.*/, '');

      // Handle fromMe messages based on mode
      if (msg.key.fromMe) {
        if (isGroup || chatId.includes('status')) continue;

        if (WHATSAPP_MODE === 'bot') {
          // Bot mode: separate number. ALL fromMe are echo-backs of our own replies — skip.
          continue;
        }

        // Self-chat mode: only allow messages in the user's own self-chat
        // WhatsApp now uses LID (Linked Identity Device) format: 67427329167522@lid
        // AND classic format: 34652029134@s.whatsapp.net
        // sock.user has both: { id: "number:10@s.whatsapp.net", lid: "lid_number:10@lid" }
        const myNumber = (sock.user?.id || '').replace(/:.*@/, '@').replace(/@.*/, '');
        const myLid = (sock.user?.lid || '').replace(/:.*@/, '@').replace(/@.*/, '');
        const chatNumber = chatId.replace(/@.*/, '');
        const isSelfChat = (myNumber && chatNumber === myNumber) || (myLid && chatNumber === myLid);
        if (!isSelfChat) continue;
      }

      // Handle !fromMe messages (from other people) based on mode.
      // Self-chat mode only responds to the user's own messages to
      // themselves — stranger DMs / group pings must never reach the
      // Python gateway, otherwise a pairing-code reply fires in response
      // to arbitrary incoming messages (#8389).
      if (!msg.key.fromMe) {
        if (WHATSAPP_MODE === 'self-chat') {
          try {
            console.log(JSON.stringify({
              event: 'ignored',
              reason: 'self_chat_mode_rejects_non_self',
              chatId,
              senderId,
            }));
          } catch {}
          continue;
        }
        if (!matchesAllowedUser(senderId, ALLOWED_USERS, SESSION_DIR)) {
          try {
            console.log(JSON.stringify({
              event: 'ignored',
              reason: 'allowlist_mismatch',
              chatId,
              senderId,
            }));
          } catch {}
          continue;
        }
      }

      const messageContent = getMessageContent(msg);
      const contextInfo = getContextInfo(messageContent);
      const mentionedIds = Array.from(new Set((contextInfo?.mentionedJid || []).map(normalizeWhatsAppId).filter(Boolean)));
      const quotedParticipant = normalizeWhatsAppId(contextInfo?.participant || contextInfo?.remoteJid || '');

      // Extract message body
      let body = '';
      let hasMedia = false;
      let mediaType = '';
      const mediaUrls = [];

      if (messageContent.conversation) {
        body = messageContent.conversation;
      } else if (messageContent.extendedTextMessage?.text) {
        body = messageContent.extendedTextMessage.text;
      } else if (messageContent.imageMessage) {
        body = messageContent.imageMessage.caption || '';
        hasMedia = true;
        mediaType = 'image';
        try {
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          const mime = messageContent.imageMessage.mimetype || 'image/jpeg';
          const extMap = { 'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp', 'image/gif': '.gif' };
          const ext = extMap[mime] || '.jpg';
          mkdirSync(IMAGE_CACHE_DIR, { recursive: true });
          const filePath = path.join(IMAGE_CACHE_DIR, `img_${randomBytes(6).toString('hex')}${ext}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
        } catch (err) {
          console.error('[bridge] Failed to download image:', err.message);
        }
      } else if (messageContent.videoMessage) {
        body = messageContent.videoMessage.caption || '';
        hasMedia = true;
        mediaType = 'video';
        try {
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          const mime = messageContent.videoMessage.mimetype || 'video/mp4';
          const ext = mime.includes('mp4') ? '.mp4' : '.mkv';
          mkdirSync(DOCUMENT_CACHE_DIR, { recursive: true });
          const filePath = path.join(DOCUMENT_CACHE_DIR, `vid_${randomBytes(6).toString('hex')}${ext}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
        } catch (err) {
          console.error('[bridge] Failed to download video:', err.message);
        }
      } else if (messageContent.audioMessage || messageContent.pttMessage) {
        hasMedia = true;
        mediaType = messageContent.pttMessage ? 'ptt' : 'audio';
        try {
          const audioMsg = messageContent.pttMessage || messageContent.audioMessage;
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          const mime = audioMsg.mimetype || 'audio/ogg';
          const ext = mime.includes('ogg') ? '.ogg' : mime.includes('mp4') ? '.m4a' : '.ogg';
          mkdirSync(AUDIO_CACHE_DIR, { recursive: true });
          const filePath = path.join(AUDIO_CACHE_DIR, `aud_${randomBytes(6).toString('hex')}${ext}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
        } catch (err) {
          console.error('[bridge] Failed to download audio:', err.message);
        }
      } else if (messageContent.documentMessage) {
        body = messageContent.documentMessage.caption || '';
        hasMedia = true;
        mediaType = 'document';
        const fileName = messageContent.documentMessage.fileName || 'document';
        try {
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          mkdirSync(DOCUMENT_CACHE_DIR, { recursive: true });
          const safeFileName = path.basename(fileName).replace(/[^a-zA-Z0-9._-]/g, '_');
          const filePath = path.join(DOCUMENT_CACHE_DIR, `doc_${randomBytes(6).toString('hex')}_${safeFileName}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
        } catch (err) {
          console.error('[bridge] Failed to download document:', err.message);
        }
      }

      // For media without caption, use a placeholder so the API message is never empty
      if (hasMedia && !body) {
        body = `[${mediaType} received]`;
      }

      // Ignore Hermes' own reply messages in self-chat mode to avoid loops.
      if (msg.key.fromMe && ((REPLY_PREFIX && body.startsWith(REPLY_PREFIX)) || recentlySentIds.has(msg.key.id))) {
        if (WHATSAPP_DEBUG) {
          try { console.log(JSON.stringify({ event: 'ignored', reason: 'agent_echo', chatId, messageId: msg.key.id })); } catch {}
        }
        continue;
      }

      // Skip empty messages
      if (!body && !hasMedia) {
        if (WHATSAPP_DEBUG) {
          try { 
            console.log(JSON.stringify({ event: 'ignored', reason: 'empty', chatId, messageKeys: Object.keys(msg.message || {}) })); 
          } catch (err) {
            console.error('Failed to log empty message event:', err);
          }
        }
        continue;
      }

      const event = {
        messageId: msg.key.id,
        chatId,
        senderId,
        senderName: msg.pushName || senderNumber,
        chatName: isGroup ? (chatId.split('@')[0]) : (msg.pushName || senderNumber),
        isGroup,
        body,
        hasMedia,
        mediaType,
        mediaUrls,
        mentionedIds,
        quotedParticipant,
        botIds,
        timestamp: msg.messageTimestamp,
      };

      messageQueue.push(event);
      if (messageQueue.length > MAX_QUEUE_SIZE) {
        messageQueue.shift();
      }
    }
  });
}

// HTTP server
const app = express();
app.use(express.json());

// Host-header validation — defends against DNS rebinding.
// The bridge binds loopback-only (127.0.0.1) but a victim browser on
// the same machine could be tricked into fetching from an attacker
// hostname that TTL-flips to 127.0.0.1. Reject any request whose Host
// header doesn't resolve to a loopback alias.
// See GHSA-ppp5-vxwm-4cf7.
const _ACCEPTED_HOST_VALUES = new Set([
  'localhost',
  '127.0.0.1',
  '[::1]',
  '::1',
]);

app.use((req, res, next) => {
  const raw = (req.headers.host || '').trim();
  if (!raw) {
    return res.status(400).json({ error: 'Missing Host header' });
  }
  // Strip port suffix: "localhost:3000" → "localhost"
  const hostOnly = (raw.includes(':')
    ? raw.substring(0, raw.lastIndexOf(':'))
    : raw
  ).replace(/^\[|\]$/g, '').toLowerCase();
  if (!_ACCEPTED_HOST_VALUES.has(hostOnly)) {
    return res.status(400).json({
      error: 'Invalid Host header. Bridge accepts loopback hosts only.',
    });
  }
  next();
});

// Poll for new messages (long-poll style)
app.get('/messages', (req, res) => {
  const msgs = messageQueue.splice(0, messageQueue.length);
  res.json(msgs);
});

// Send a message
app.post('/send', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }

  const { chatId, message, replyTo } = req.body;
  if (!chatId || !message) {
    return res.status(400).json({ error: 'chatId and message are required' });
  }

  try {
    const chunks = splitLongMessage(formatOutgoingMessage(message));
    const messageIds = [];
    for (let i = 0; i < chunks.length; i += 1) {
      const sent = await sock.sendMessage(chatId, { text: chunks[i] });
      trackSentMessageId(sent);
      if (sent?.key?.id) messageIds.push(sent.key.id);
      if (chunks.length > 1 && i < chunks.length - 1) {
        await sleep(CHUNK_DELAY_MS);
      }
    }

    res.json({
      success: true,
      messageId: messageIds[messageIds.length - 1],
      messageIds,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Edit a previously sent message
app.post('/edit', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }

  const { chatId, messageId, message } = req.body;
  if (!chatId || !messageId || !message) {
    return res.status(400).json({ error: 'chatId, messageId, and message are required' });
  }

  try {
    const key = { id: messageId, fromMe: true, remoteJid: chatId };
    const chunks = splitLongMessage(formatOutgoingMessage(message));
    const messageIds = [];

    await sock.sendMessage(chatId, { text: chunks[0], edit: key });
    if (chunks.length > 1) {
      for (let i = 1; i < chunks.length; i += 1) {
        const sent = await sock.sendMessage(chatId, { text: chunks[i] });
        trackSentMessageId(sent);
        if (sent?.key?.id) messageIds.push(sent.key.id);
        if (i < chunks.length - 1) {
          await sleep(CHUNK_DELAY_MS);
        }
      }
    }

    res.json({ success: true, messageIds });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// MIME type map and media type inference for /send-media
const MIME_MAP = {
  jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png',
  webp: 'image/webp', gif: 'image/gif',
  mp4: 'video/mp4', mov: 'video/quicktime', avi: 'video/x-msvideo',
  mkv: 'video/x-matroska', '3gp': 'video/3gpp',
  pdf: 'application/pdf',
  doc: 'application/msword',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
};

function inferMediaType(ext) {
  if (['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext)) return 'image';
  if (['mp4', 'mov', 'avi', 'mkv', '3gp'].includes(ext)) return 'video';
  if (['ogg', 'opus', 'mp3', 'wav', 'm4a'].includes(ext)) return 'audio';
  return 'document';
}

// Send media (image, video, document) natively
app.post('/send-media', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }

  const { chatId, filePath, mediaType, caption, fileName } = req.body;
  if (!chatId || !filePath) {
    return res.status(400).json({ error: 'chatId and filePath are required' });
  }

  try {
    if (!existsSync(filePath)) {
      return res.status(404).json({ error: `File not found: ${filePath}` });
    }

    const buffer = readFileSync(filePath);
    const ext = filePath.toLowerCase().split('.').pop();
    const type = mediaType || inferMediaType(ext);
    let msgPayload;

    switch (type) {
      case 'image':
        msgPayload = { image: buffer, caption: caption || undefined, mimetype: MIME_MAP[ext] || 'image/jpeg' };
        break;
      case 'video':
        msgPayload = { video: buffer, caption: caption || undefined, mimetype: MIME_MAP[ext] || 'video/mp4' };
        break;
      case 'audio': {
        // WhatsApp only renders a native voice bubble (ptt) when the file is ogg/opus.
        // If the caller passes mp3, wav, m4a etc. (e.g. from Edge TTS / NeuTTS),
        // silently convert to ogg/opus via ffmpeg so ptt is always honoured.
        let audioBuffer = buffer;
        let audioExt = ext;
        const needsConversion = !['ogg', 'opus'].includes(ext);
        let tmpPath = null;
        if (needsConversion) {
          tmpPath = path.join(tmpdir(), `hermes_voice_${randomBytes(6).toString('hex')}.ogg`);
          try {
            execSync(
              `ffmpeg -y -i ${JSON.stringify(filePath)} -ar 48000 -ac 1 -c:a libopus ${JSON.stringify(tmpPath)}`,
              { timeout: 30000, stdio: 'pipe' }
            );
            audioBuffer = readFileSync(tmpPath);
            audioExt = 'ogg';
          } catch (convErr) {
            // ffmpeg not available or conversion failed — fall back to original format
            console.warn('[bridge] ffmpeg conversion failed, sending as file attachment:', convErr.message);
          } finally {
            try { if (tmpPath && existsSync(tmpPath)) unlinkSync(tmpPath); } catch (_) {}
          }
        }
        const audioMime = (audioExt === 'ogg' || audioExt === 'opus') ? 'audio/ogg; codecs=opus' : 'audio/mpeg';
        msgPayload = { audio: audioBuffer, mimetype: audioMime, ptt: audioExt === 'ogg' || audioExt === 'opus' };
        break;
      }
      case 'document':
      default:
        msgPayload = {
          document: buffer,
          fileName: fileName || path.basename(filePath),
          caption: caption || undefined,
          mimetype: MIME_MAP[ext] || 'application/octet-stream',
        };
        break;
    }

    const sent = await sock.sendMessage(chatId, msgPayload);

    trackSentMessageId(sent);

    res.json({ success: true, messageId: sent?.key?.id });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Typing indicator
app.post('/typing', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected' });
  }

  const { chatId } = req.body;
  if (!chatId) return res.status(400).json({ error: 'chatId required' });

  try {
    await sock.sendPresenceUpdate('composing', chatId);
    res.json({ success: true });
  } catch (err) {
    res.json({ success: false });
  }
});

// Chat info
app.get('/chat/:id', async (req, res) => {
  const chatId = req.params.id;
  const isGroup = chatId.endsWith('@g.us');

  // Only query WhatsApp when the socket is actually connected — otherwise
  // groupMetadata() never resolves and the HTTP request hangs forever.
  if (isGroup && sock && connectionState === 'connected') {
    try {
      const metadata = await sock.groupMetadata(chatId);
      return res.json({
        name: metadata.subject,
        isGroup: true,
        participants: metadata.participants.map(p => p.id),
      });
    } catch {
      // Fall through to default
    }
  }

  res.json({
    name: chatId.replace(/@.*/, ''),
    isGroup,
    participants: [],
  });
});

// ============================================================
// CLI extensions (tools/wa_client.py)
// ============================================================

const STORE_DISABLED_PAYLOAD = {
  error: 'Bridge-local store is disabled (WA_STORE=off)',
  hint: 'Restart the bridge without WA_STORE=off to enable chats/search/history endpoints.',
};

let groupCache = { at: 0, data: null };

async function fetchGroups(force = false) {
  if (!sock || connectionState !== 'connected') return null;
  if (typeof sock.groupFetchAllParticipating !== 'function') return undefined; // unsupported
  if (!force && groupCache.data && Date.now() - groupCache.at < 60000) return groupCache.data;
  const data = await sock.groupFetchAllParticipating();
  groupCache = { at: Date.now(), data };
  for (const [jid, meta] of Object.entries(data || {})) {
    if (meta?.subject) upsertChat(jid, { name: meta.subject });
  }
  return data;
}

/** Resolve a user-supplied chat id to the ids actually present in the store. */
function resolveChatIds(input) {
  if (!input) return [];
  if (store.chats.has(input) || store.messages.some((m) => m.chatId === input)) return [input];
  const bare = String(input).replace(/@.*/, '').replace(/^\+/, '');
  const matches = new Set();
  for (const id of store.chats.keys()) {
    if (id.replace(/@.*/, '') === bare) matches.add(id);
  }
  for (const m of store.messages) {
    if (m.chatId.replace(/@.*/, '') === bare) matches.add(m.chatId);
  }
  return matches.size ? Array.from(matches) : [input];
}

function decorateChat(chat) {
  return {
    ...chat,
    name: chat.name || contactDisplayName(chat.id) || String(chat.id).replace(/@.*/, ''),
  };
}

// Current pairing QR (null once paired)
app.get('/qr', (req, res) => {
  res.json({
    connection: connectionState,
    qr: currentQR,
    ascii: currentQRAscii,
    qrAt: currentQRAt,
    user: sock?.user ? { id: sock.user.id, lid: sock.user.lid || null, name: sock.user.name || null } : null,
  });
});

// Chat list with last message + unread counts
app.get('/chats', async (req, res) => {
  if (!STORE_ENABLED) return res.status(501).json(STORE_DISABLED_PAYLOAD);
  const limit = Math.max(1, parseInt(req.query.limit || '50', 10) || 50);
  const unreadOnly = ['1', 'true', 'yes'].includes(String(req.query.unread || '').toLowerCase());
  const groupsOnly = ['1', 'true', 'yes'].includes(String(req.query.groups || '').toLowerCase());

  try { await fetchGroups(); } catch (err) {
    if (WHATSAPP_DEBUG) console.warn('[bridge] fetchGroups failed:', err.message);
  }

  let chats = Array.from(store.chats.values());
  if (unreadOnly) chats = chats.filter((c) => (c.unreadCount || 0) > 0);
  if (groupsOnly) chats = chats.filter((c) => c.isGroup);
  chats.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));

  res.json({
    total: store.chats.size,
    count: Math.min(chats.length, limit),
    coverage: storeCoverage(),
    chats: chats.slice(0, limit).map(decorateChat),
  });
});

// Message history for one chat (bridge-local store)
app.get('/chat/:id/messages', (req, res) => {
  if (!STORE_ENABLED) return res.status(501).json(STORE_DISABLED_PAYLOAD);
  const limit = Math.max(1, parseInt(req.query.limit || '50', 10) || 50);
  const ids = resolveChatIds(req.params.id);
  const msgs = store.messages.filter((m) => ids.includes(m.chatId));
  msgs.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
  res.json({
    chatId: req.params.id,
    resolvedChatIds: ids,
    total: msgs.length,
    coverage: storeCoverage(),
    messages: msgs.slice(-limit),
  });
});

// Known contacts
app.get('/contacts', (req, res) => {
  if (!STORE_ENABLED) return res.status(501).json(STORE_DISABLED_PAYLOAD);
  const q = String(req.query.q || '').trim().toLowerCase();
  const limit = Math.max(1, parseInt(req.query.limit || '500', 10) || 500);
  let contacts = Array.from(store.contacts.values()).map((c) => ({
    ...c,
    displayName: c.name || c.notify || c.verifiedName || String(c.id).replace(/@.*/, ''),
    number: String(c.id).replace(/@.*/, ''),
  }));
  if (q) {
    contacts = contacts.filter((c) =>
      c.displayName.toLowerCase().includes(q) || c.id.toLowerCase().includes(q)
    );
  }
  contacts.sort((a, b) => a.displayName.localeCompare(b.displayName));
  res.json({ total: store.contacts.size, count: Math.min(contacts.length, limit), coverage: storeCoverage(), contacts: contacts.slice(0, limit) });
});

// Groups the account participates in (live query)
app.get('/groups', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  try {
    const data = await fetchGroups(true);
    if (data === undefined) {
      return res.status(501).json({
        error: 'groupFetchAllParticipating() is not available in this Baileys build',
        hint: 'Use GET /chats?groups=1 (store-based) instead.',
      });
    }
    const groups = Object.entries(data || {}).map(([jid, meta]) => ({
      id: jid,
      subject: meta?.subject || '',
      owner: meta?.owner || null,
      creation: meta?.creation || null,
      desc: meta?.desc || '',
      size: Array.isArray(meta?.participants) ? meta.participants.length : (meta?.size ?? null),
      announce: !!meta?.announce,
      participants: Array.isArray(meta?.participants)
        ? meta.participants.map((p) => ({ id: p.id, admin: p.admin || null }))
        : [],
    }));
    groups.sort((a, b) => a.subject.localeCompare(b.subject));
    res.json({ count: groups.length, groups });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Full-text search over the bridge-local message store
app.get('/search', (req, res) => {
  if (!STORE_ENABLED) {
    return res.status(501).json({
      ...STORE_DISABLED_PAYLOAD,
      error: 'Search unavailable: bridge-local store is disabled (WA_STORE=off). Baileys 7.x ships no built-in message store.',
    });
  }
  const q = String(req.query.q || '').trim();
  if (!q) return res.status(400).json({ error: 'q is required' });
  const limit = Math.max(1, parseInt(req.query.limit || '50', 10) || 50);
  const chatFilter = req.query.chat ? resolveChatIds(String(req.query.chat)) : null;
  const needle = q.toLowerCase();

  let results = store.messages.filter((m) => {
    if (chatFilter && !chatFilter.includes(m.chatId)) return false;
    return (m.text || '').toLowerCase().includes(needle);
  });
  results.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
  results = results.slice(0, limit).map((m) => ({
    ...m,
    chatName: decorateChat(store.chats.get(m.chatId) || { id: m.chatId }).name,
  }));

  res.json({ query: q, count: results.length, source: 'bridge-local-store', coverage: storeCoverage(), results });
});

// Mark a chat (or specific messages) as read
app.post('/mark-read', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  if (typeof sock.readMessages !== 'function') {
    return res.status(501).json({ error: 'readMessages() not available in this Baileys build' });
  }

  const { chatId, messageIds } = req.body || {};
  if (!chatId) return res.status(400).json({ error: 'chatId is required' });

  const ids = resolveChatIds(chatId);
  const targetChat = ids[0];
  let keys = [];

  try {
    if (Array.isArray(messageIds) && messageIds.length) {
      keys = messageIds.map((id) => {
        const raw = rawMessages.get(id);
        if (raw?.key) return raw.key;
        return { remoteJid: targetChat, id, fromMe: false };
      });
    } else {
      const recent = store.messages
        .filter((m) => ids.includes(m.chatId) && !m.fromMe)
        .slice(-Math.max(1, parseInt(req.body?.limit || '30', 10) || 30));
      keys = recent.map((m) => {
        const raw = rawMessages.get(m.id);
        if (raw?.key) return raw.key;
        return {
          remoteJid: m.chatId,
          id: m.id,
          fromMe: false,
          ...(m.chatId.endsWith('@g.us') ? { participant: m.senderId } : {}),
        };
      });
    }

    if (!keys.length) {
      return res.status(404).json({
        error: 'No known incoming messages for this chat in the bridge store',
        hint: 'The bridge can only ack messages it has seen. Send/receive something first, or pass messageIds.',
      });
    }

    await sock.readMessages(keys);
    for (const id of ids) upsertChat(id, { unreadCount: 0 });
    res.json({ success: true, chatId: targetChat, marked: keys.length });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Download media of a cached message to disk
app.get('/media/:messageId', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const messageId = req.params.messageId;
  const raw = rawMessages.get(messageId);
  if (!raw) {
    return res.status(404).json({
      error: `Message ${messageId} is not in the bridge raw cache`,
      hint: `Only the last ${RAW_CACHE_MAX} messages seen by this bridge process can be downloaded (WA_RAW_CACHE_MAX). Media received while the bridge was running is also auto-saved to the image/document/audio cache dirs.`,
    });
  }

  const content = getMessageContent(raw);
  const mediaType = detectMediaType(content);
  if (!mediaType) return res.status(400).json({ error: 'Message contains no downloadable media' });

  const node =
    content.imageMessage || content.videoMessage || content.pttMessage ||
    content.audioMessage || content.documentMessage ||
    content.documentWithCaptionMessage?.message?.documentMessage ||
    content.stickerMessage || {};
  const mime = node.mimetype || '';
  const extFromMime = mime.includes('jpeg') ? '.jpg'
    : mime.includes('png') ? '.png'
    : mime.includes('webp') ? '.webp'
    : mime.includes('gif') ? '.gif'
    : mime.includes('mp4') ? '.mp4'
    : mime.includes('ogg') ? '.ogg'
    : mime.includes('pdf') ? '.pdf'
    : '.bin';
  const baseName = node.fileName
    ? path.basename(node.fileName).replace(/[^a-zA-Z0-9._-]/g, '_')
    : `${mediaType}_${messageId.slice(0, 12).replace(/[^a-zA-Z0-9]/g, '')}${extFromMime}`;

  try {
    const outDir = req.query.dir ? String(req.query.dir) : MEDIA_DOWNLOAD_DIR;
    mkdirSync(outDir, { recursive: true });
    const outPath = path.join(outDir, baseName);
    const buf = await downloadMediaMessage(raw, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
    writeFileSync(outPath, buf);
    res.json({ success: true, messageId, mediaType, mimetype: mime, path: outPath, size: buf.length });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Profile info: picture, status, business profile, group metadata
app.get('/profile/:jid', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const jid = req.params.jid;
  const isGroup = jid.endsWith('@g.us');
  const out = { jid, isGroup, name: contactDisplayName(jid) || null };

  try {
    out.pictureUrl = await sock.profilePictureUrl(jid, 'image');
  } catch (err) {
    out.pictureUrl = null;
    out.pictureError = err.message;
  }

  if (isGroup) {
    try {
      const meta = await sock.groupMetadata(jid);
      out.subject = meta.subject;
      out.desc = meta.desc || '';
      out.owner = meta.owner || null;
      out.size = meta.participants?.length ?? null;
      out.participants = (meta.participants || []).map((p) => ({ id: p.id, admin: p.admin || null }));
    } catch (err) {
      out.groupError = err.message;
    }
  } else {
    try {
      if (typeof sock.fetchStatus === 'function') {
        const status = await sock.fetchStatus(jid);
        // Baileys returns either { status, setAt } or an array of those
        out.status = Array.isArray(status) ? (status[0]?.status?.status ?? status[0]?.status ?? null) : (status?.status ?? null);
      } else {
        out.status = null;
        out.statusError = 'fetchStatus() not available in this Baileys build';
      }
    } catch (err) {
      out.status = null;
      out.statusError = err.message;
    }
    try {
      if (typeof sock.getBusinessProfile === 'function') {
        out.businessProfile = (await sock.getBusinessProfile(jid)) || null;
      }
    } catch (err) {
      out.businessProfile = null;
      out.businessProfileError = err.message;
    }
    try {
      if (typeof sock.onWhatsApp === 'function') {
        const check = await sock.onWhatsApp(jid);
        out.onWhatsApp = Array.isArray(check) ? (check[0] || null) : (check || null);
      }
    } catch (err) {
      out.onWhatsAppError = err.message;
    }
  }

  res.json(out);
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: connectionState,
    queueLength: messageQueue.length,
    uptime: process.uptime(),
    // --- CLI extensions (additive; old fields above are unchanged) ---
    mode: WHATSAPP_MODE,
    pid: process.pid,
    port: PORT,
    sessionDir: SESSION_DIR,
    hasQR: !!currentQR,
    user: sock?.user ? { id: sock.user.id, lid: sock.user.lid || null, name: sock.user.name || null } : null,
    store: storeCoverage(),
  });
});

// Start
if (PAIR_ONLY) {
  // Pair-only mode: just connect, show QR, save creds, exit. No HTTP server.
  console.log('📱 WhatsApp pairing mode');
  console.log(`📁 Session: ${SESSION_DIR}`);
  console.log();
  startSocket();
} else {
  app.listen(PORT, '127.0.0.1', () => {
    console.log(`🌉 WhatsApp bridge listening on port ${PORT} (mode: ${WHATSAPP_MODE})`);
    console.log(`📁 Session stored in: ${SESSION_DIR}`);
    console.log(STORE_ENABLED
      ? `💾 Local store: ${STORE_DIR} (max ${STORE_MAX_MESSAGES} messages)`
      : `💾 Local store: disabled (WA_STORE=off) — /chats, /search, /contacts return 501`);
    if (ALLOWED_USERS.size > 0) {
      console.log(`🔒 Allowed users: ${Array.from(ALLOWED_USERS).join(', ')}`);
    } else if (WHATSAPP_MODE === 'self-chat') {
      console.log(`🔒 Self-chat mode — only your own messages to yourself are processed.`);
    } else {
      console.log(`🔒 No WHATSAPP_ALLOWED_USERS set — incoming messages are rejected.`);
      console.log(`   Set WHATSAPP_ALLOWED_USERS=<phone> to authorize specific users,`);
      console.log(`   or WHATSAPP_ALLOWED_USERS=* for an explicit open bot.`);
    }
    console.log();
    startSocket();
  });
}
