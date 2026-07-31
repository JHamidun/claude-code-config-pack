#!/usr/bin/env python3
"""Vector Memory Manager - stores session context in Qdrant (local mode)."""

import atexit
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

from qdrant_client import QdrantClient, models

MEMORY_DIR = Path.home() / ".claude" / "vector-memory"
VECTOR_DB_PATH = MEMORY_DIR / "qdrant_db"
COMPACTS_DIR = MEMORY_DIR / "compacts"
COLLECTION_NAME = "session_memory"

_client = None

def _str_to_uuid(s):
    """Convert string ID to deterministic UUID for Qdrant."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, s))

def _cleanup():
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None

atexit.register(_cleanup)

def get_client():
    global _client
    if _client is None:
        VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
        _client = QdrantClient(path=str(VECTOR_DB_PATH))
        _ensure_collection(_client)
    return _client

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384

def _ensure_collection(client):
    """Create collection if it doesn't exist."""
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=EMBED_DIM, distance=models.Distance.COSINE),
        )
    client.set_model(EMBED_MODEL)

def _add_document(client, doc_id, content, metadata):
    """Add a single document with metadata."""
    point_id = _str_to_uuid(doc_id)
    payload = {**metadata, "doc_id": doc_id, "content": content}
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=point_id,
                vector=models.Document(text=content, model=EMBED_MODEL),
                payload=payload,
            )
        ],
    )

def save_compact(content, metadata=None):
    client = get_client()
    timestamp = datetime.now().isoformat()
    doc_id = f"compact_{timestamp.replace(':', '-').replace('.', '-')}"
    meta = {"type": "auto_compact", "timestamp": timestamp, "date": timestamp[:10]}
    if metadata:
        meta.update(metadata)
    _add_document(client, doc_id, content, meta)
    COMPACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(COMPACTS_DIR / f"{doc_id}.md", 'w', encoding='utf-8') as f:
        f.write(f"# Auto-Compact: {timestamp}\n\n{content}")
    print(f"[OK] Compact saved: {doc_id}")
    return doc_id

def save_learning(content, category="general"):
    client = get_client()
    timestamp = datetime.now().isoformat()
    doc_id = f"learning_{timestamp.replace(':', '-').replace('.', '-')}"
    meta = {"type": "learning", "category": category, "timestamp": timestamp, "date": timestamp[:10]}
    _add_document(client, doc_id, content, meta)
    print(f"[LEARN] Saved: {content[:50]}...")
    return doc_id

def save_decision(content, project=None):
    client = get_client()
    timestamp = datetime.now().isoformat()
    doc_id = f"decision_{timestamp.replace(':', '-').replace('.', '-')}"
    meta = {"type": "decision", "timestamp": timestamp, "date": timestamp[:10]}
    if project:
        meta["project"] = project
    _add_document(client, doc_id, content, meta)
    print(f"[DECISION] Saved: {content[:50]}...")
    return doc_id

def search_memory(query, n_results=5, filter_type=None):
    client = get_client()
    query_filter = None
    if filter_type:
        query_filter = models.Filter(
            must=[models.FieldCondition(key="type", match=models.MatchValue(value=filter_type))]
        )
    try:
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=models.Document(text=query, model=EMBED_MODEL),
            limit=n_results,
            query_filter=query_filter,
        ).points
    except Exception:
        return []
    formatted = []
    for hit in results:
        payload = hit.payload or {}
        formatted.append({
            "content": payload.get("content", payload.get("document", "")),
            "metadata": {k: v for k, v in payload.items() if k not in ("content", "document")},
            "distance": hit.score,
        })
    return formatted

def get_recent_context(n=5):
    client = get_client()
    try:
        results, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="type", match=models.MatchValue(value="auto_compact"))]
            ),
            limit=n,
            with_payload=True,
        )
    except Exception:
        return "No previous session context found."
    if not results:
        return "No previous session context found."
    context = "## Recent Session Context:\n\n"
    for point in results:
        payload = point.payload or {}
        content = payload.get("content", "")
        date = payload.get("date", "Unknown")
        context += f"### {date}\n{content[:500]}...\n\n"
    return context

def get_last_session_summary(n=3, chars_per_doc=600):
    """Get summary of recent sessions for context."""
    client = get_client()
    try:
        results, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="type", match=models.MatchValue(value="auto_compact"))]
            ),
            limit=n,
            with_payload=True,
        )
    except Exception:
        return "NEW_SESSION: No previous context. Fresh start."
    if not results:
        return "NEW_SESSION: No previous context. Fresh start."

    summary = "## CONTEXT FROM PREVIOUS SESSIONS:\n\n"
    for point in results:
        payload = point.payload or {}
        date = payload.get("date", "Unknown")
        content = payload.get("content", "")
        content = content[:chars_per_doc]
        if len(payload.get("content", "")) > chars_per_doc:
            content += "..."
        summary += f"### [{date}]\n{content}\n\n"
    return summary

def check_triggers(time_minutes=30, file_threshold=5, files_changed=0):
    """Check all triggers for checkpoint. Returns (should_save, reasons)."""
    reasons = []
    should_save = False

    client = get_client()
    try:
        results, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1,
            with_payload=True,
        )
    except Exception:
        return True, ["FIRST_SAVE: No previous saves"]

    if results and results[0].payload:
        last_ts = results[0].payload.get('timestamp', '')
        if last_ts:
            try:
                last_save = datetime.fromisoformat(last_ts)
                elapsed = (datetime.now() - last_save).total_seconds() / 60
                if elapsed >= time_minutes:
                    should_save = True
                    reasons.append(f"TIME: {int(elapsed)} min elapsed (threshold: {time_minutes})")
            except Exception:
                pass
    else:
        should_save = True
        reasons.append("FIRST_SAVE: No previous saves")

    if files_changed >= file_threshold:
        should_save = True
        reasons.append(f"FILES: {files_changed} changed (threshold: {file_threshold})")

    return should_save, reasons

