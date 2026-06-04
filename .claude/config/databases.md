# Databases

> Add your database connection details here.

## PostgreSQL
| Param | Value |
|-------|-------|
| Host | YOUR_SERVER_IP |
| Port | 5432 |
| Databases | your_database |
| Env vars | `DATABASE_URL`, `DATABASE_URL_EXTERNAL` |
| MCP server | `postgres` (mcp.json) |

## Redis
| Param | Value |
|-------|-------|
| Host | YOUR_SERVER_IP |
| Port | 6379 |
| Env vars | `REDIS_URL`, `REDIS_URL_EXTERNAL` |
| MCP server | `redis` (mcp.json) |

## SQLite
| File | Use |
|------|-----|
| chats.db | Claude Code chat search index (FTS5) |

## Connection Strings
All connection strings live in: `~/.claude/.credentials.master.env`
