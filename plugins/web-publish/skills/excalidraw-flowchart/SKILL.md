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

## Process

1. User describes what they need diagrammed
2. Identify diagram type (flowchart/arch/sequence/ER/mind map)
3. Generate Excalidraw JSON with proper layout
4. Save to `.excalidraw` file
5. User opens in Excalidraw (VS Code extension or excalidraw.com)

## Layout Rules

- Horizontal spacing: 250px between nodes
- Vertical spacing: 150px between rows
- Node width: 180-220px
- Node height: 50-70px
- Use grid alignment (snap to 20px grid)
- Arrows: prefer orthogonal routing

## Output

Save the JSON as `diagram.excalidraw` in the current directory. User can open it directly in VS Code with the Excalidraw extension.
