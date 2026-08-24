# HTML Component Library for Webinar Documents

## Document Header

```html
<div class="header">
    <h1>Title</h1>
    <div class="subtitle">Subtitle</div>
    <div class="meta">Date | Speaker</div>
</div>
```

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

## Section Headers (colored by topic)

```html
<h2 class="section-name topic-class">Section Title</h2>
```

```css
h2 {
    font-size: 1.4rem;
    color: #151766;
    margin: 35px 0 15px;
    padding: 10px 20px;
    border-radius: 8px;
    page-break-after: avoid;
}
/* Example topic classes — переименуй под свои темы */
h2.topic-a { background: rgba(139, 92, 246, 0.1); border-left: 5px solid #8b5cf6; }
h2.topic-b { background: rgba(16, 185, 129, 0.1); border-left: 5px solid #10b981; }
h2.topic-c { background: rgba(66, 133, 244, 0.1); border-left: 5px solid #4285F4; }
```

## Step Block

```html
<div class="step">
    <div class="step-num purple">1</div>
    <div class="step-content"><strong>Bold label:</strong> Description text</div>
</div>
```

```css
.step {
    display: flex;
    align-items: flex-start;
    gap: 15px;
    margin: 10px 0;
    padding: 12px 16px;
    background: #f8fafc;
    border-radius: 10px;
}
.step-num {
    flex-shrink: 0;
    width: 32px; height: 32px;
    border-radius: 50%;
    color: white;
    font-weight: 700;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    justify-content: center;
}
.step-num.purple { background: #8b5cf6; }
.step-num.green { background: #10b981; }
.step-num.blue { background: #4285F4; }
.step-num.tg { background: #0088cc; }
.step-num.orange { background: #f97316; }
.step-num.pink { background: #ea4c89; }
.step-num.navy { background: #151766; }
.step-num.teal { background: #14b8a6; }
```

## Prompt/Code Box

```html
<div class="prompt-box">
    <span class="label">LABEL TEXT</span>
    <span class="section-title"># SECTION</span>
    Prompt or code content here
</div>
```

```css
.prompt-box {
    background: #0f172a;
    color: #7dd3fc;
    padding: 20px 25px;
    border-radius: 12px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.82rem;
    line-height: 1.7;
    margin: 12px 0;
    white-space: pre-line;
    page-break-inside: avoid;
}
.prompt-box .label {
    color: #f97316;
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
    display: block;
}
.prompt-box .section-title { color: #10b981; font-weight: 700; }
```

## Info Boxes

```html
<div class="tip-box"><strong>Tip title:</strong> Content</div>
<div class="warning-box"><strong>Warning title:</strong> Content</div>
<div class="webinar-quote">
    <span class="speaker">Source:</span> "Quote text"
</div>
```

```css
.tip-box {
    background: linear-gradient(135deg, rgba(41, 169, 255, 0.08), rgba(45, 47, 232, 0.05));
    border-left: 4px solid #2D2FE8;
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin: 12px 0;
    font-size: 0.88rem;
}
.warning-box {
    background: rgba(249, 115, 22, 0.08);
    border-left: 4px solid #f97316;
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin: 12px 0;
    font-size: 0.88rem;
}
.webinar-quote {
    background: rgba(139, 92, 246, 0.06);
    border-left: 4px solid #8b5cf6;
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin: 12px 0;
    font-size: 0.88rem;
    font-style: italic;
}
.webinar-quote .speaker {
    font-style: normal;
    font-weight: 600;
    color: #8b5cf6;
    font-size: 0.8rem;
}
```

## Styled Table

```html
<table class="table">
    <thead><tr><th>Header 1</th><th>Header 2</th></tr></thead>
    <tbody>
        <tr><td>Data</td><td>Data</td></tr>
        <tr><td>Data</td><td>Data</td></tr>
    </tbody>
</table>
```

```css
.table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 0.85rem; }
.table th { background: #151766; color: white; padding: 10px 14px; text-align: left; }
.table td { padding: 8px 14px; border-bottom: 1px solid #e5e7eb; }
.table tr:nth-child(even) { background: #f8fafc; }
```

## Two-Column Cards

```html
<div class="grid-2">
    <div class="card">
        <h4>Card Title</h4>
        <ul><li>Item 1</li><li>Item 2</li></ul>
    </div>
    <div class="card">
        <h4>Card Title</h4>
        <ul><li>Item 1</li><li>Item 2</li></ul>
    </div>
</div>
```

```css
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 12px 0; }
.card {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 16px;
    font-size: 0.88rem;
}
.card h4 { font-size: 0.95rem; margin-bottom: 8px; }
```

## Section Divider

```html
<hr class="divider">
```

```css
.divider {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, #2D2FE8, transparent);
    margin: 30px 0;
}
```

## Footer

```html
<div class="footer">
    <p><strong>Contacts:</strong> <a href="...">Link</a></p>
    <p style="margin-top: 8px;">Promo: <strong>CODE</strong></p>
</div>
```

```css
.footer {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 2px solid #e5e7eb;
    font-size: 0.85rem;
    color: #64748b;
}
.footer a { color: #2D2FE8; text-decoration: none; }
```

## Print CSS

```css
@media print {
    body { padding: 30px 40px; }
    h2 { page-break-after: avoid; }
    .prompt-box { page-break-inside: avoid; }
    .step { page-break-inside: avoid; }
}
```

## Base Document Styles

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

## Transcript-Specific Components

### Timestamp Badge

```html
<div class="paragraph">
    <span class="timestamp">05:30</span>Text of the paragraph
</div>
```

```css
.timestamp {
    display: inline-block;
    font-family: monospace;
    font-size: 0.78rem;
    color: #9ca3af;
    background: #f3f4f6;
    padding: 1px 8px;
    border-radius: 4px;
    margin-right: 8px;
}
```

### Table of Contents

```html
<div class="toc">
    <h2>Contents</h2>
    <div class="toc-item">
        <span>Section Title</span>
        <span class="toc-time">05:30</span>
    </div>
</div>
```

```css
.toc {
    background: #f8fafc;
    border-radius: 12px;
    padding: 25px 30px;
    margin-bottom: 35px;
    border: 1px solid #e5e7eb;
}
.toc-item {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    font-size: 0.9rem;
    border-bottom: 1px dotted #d1d5db;
}
.toc-time { color: #6b7280; font-family: monospace; font-size: 0.85rem; }
```

### Stats Bar (in header)

```html
<div class="stats">
    <div class="stat"><strong>140</strong> paragraphs</div>
    <div class="stat"><strong>~2 hours</strong> duration</div>
</div>
```

```css
.header .stats {
    display: flex; gap: 30px; margin-top: 20px;
    padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.15);
}
.header .stat strong { color: #7dd3fc; }
```