def save_milestone(content, milestone_type="checkpoint"):
    """Save a milestone during session (for auto-triggers)."""
    client = get_client()
    timestamp = datetime.now().isoformat()
    doc_id = f"milestone_{timestamp.replace(':', '-').replace('.', '-')}"
    meta = {"type": "milestone", "milestone_type": milestone_type, "timestamp": timestamp, "date": timestamp[:10]}
    _add_document(client, doc_id, content, meta)
    print(f"[MILESTONE] {milestone_type}: saved")
    return doc_id

def get_relevant_context(query, n=3):
    results = search_memory(query, n_results=n)
    if not results:
        return "No relevant context found."
    context = "## Relevant Past Context:\n\n"
    for r in results:
        meta = r.get('metadata', {})
        context += f"**[{meta.get('type', 'unknown')}] {meta.get('date', '')}:**\n{r['content'][:300]}...\n\n"
    return context

def get_stats():
    client = get_client()
    try:
        count_result = client.count(collection_name=COLLECTION_NAME)
        total = count_result.count
    except Exception:
        total = 0
    type_counts = {}
    for doc_type in ['auto_compact', 'learning', 'decision', 'milestone']:
        try:
            results, _ = client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="type", match=models.MatchValue(value=doc_type))]
                ),
                limit=10000,
                with_payload=False,
            )
            type_counts[doc_type] = len(results)
        except Exception:
            type_counts[doc_type] = 0
    return {"total_documents": total, "by_type": type_counts, "db_path": str(VECTOR_DB_PATH)}

if __name__ == "__main__":
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    if len(sys.argv) < 2:
        print("Usage: vector_memory.py [init|check|save|learn|decide|search|context|stats|recent|milestone] [args]")
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "init":
        print(get_last_session_summary())
    elif cmd == "check":
        files = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        should_save, reasons = check_triggers(time_minutes=30, file_threshold=5, files_changed=files)
        if should_save:
            print(f"CHECKPOINT_NEEDED: {'; '.join(reasons)}")
        else:
            print("OK: No checkpoint needed yet")
    elif cmd == "save":
        save_compact(sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read())
    elif cmd == "learn":
        save_learning(sys.argv[2] if len(sys.argv) > 2 else "", sys.argv[3] if len(sys.argv) > 3 else "general")
    elif cmd == "decide":
        save_decision(sys.argv[2] if len(sys.argv) > 2 else "", sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "milestone":
        save_milestone(sys.argv[2] if len(sys.argv) > 2 else "", sys.argv[3] if len(sys.argv) > 3 else "checkpoint")
    elif cmd == "search":
        for r in search_memory(sys.argv[2] if len(sys.argv) > 2 else ""):
            print(f"\n--- {r['metadata'].get('type', '?')} ({r['metadata'].get('date', '')}) ---\n{r['content'][:200]}...")
    elif cmd == "context":
        print(get_relevant_context(sys.argv[2]) if len(sys.argv) > 2 else get_recent_context())
    elif cmd == "stats":
        s = get_stats()
        print(f"\nVector Memory Stats (Qdrant):\n   Total: {s['total_documents']}\n   Compacts: {s['by_type'].get('auto_compact', 0)}\n   Learnings: {s['by_type'].get('learning', 0)}\n   Decisions: {s['by_type'].get('decision', 0)}\n   Milestones: {s['by_type'].get('milestone', 0)}\n   Path: {s['db_path']}")
    elif cmd == "recent":
        print(get_recent_context(int(sys.argv[2]) if len(sys.argv) > 2 else 5))
    elif cmd == "recall-recent":
        # Alias for init — used by SessionStart hook
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        print(get_last_session_summary(n=n))
    elif cmd == "cache-refresh":
        # Update text cache file for fast SessionStart hook
        summary = get_last_session_summary(n=3)
        cache_path = MEMORY_DIR / "session_cache.txt"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(summary, encoding='utf-8')
        print(f"[CACHE] Updated: {cache_path}")
    elif cmd == "migrate-from-chroma":
        # Migration helper: reads old ChromaDB data and imports into Qdrant
        old_db = MEMORY_DIR / "vector_db"
        if not old_db.exists():
            print("No old ChromaDB database found.")
            sys.exit(0)
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            old_client = chromadb.PersistentClient(path=str(old_db), settings=ChromaSettings(anonymized_telemetry=False))
            old_collection = old_client.get_or_create_collection(name="session_memory")
            all_data = old_collection.get()
            if not all_data['ids']:
                print("Old database is empty.")
                sys.exit(0)
            print(f"Found {len(all_data['ids'])} documents in ChromaDB. Migrating...")
            client = get_client()
            migrated = 0
            for i, doc_id in enumerate(all_data['ids']):
                content = all_data['documents'][i]
                meta = all_data['metadatas'][i] if all_data['metadatas'] else {}
                try:
                    _add_document(client, doc_id, content, meta)
                    migrated += 1
                except Exception as e:
                    print(f"  [SKIP] {doc_id}: {e}")
            print(f"[OK] Migrated {migrated}/{len(all_data['ids'])} documents to Qdrant.")
        except ImportError:
            print("chromadb not installed. Cannot migrate. Install: pip install chromadb")
        except Exception as e:
            print(f"Migration error: {e}")
    else:
        print(f"Unknown: {cmd}")
