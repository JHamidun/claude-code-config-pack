---
name: mcp-usage
description: "MCP Servers Usage Skill"
---

# MCP Servers Usage Skill

Quick reference for using all 24 MCP servers effectively.

## When to Use This Skill
- User asks what tools/capabilities are available
- Need to choose the right MCP server for a task
- Want to combine multiple servers for complex workflows

## Full Documentation
See: `${WORKSPACE}/.claude/MCP_SERVERS_GUIDE.md`

---

## Quick Command Reference

### Image Generation
```
"Сгенерируй изображение..." → DALL-E 3 (основной)
"Альтернативный стиль..." → Gemini 3 Pro Image (НЕ Replicate FLUX)
"Увеличь разрешение..." → Replicate (Real-ESRGAN)
```

### Audio/Voice
```
"Озвучь текст..." → ElevenLabs (НЕ Replicate Riffusion)
"Транскрибируй аудио..." → Deepgram (НЕ Replicate Whisper)
```

### Web Scraping
```
"Спарси Instagram..." → Apify (instagram-scraper)
"Парсинг Amazon..." → Apify (amazon-product-scraper)
"Google Maps контакты..." → Apify (google-maps-scraper)
"Скрапинг любого сайта..." → Apify (web-scraper)
```

### Design
```
"Покажи Figma файл..." → Figma
"Экспортируй из Figma..." → Figma
```

### Search & Data
```
"Найди в интернете..." → Brave Search
"Документация API X..." → Context7
"Загрузи страницу..." → Fetch
```

### Development
```
"Создай issue..." → GitHub / Linear
"Покажи ошибки..." → Sentry
"Запусти workflow..." → N8N
```

### Communication
```
"Отправь в Slack..." → Slack
"Создай страницу Notion..." → Notion
```

### Databases
```
"SQL запрос к локальной БД..." → SQLite
"Запрос к серверной БД..." → PostgreSQL
"Кэш/очередь..." → Redis
```

### Browser
```
"Скриншот страницы..." → Puppeteer
"Протестируй UI..." → Playwright
```

### Memory
```
"Запомни что..." → Memory
"Что ты знаешь о..." → Memory
```

---

## Server Categories

### AI & Media (4)
| Server | Best For |
|--------|----------|
| dalle | Quick image generation |
| replicate | Advanced models (FLUX, Whisper, etc) |
| elevenlabs | Voice/TTS |
| figma | Design files |

### Integrations (5)
| Server | Best For |
|--------|----------|
| n8n | Workflow automation |
| github | Code repos, issues |
| slack | Team messaging |
| notion | Documentation |
| linear | Task management |

### Data & Scraping (7)
| Server | Best For |
|--------|----------|
| brave-search | Web search |
| context7 | API documentation |
| fetch | Simple web fetching |
| apify | Advanced web scraping (social, e-commerce) |
| sqlite | Local database |
| postgres | Server database |
| redis | Caching |

### DevOps (3)
| Server | Best For |
|--------|----------|
| sentry | Error monitoring |
| puppeteer | Browser automation |
| playwright | E2E testing |

---

## Multi-Server Workflows

### Content Creation Pipeline
1. **Research**: Brave Search → gather info
2. **Write**: Claude → create content
3. **Design**: DALL-E → generate images
4. **Voice**: ElevenLabs → create audio
5. **Publish**: N8N → automate distribution

### Development Workflow
1. **Plan**: Linear → create tasks
2. **Code**: GitHub → manage repo
3. **Test**: Playwright → E2E tests
4. **Monitor**: Sentry → track errors
5. **Document**: Notion → write docs

### SEO/Marketing (if Ahrefs enabled)
1. **Research**: Ahrefs → keyword analysis
2. **Content**: Claude → write articles
3. **Images**: DALL-E → create visuals
4. **Publish**: N8N → automate posting
5. **Track**: Sentry → monitor performance

---

## Cost Awareness

### Pay-per-use
- **DALL-E**: $0.04-0.12/image
- **ElevenLabs**: ~$0.30/1000 chars
- **Replicate**: ~$0.0001-0.01/sec
- **Apify**: $5/мес бесплатно, далее pay-per-use

### Free/Included
- Memory, Filesystem, Sequential Thinking
- GitHub, Slack, Notion, Linear (API limits)
- Brave Search, Context7, Fetch
- SQLite, PostgreSQL, Redis
- Puppeteer, Playwright
- Sentry, Time

### Subscription Required
- Ahrefs: $99+/month (currently disabled)

---

## Tips

1. **Start simple**: Use one server, then combine
2. **Check costs**: AI generation costs money
3. **Cache results**: Use Redis for repeated queries
4. **Automate**: Use N8N for repetitive tasks
5. **Document**: Save findings to Notion/Memory
