---
name: excalidraw-flowchart
description: Generate Excalidraw JSON for architecture diagrams, flowcharts, sequence diagrams. Use when user asks for "диаграмма", "flowchart", "excalidraw", "архитектурная схема".
---

# Excalidraw Flowchart Generator

Generate Excalidraw-compatible JSON for various diagram types.

## Supported Diagram Types

1. **Flowchart** — process flows, decision trees
2. **Architecture diagram** — system components and connections
3. **Sequence diagram** — interaction between services/actors
4. **Entity relationship** — database schemas
5. **Mind map** — brainstorming, topic exploration

## Excalidraw JSON Structure

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "claude-code",
  "elements": [
    {
      "type": "rectangle",
      "x": 100, "y": 100,
      "width": 200, "height": 60,
      "strokeColor": "#1e1e1e",
      "backgroundColor": "#a5d8ff",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "roundness": { "type": 3 },
      "id": "node-1"
    },
    {
      "type": "text",
      "x": 130, "y": 120,
      "width": 140, "height": 25,
      "text": "Service A",
      "fontSize": 16,
      "fontFamily": 1,
      "textAlign": "center",
      "containerId": "node-1",
      "id": "text-1"
    },
    {
      "type": "arrow",
      "x": 300, "y": 130,
      "width": 100, "height": 0,
      "strokeColor": "#1e1e1e",
      "strokeWidth": 2,
      "startBinding": { "elementId": "node-1", "focus": 0, "gap": 1 },
      "endBinding": { "elementId": "node-2", "focus": 0, "gap": 1 },
      "id": "arrow-1"
    }
  ],
  "appState": {
    "viewBackgroundColor": "#ffffff",
    "gridSize": 20
  }
}
```

## Color Palette

| Purpose | Color |
|---------|-------|
| Primary nodes | `#a5d8ff` (light blue) |
| Secondary | `#b2f2bb` (light green) |
| Warning | `#ffec99` (light yellow) |
| Error/critical | `#ffc9c9` (light red) |
| Database | `#d0bfff` (light purple) |
| External | `#e9ecef` (light gray) |

## Process (с визуальным циклом)

1. Пользователь описывает, что диаграммировать
2. Определи тип (flowchart/arch/sequence/ER/mind map)
3. Сгенерируй Excalidraw JSON с layout (правила ниже) → сохрани `.excalidraw`
4. **Визуальный цикл (render → смотрю → правлю)** — см. секцию ниже: отрендерь в PNG, ПОСМОТРИ, поправь композицию. НЕ отдавай one-shot вслепую — сложные схемы почти всегда требуют 1-2 итерации.
5. Отдай `.excalidraw` (+ PNG). Открывается в VS Code Excalidraw-расширении или excalidraw.com.

## Визуальный цикл (render → смотрю → правлю) — без постоянного сервера

Итеративная доводка через **playwright** (уже в стеке; НЕ нужен постоянный :3000-сервер — открываем/закрываем per-render):

1. Сгенерь `.excalidraw` JSON.
2. Отрендерь в PNG: playwright открывает `https://excalidraw.com` (или локальный excalidraw) → импортирует JSON (drag-drop/localStorage/`?json=`) → `browser_take_screenshot`. Скрипт-обёртка: `skills/excalidraw-flowchart/scripts/render.py` (Playwright, headless, load→screenshot→close).
3. **ПОСМОТРИ PNG** (Read) — наложения, пересечения стрелок, кривой layout, обрезка.
4. Поправь JSON (координаты/spacing/routing) → перерендерь. Гейт: нет наложений, стрелки читаемы, всё в кадре.

Для агента этого достаточно; постоянный canvas-сервер (mcp_excalidraw) нужен только для ЖИВОГО интерактивного холста с человеком — это отдельный кейс, не ставим ради генерации.

## Layout-операции (align / distribute / group)
- **Выравнивание**: одна ось — общий x (столбец) или y (ряд); фиксируй числом, не «на глаз».
- **Распределение**: равные зазоры между 3+ элементами = `(max-min)/(n-1)`.
- **Группировка**: связанные узлы — общий `groupIds:[id]`; подпись-контейнер — `frame`.
- **Grid-snap** 20px, орто-роутинг стрелок (см. Layout Rules ниже).

## Из Mermaid
Есть Mermaid-текст → конверсия: (а) excalidraw.com имеет встроенный «Mermaid to Excalidraw» (через playwright-фронт), либо (б) Cloud MCP Mermaid_Chart для самой Mermaid-диаграммы, если excalidraw-стиль не критичен.

## Визуализация memory-графа (тай-ин с твоим графом)
Нарисовать связи из `memory_graph.py` (5137 узлов): `python ~/.claude/scripts/memory_graph.py neighbors "<узел>"` (или `path`/`hubs`) → распарси узлы/рёбра → сгенерь Excalidraw (узлы=прямоугольники, рёбра=стрелки с подписью типа связи) → визуальный цикл. Так граф «кто связан с X» становится картинкой.

## Layout Rules

- Horizontal spacing: 250px between nodes
- Vertical spacing: 150px between rows
- Node width: 180-220px
- Node height: 50-70px
- Use grid alignment (snap to 20px grid)
- Arrows: prefer orthogonal routing

## Output

Save the JSON as `diagram.excalidraw` in the current directory. User can open it directly in VS Code with the Excalidraw extension.
