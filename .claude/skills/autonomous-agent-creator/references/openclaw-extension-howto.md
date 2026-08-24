# OpenClaw Extension Development Guide

> Step-by-step guide based on linkedin-autopilot and e2e-testing extensions.

---

## 1. Directory Structure

```
my-extension/
  package.json         # NPM package metadata + deps
  tsconfig.json        # TypeScript config
  src/
    index.ts           # Entry point with definePluginEntry
    tools/
      my-tool.ts       # Individual tool factory
      rate-limiter.ts  # (Optional) Rate limiting module
  dist/                # Compiled JS (gitignored, built before deploy)
```

Extensions live inside the OpenClaw container at `/home/node/.openclaw/extensions/<extension>/`.

---

## 2. package.json

```json
{
  "name": "@openclaw/my-extension",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "clean": "rm -rf dist"
  },
  "dependencies": {
    "@sinclair/typebox": "^0.32.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "@types/node": "^20.0.0"
  }
}
```

Key points:
- `"type": "module"` is required (OpenClaw uses ESM)
- `@sinclair/typebox` is the standard for parameter schemas
- Keep deps minimal — each dep increases image size

---

## 3. tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "declaration": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

---

## 4. Entry Point: src/index.ts

```typescript
import { Type } from '@sinclair/typebox';
import { myToolFactory } from './tools/my-tool.js';
import { anotherToolFactory } from './tools/another-tool.js';

export const definePluginEntry = () => ({
  id: 'my-extension',
  name: 'My Extension',
  version: '1.0.0',

  register(api: PluginAPI) {
    // Register each tool with its factory
    api.registerTool(myToolFactory, { names: ['my_tool'] });
    api.registerTool(anotherToolFactory, { names: ['another_tool'] });
  }
});

// Type definition for the API (not exported by OpenClaw yet)
interface PluginAPI {
  registerTool(factory: ToolFactory, opts: { names: string[] }): void;
  getConfig(): Record<string, unknown>;
}

type ToolFactory = (config: any) => {
  name: string;
  description: string;
  parameters: any;
  execute: (params: any) => Promise<any>;
};

export default definePluginEntry;
```

---

## 5. Tool Factory Pattern

```typescript
// src/tools/my-tool.ts
import { Type, Static } from '@sinclair/typebox';

const MyToolParams = Type.Object({
  url: Type.String({ description: 'Target URL to process' }),
  mode: Type.Optional(Type.Union([
    Type.Literal('fast'),
    Type.Literal('thorough'),
    Type.Literal('stealth')
  ], { description: 'Processing mode (default: fast)' })),
  maxResults: Type.Optional(Type.Number({
    description: 'Maximum results to return',
    minimum: 1,
    maximum: 100,
    default: 10
  }))
});

type MyToolInput = Static<typeof MyToolParams>;

export function myToolFactory(config: any) {
  return {
    name: 'my_tool',
    description: `Processes the given URL and extracts data.
Call this tool when the user wants to analyze a webpage.
Returns structured data that you should present as a summary.
If mode is 'stealth', add delays between requests.`,
    parameters: MyToolParams,

    async execute(params: MyToolInput) {
      const { url, mode = 'fast', maxResults = 10 } = params;

      try {
        const result = await processUrl(url, mode, maxResults);
        return { ok: true, data: result };
      } catch (err: any) {
        return { ok: false, error: err.message };
      }
    }
  };
}
```

---

## 6. TypeBox Schema Examples

```typescript
import { Type } from '@sinclair/typebox';

// Basic types
Type.String({ description: 'A text value' })
Type.Number({ description: 'A numeric value' })
Type.Integer({ description: 'An integer value' })
Type.Boolean({ description: 'True or false' })

// Optional fields
Type.Optional(Type.String({ description: 'Optional text' }))

// Enums via Union of Literals
Type.Union([
  Type.Literal('draft'),
  Type.Literal('published'),
  Type.Literal('archived')
], { description: 'Content status' })

// Arrays
Type.Array(Type.String(), { description: 'List of tags' })

// Nested objects
Type.Object({
  name: Type.String(),
  age: Type.Optional(Type.Number()),
  address: Type.Object({
    city: Type.String(),
    country: Type.String()
  })
})

// With constraints
Type.String({ minLength: 1, maxLength: 500 })
Type.Number({ minimum: 0, maximum: 100 })
Type.Array(Type.String(), { minItems: 1, maxItems: 10 })
```

---

## 7. "Instruction Emitter" Pattern

Tools DON'T execute browser actions directly. They return step-by-step instructions
for the agent to execute via the built-in `browser` tool.

```typescript
// src/tools/linkedin-post.ts

export function linkedinPostFactory(config: any) {
  return {
    name: 'linkedin_create_post',
    description: `Generates step-by-step browser instructions for publishing a LinkedIn post.
