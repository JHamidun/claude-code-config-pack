# Visual design reference — create-an-asset

Read this when building the asset's styles, or when the user asks to restyle one.

## Color system

Dark base, prospect's brand as the accent. Drop the researched hexes into the two
brand variables; everything else derives from them.

```css
:root {
    /* === Prospect brand (from research) === */
    --brand-primary: #[extracted];
    --brand-secondary: #[extracted];
    --brand-primary-rgb: [r, g, b];   /* needed for rgba() glows */

    /* === Dark base === */
    --bg-primary:  #0a0d14;
    --bg-elevated: #0f131c;
    --bg-surface:  #161b28;
    --bg-hover:    #1e2536;

    /* === Text === */
    --text-primary:   #ffffff;
    --text-secondary: rgba(255, 255, 255, 0.7);
    --text-muted:     rgba(255, 255, 255, 0.5);

    /* === Accent === */
    --accent:       var(--brand-primary);
    --accent-hover: var(--brand-secondary);
    --accent-glow:  rgba(var(--brand-primary-rgb), 0.3);

    /* === Status === */
    --success: #12b886;
    --warning: #f59e0b;
    --error:   #ef4444;
}
```

## Typography

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

h1    { font-size: 2.5rem;  font-weight: 700; }
h2    { font-size: 1.75rem; font-weight: 600; }
h3    { font-size: 1.25rem; font-weight: 600; }
body  { font-size: 1rem;    font-weight: 400; line-height: 1.6; }
small { font-size: 0.875rem; font-weight: 500; }
```

## Elements

**Cards** — `var(--bg-surface)` background, 1px `rgba(255,255,255,0.1)` border,
12px radius, subtle layered shadow; on hover a slight elevation and border glow.

**Buttons** — primary: `var(--accent)` fill with white text; secondary: transparent
with an accent border. Hover raises brightness and scale slightly.

**Animations** — 200-300ms ease. Tab switches fade + slide; loading states pulse or
show a skeleton. Anything faster reads as a glitch, anything slower reads as lag.

## Workflow demo styles

```css
.node {
    background: var(--bg-surface);
    border: 2px solid var(--brand-primary);
    border-radius: 12px;
    padding: 16px;
    min-width: 140px;
}

.node.active {
    box-shadow: 0 0 20px var(--accent-glow);
    border-color: var(--accent);
}

.node.human {
    border-color: #f59e0b;   /* warm border marks the human in the loop */
}

.node.ai {
    background: linear-gradient(135deg, var(--bg-surface), var(--bg-elevated));
    border-color: var(--accent);
}

.arrow {
    stroke: var(--text-muted);
    stroke-width: 2;
    fill: none;
    marker-end: url(#arrowhead);
}

.arrow.active {
    stroke: var(--accent);
    stroke-dasharray: 8 4;
    animation: flowDash 1s linear infinite;
}

.canvas {
    background:
        radial-gradient(circle at center, var(--bg-elevated) 0%, var(--bg-primary) 100%),
        url("data:image/svg+xml,...");   /* subtle grid */
    overflow: auto;
}
```

## Component icons

| Type | Icon | Examples |
|------|------|----------|
| human | person SVG or 👤 | User, Analyst, Admin |
| document | file SVG or 📄 | PDF, Contract, Report |
| ai | brain SVG or 🤖 | AI agent, model |
| database | cylinder SVG or 🗄️ | Snowflake, Postgres |
| api | plug SVG or 🔌 | REST, GraphQL |
| middleware | hub SVG or ⚡ | Integration platform, MCP server |
| output | screen SVG or 📊 | Dashboard, report |

## Brand color fallbacks

Use only when the prospect's real brand colors could not be extracted.

| Industry | Primary | Secondary |
|----------|---------|-----------|
| Technology | #2563eb | #7c3aed |
| Finance | #0f172a | #3b82f6 |
| Healthcare | #0891b2 | #06b6d4 |
| Manufacturing | #ea580c | #f97316 |
| Retail | #db2777 | #ec4899 |
| Energy | #16a34a | #22c55e |
| Default | #3b82f6 | #8b5cf6 |
