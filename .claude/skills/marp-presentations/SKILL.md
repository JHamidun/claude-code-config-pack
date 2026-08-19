---
name: marp-presentations
description: "Marp: Markdown → слайды (HTML/PDF/PPTX) через npx marp-cli, бесплатная альтернатива Gamma. Триггеры: «слайды из markdown», «marp»."
---

# Marp — Markdown Presentations

> Use when: "презентация", "слайды из markdown", "marp", "slides from markdown"
> Free alternative to Gamma. Markdown → PDF/PPTX/HTML slides.

## Overview

Marp converts Markdown files into professional presentations.
Output formats: HTML, PDF, PPTX, PNG, JPEG.

## Installation

```bash
# CLI (one-shot via npx, no install needed)
npx @marp-team/marp-cli slide.md --pdf

# Or install globally
npm install -g @marp-team/marp-cli

# VSCode extension (recommended for preview)
# Install: "Marp for VS Code" (marp-team.marp-vscode)
```

## Slide Syntax

```markdown
---
marp: true
theme: default
paginate: true
header: "Company Name"
footer: "2026"
style: |
  section {
    font-family: 'Arial', sans-serif;
  }
  h1 {
    color: #2563eb;
  }
---

# Slide 1 Title

Content for first slide

---

# Slide 2 Title

- Bullet point 1
- Bullet point 2
- Bullet point 3

![bg right:40%](image.png)

---

<!-- _class: lead -->

# Big centered text

Subtitle underneath

---

# Code Example

```python
def hello():
    print("Hello from Marp!")
```

---

# Two Columns

<div style="display: flex; gap: 2rem;">
<div>

**Left column**
- Point A
- Point B

</div>
<div>

**Right column**
- Point C
- Point D

</div>
</div>
```

## Built-in Themes

| Theme | Style |
|-------|-------|
| `default` | Clean, professional |
| `gaia` | Bold, colorful |
| `uncover` | Minimalist |

## Key Directives

```markdown
<!-- _class: lead -->        <!-- Centered large text -->
<!-- _class: invert -->      <!-- Dark background -->
<!-- _backgroundColor: #1a1a2e -->  <!-- Custom bg -->
<!-- _color: white -->       <!-- Text color -->
<!-- _paginate: false -->    <!-- Hide page number -->
<!-- _header: "" -->         <!-- Remove header for this slide -->
```

## Background Images

```markdown
![bg](image.jpg)             <!-- Full background -->
![bg right:40%](photo.jpg)   <!-- Split layout -->
![bg left:50%](chart.png)    <!-- Left split -->
![bg contain](diagram.svg)   <!-- Fit to slide -->
![bg blur:5px](photo.jpg)    <!-- Blurred background -->
![bg opacity:0.3](bg.jpg)    <!-- Semi-transparent -->
```

## CLI Commands

```bash
# Markdown → PDF
npx @marp-team/marp-cli slides.md --pdf

# Markdown → PPTX
npx @marp-team/marp-cli slides.md --pptx

# Markdown → HTML (single file)
npx @marp-team/marp-cli slides.md --html

# Markdown → PNG images (one per slide)
npx @marp-team/marp-cli slides.md --images png

# Watch mode (auto-rebuild on save)
npx @marp-team/marp-cli slides.md --pdf --watch

# Custom theme
npx @marp-team/marp-cli slides.md --pdf --theme ./custom-theme.css

# Server mode (preview in browser)
npx @marp-team/marp-cli slides.md --server --watch
```

## Workflow: Research → Presentation

```bash
# 1. Claude generates markdown with slide content
# 2. Save as slides.md with Marp frontmatter
# 3. Convert to desired format

# For PDF (best for sharing):
npx @marp-team/marp-cli slides.md --pdf --allow-local-files

# For PPTX (if client needs editable):
npx @marp-team/marp-cli slides.md --pptx

# For HTML (for web hosting):
npx @marp-team/marp-cli slides.md --html
```

## Custom Theme Example

```css
/* custom-theme.css */
@import 'default';

section {
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  color: #e0e0e0;
  font-family: 'Inter', sans-serif;
}

h1 {
  color: #7c3aed;
  border-bottom: 2px solid #7c3aed;
  padding-bottom: 0.3em;
}

h2 {
  color: #a78bfa;
}

code {
  background: rgba(124, 58, 237, 0.2);
  color: #c4b5fd;
}
```

## Dependencies

- Node.js v18+ (for npx)
- Chrome/Chromium (for PDF export, auto-detected)

## Notes

- Marp is 100% free and open-source
- VSCode extension gives live preview while editing
- `---` separates slides (standard Markdown horizontal rule)
- Supports math via KaTeX: `$E = mc^2$`
- Supports emoji: `:rocket:` → 🚀