IMPORTANT: This tool does NOT execute actions. It returns instructions that YOU must execute
using the browser tool, one step at a time. Wait for each step to complete before proceeding.`,
    parameters: Type.Object({
      content: Type.String({ description: 'Post text content' }),
      hasImage: Type.Optional(Type.Boolean({ description: 'Whether to attach an image' }))
    }),

    async execute(params: { content: string; hasImage?: boolean }) {
      const steps = [
        {
          step: 1,
          action: 'navigate',
          instruction: 'Navigate to https://www.linkedin.com/feed/',
          waitFor: 'button[aria-label="Start a post"]'
        },
        {
          step: 2,
          action: 'click',
          instruction: 'Click the "Start a post" button',
          selector: 'button[aria-label="Start a post"]',
          waitFor: '.ql-editor'
        },
        {
          step: 3,
          action: 'type',
          instruction: `Type the post content into the editor`,
          selector: '.ql-editor',
          text: params.content,
          waitFor: 'button[aria-label="Post"]'
        },
        {
          step: 4,
          action: 'click',
          instruction: 'Click the "Post" button to publish',
          selector: 'button[aria-label="Post"]',
          waitFor: '.feed-shared-update-v2'
        }
      ];

      return {
        ok: true,
        instructions: steps,
        _agent_hint: 'Execute each step sequentially using the browser tool. Report success/failure after each.'
      };
    }
  };
}
```

Why this pattern:
- Tools can't access the browser directly (different execution context)
- Agent has browser tool with error recovery capabilities
- Separates planning (extension) from execution (agent + browser)
- Allows agent to handle failures gracefully (retry, skip, report)

---

## 8. Rate Limiter Module

```typescript
// src/tools/rate-limiter.ts

interface ActionLog {
  timestamp: number;
  action: string;
}

const actionLog: ActionLog[] = [];

const LIMITS = {
  hourly: { window: 3600_000, max: 20 },
  daily: { window: 86400_000, max: 100 }
};

export function checkRateLimit(action: string): { allowed: boolean; reason?: string } {
  const now = Date.now();

  // Clean old entries
  const cutoff = now - LIMITS.daily.window;
  while (actionLog.length > 0 && actionLog[0].timestamp < cutoff) {
    actionLog.shift();
  }

  // Check hourly
  const hourAgo = now - LIMITS.hourly.window;
  const hourlyCount = actionLog.filter(a => a.timestamp > hourAgo && a.action === action).length;
  if (hourlyCount >= LIMITS.hourly.max) {
    return { allowed: false, reason: `Hourly limit reached (${LIMITS.hourly.max}/h)` };
  }

  // Check daily
  const dailyCount = actionLog.filter(a => a.action === action).length;
  if (dailyCount >= LIMITS.daily.max) {
    return { allowed: false, reason: `Daily limit reached (${LIMITS.daily.max}/d)` };
  }

  return { allowed: true };
}

export function logAction(action: string): void {
  actionLog.push({ timestamp: Date.now(), action });
}
```

Usage in tool:
```typescript
import { checkRateLimit, logAction } from './rate-limiter.js';

async execute(params) {
  const check = checkRateLimit('linkedin_post');
  if (!check.allowed) {
    return { ok: false, error: check.reason, retry: false };
  }

  // ... do work ...
  logAction('linkedin_post');
  return { ok: true, data: result };
}
```

---

## 9. Building and Deploying

### Build locally:

```bash
cd my-extension
pnpm install
pnpm build
```

### Copy to server:

```bash
scp -r dist/ "$SERVER":/opt/openclaw-<bot>/extensions/my-extension/dist/
scp package.json "$SERVER":/opt/openclaw-<bot>/extensions/my-extension/
```

### Or bake into image (rebuild needed):

```dockerfile
COPY extensions/my-extension /home/node/.openclaw/extensions/my-extension
RUN cd /home/node/.openclaw/extensions/my-extension && npm install --production
```

### Container restart required after extension changes:

```bash
ssh "$SERVER" 'docker restart openclaw-<bot>'
```

---

## 10. Configuration via openclaw.json

Extensions can read config from the main openclaw.json:

```json
{
  "extensions": {
    "my-extension": {
      "enabled": true,
      "apiKey": "${MY_EXTENSION_API_KEY}",
      "maxConcurrent": 3
    }
  }
}
```

Access in the factory:
```typescript
export function myToolFactory(config: any) {
  const extConfig = config?.extensions?.['my-extension'] || {};
  const apiKey = extConfig.apiKey;
  // ...
}
```

---

## 11. Debugging

### Check if extension loaded:

```bash
ssh "$SERVER" 'docker logs openclaw-<bot> 2>&1 | grep -i "extension\|plugin"'
```

### Common issues:

| Symptom | Cause | Fix |
|---------|-------|-----|
| Tool not appearing | Name mismatch between `names` array and tool `name` field | Ensure they match exactly |
| "Cannot find module" | Missing `dist/` or bad import path | Run `pnpm build`, check `.js` extensions in imports |
| Extension silently ignored | `"type": "module"` missing in package.json | Add it |
| Runtime error on tool call | Parameter validation failed | Check TypeBox schema matches actual params |
