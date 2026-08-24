# Styling Guide

## Dark Theme (Slide Presentations)

### Color Variables

```css
:root {
    --primary: #2D2FE8;      /* Main blue */
    --accent: #29A9FF;        /* Accent cyan */
    --bg-dark: #0a0b2e;       /* Background */
    --chatbot-color: #f97316; /* Orange */
    --assistant-color: #8b5cf6; /* Purple */
    --agent-color: #10b981;   /* Green */
}
```

### Background Gradient

```css
body {
    background: linear-gradient(135deg, #0a0b2e 0%, #151766 50%, #1a1a3e 100%);
    color: white;
    width: 1920px;
    height: 1080px;
    overflow: hidden;
    margin: 0;
    padding: 0;
    font-family: 'Segoe UI', -apple-system, sans-serif;
}
```

### Slide Layout

```css
.slide {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    display: none !important;
    padding: 50px 70px;
    overflow: hidden;
}
.slide.active {
    display: flex !important;
    flex-direction: column;
}
```

### Content Cards (on dark background)

```css
.card-dark {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 25px 30px;
    backdrop-filter: blur(10px);
}
```

### Slide Title

```css
.slide h2 {
    font-size: 2.2rem;
    font-weight: 700;
    margin-bottom: 30px;
    background: linear-gradient(135deg, #fff, #7dd3fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
```

### Bullet Points (on dark)

```css
.slide ul {
    list-style: none;
    padding: 0;
}
.slide li {
    padding: 8px 0;
    padding-left: 30px;
    position: relative;
    font-size: 1.3rem;
    line-height: 1.6;
}
.slide li::before {
    content: '';
    position: absolute;
    left: 0;
    top: 16px;
    width: 12px;
    height: 12px;
    border-radius: 3px;
    background: var(--accent);
}
```

### Color-Coded Labels

```css
.label-chatbot { color: #f97316; }  /* Orange */
.label-assistant { color: #8b5cf6; } /* Purple */
.label-agent { color: #10b981; }     /* Green */
```

---

## Light Theme (Documents: Summary, Instructions, Transcript)

### Base Styles

```css
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Segoe UI', -apple-system, sans-serif;
    color: #1a1a2e;
    line-height: 1.7;
    background: #fff;
    padding: 50px 60px;
}
h3 { font-size: 1.05rem; color: #374151; margin: 18px 0 10px; }
p { margin-bottom: 10px; font-size: 0.92rem; }
ul { margin: 8px 0 8px 20px; font-size: 0.88rem; }
li { margin-bottom: 4px; }
```

### Header (gradient, for all documents)

```css
.header {
    background: linear-gradient(135deg, #0a0b2e, #151766, #2D2FE8);
    color: white;
    padding: 40px 50px;
    border-radius: 16px;
    margin-bottom: 40px;
}
.header h1 { font-size: 1.8rem; margin-bottom: 8px; }
.header .subtitle { font-size: 1.1rem; opacity: 0.9; color: #7dd3fc; }
.header .meta { font-size: 0.9rem; opacity: 0.7; margin-top: 15px; }
```

### Section Headers (color-coded)

```css
h2 {
    font-size: 1.4rem;
    color: #151766;
    margin: 35px 0 15px;
    padding: 10px 20px;
    border-radius: 8px;
    page-break-after: avoid;
}
```

### Topic Colors

| Topic | Background | Border |
|-------|-----------|--------|
| Тема A (инструмент) | `rgba(139, 92, 246, 0.1)` | `#8b5cf6` |
| Тема B (инструмент) | `rgba(16, 185, 129, 0.1)` | `#10b981` |
| Gemini | `rgba(66, 133, 244, 0.1)` | `#4285F4` |
| Telegram | `rgba(0, 136, 204, 0.1)` | `#0088cc` |
| Agents | `rgba(249, 115, 22, 0.1)` | `#f97316` |
| n8n | `rgba(234, 76, 137, 0.1)` | `#ea4c89` |
| Prompts | `rgba(45, 47, 232, 0.1)` | `#2D2FE8` |
| Tips | `rgba(20, 184, 166, 0.1)` | `#14b8a6` |
| Intro | `rgba(45, 47, 232, 0.08)` | `#2D2FE8` |
| Closing | `rgba(107, 114, 128, 0.08)` | `#6b7280` |

### Text Sizing Guide

| Element | Font Size |
|---------|-----------|
| Document title (h1) | `1.8rem` |
| Section header (h2) | `1.3-1.4rem` |
| Subsection (h3) | `1.05rem` |
| Body text (p) | `0.92rem` |
| Lists (ul/li) | `0.88rem` |
| Card title (h4) | `0.95rem` |
| Card content | `0.88rem` |
| Prompt box | `0.82rem` |
| Footer | `0.85rem` |
| Timestamp badge | `0.78rem` |
| Labels (uppercase) | `0.75rem` |

---

## Print CSS

```css
@media print {
    body { padding: 30px 40px; }
    h2 { page-break-after: avoid; }
    .prompt-box { page-break-inside: avoid; }
    .step { page-break-inside: avoid; }
    .tip-box { page-break-inside: avoid; }
    .warning-box { page-break-inside: avoid; }
    .card { page-break-inside: avoid; }
    .header { page-break-after: avoid; }
}
```

---

## Viewport Constraints (Presentations)

- Target viewport: **1920 x 1080px**
- All slide content MUST fit within this area
- Use `overflow: hidden` on `.slide` to prevent overflow
- If content overflows, reduce in this order:
  1. Image sizes (photos, QR codes)
  2. Font sizes
  3. Paddings and margins
  4. Number of items per slide (split into two slides)

### Safe Content Areas

| Zone | Size |
|------|------|
| Full slide | 1920 x 1080 |
| With padding (50px 70px) | 1780 x 980 |
| Recommended content area | 1700 x 900 |
