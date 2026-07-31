---
name: word-docx
description: "Word / DOCX Skill"
---

# Word / DOCX Skill

## Overview

Expert skill for creating and manipulating Word documents using Python with python-docx.

## When to Use

- Creating professional reports
- Generating contracts and templates
- Document automation
- Adding tables, images, headers/footers
- Formatting text with styles

## Dependencies

```bash
pip install python-docx Pillow
```

## Core Operations

### 1. Create New Document

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT

def create_professional_document(title: str, output_path: str):
    """Create a professionally formatted Word document."""
    doc = Document()

    # Title
    title_para = doc.add_heading(title, level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Subtitle/date
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Generated: " + datetime.now().strftime("%Y-%m-%d"))
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(128, 128, 128)

    doc.save(output_path)
    return output_path
```

### 2. Add Formatted Text

```python
def add_formatted_paragraph(doc, text: str, bold=False, italic=False,
                            size=12, color=None, alignment='left'):
    """Add a formatted paragraph."""
    para = doc.add_paragraph()

    # Set alignment
    alignments = {
        'left': WD_ALIGN_PARAGRAPH.LEFT,
        'center': WD_ALIGN_PARAGRAPH.CENTER,
        'right': WD_ALIGN_PARAGRAPH.RIGHT,
        'justify': WD_ALIGN_PARAGRAPH.JUSTIFY
    }
    para.alignment = alignments.get(alignment, WD_ALIGN_PARAGRAPH.LEFT)

    # Add run with formatting
    run = para.add_run(text)
    run.font.bold = bold
    run.font.italic = italic
    run.font.size = Pt(size)

    if color:
        run.font.color.rgb = RGBColor(*color)

    return para

def add_bullet_list(doc, items: list, level=0):
    """Add a bullet list."""
    for item in items:
        para = doc.add_paragraph(item, style='List Bullet')
        para.paragraph_format.left_indent = Inches(0.5 * level)

def add_numbered_list(doc, items: list):
    """Add a numbered list."""
    for item in items:
        doc.add_paragraph(item, style='List Number')
```

### 3. Add Tables

```python
def add_styled_table(doc, headers: list, data: list, style='Table Grid'):
    """Add a styled table."""
    # Create table
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = style
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Add headers
    header_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        header_cells[i].text = header
        # Style header
        run = header_cells[i].paragraphs[0].runs[0]
        run.font.bold = True
        run.font.size = Pt(11)
        header_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Add data rows
    for row_data in data:
        row_cells = table.add_row().cells
        for i, value in enumerate(row_data):
            row_cells[i].text = str(value)
            row_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Set column widths
    for column in table.columns:
        for cell in column.cells:
            cell.width = Inches(1.5)

    return table

def add_data_table_from_dict(doc, data: dict):
    """Create table from dictionary."""
    headers = list(data.keys())
    max_rows = max(len(v) for v in data.values())

    rows = []
    for i in range(max_rows):
        row = [data[h][i] if i < len(data[h]) else "" for h in headers]
        rows.append(row)

    return add_styled_table(doc, headers, rows)
```

### 4. Add Images

```python
def add_image(doc, image_path: str, width_inches: float = 5):
    """Add an image to the document."""
    doc.add_picture(image_path, width=Inches(width_inches))

    # Center the image
    last_paragraph = doc.paragraphs[-1]
    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

def add_image_with_caption(doc, image_path: str, caption: str, width: float = 5):
    """Add image with caption."""
    doc.add_picture(image_path, width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    caption_para = doc.add_paragraph()
    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = caption_para.add_run(caption)
    run.font.italic = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(128, 128, 128)
```

### 5. Headers and Footers

```python
def add_header_footer(doc, header_text: str, footer_text: str,
                      add_page_numbers: bool = True):
    """Add header and footer to document."""
    section = doc.sections[0]

    # Header
    header = section.header
    header_para = header.paragraphs[0]
    header_para.text = header_text
    header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Footer
    footer = section.footer
    footer_para = footer.paragraphs[0]
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if add_page_numbers:
        # Add page number field
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement

        run = footer_para.add_run(footer_text + " | Page ")

        # Page number field
        fld_char1 = OxmlElement('w:fldChar')
        fld_char1.set(qn('w:fldCharType'), 'begin')

        instr_text = OxmlElement('w:instrText')
        instr_text.text = "PAGE"

        fld_char2 = OxmlElement('w:fldChar')
        fld_char2.set(qn('w:fldCharType'), 'end')

        run._r.append(fld_char1)
        run._r.append(instr_text)
        run._r.append(fld_char2)
    else:
        footer_para.text = footer_text
```

### 6. Custom Styles

```python
def create_custom_style(doc, style_name: str, font_name: str = 'Calibri',
                        font_size: int = 12, bold: bool = False,
                        color: tuple = (0, 0, 0)):
    """Create a custom paragraph style."""
    styles = doc.styles

    style = styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
    style.font.name = font_name
    style.font.size = Pt(font_size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(*color)

    return style

def apply_corporate_template(doc):
    """Apply corporate styling to document."""
    # Modify Normal style
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    # Modify Heading 1
    h1_style = doc.styles['Heading 1']
    h1_style.font.name = 'Calibri'
    h1_style.font.size = Pt(18)
    h1_style.font.bold = True
    h1_style.font.color.rgb = RGBColor(0, 70, 127)

    # Modify Heading 2
    h2_style = doc.styles['Heading 2']
    h2_style.font.name = 'Calibri'
    h2_style.font.size = Pt(14)
    h2_style.font.bold = True
    h2_style.font.color.rgb = RGBColor(0, 112, 192)
```

### 7. Page Setup

```python
def setup_page(doc, orientation='portrait', margins=(1, 1, 1, 1)):
    """Configure page setup."""
    from docx.enum.section import WD_ORIENT

    section = doc.sections[0]

    # Orientation
    if orientation == 'landscape':
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width, section.page_height = section.page_height, section.page_width

    # Margins (top, right, bottom, left)
    section.top_margin = Inches(margins[0])
    section.right_margin = Inches(margins[1])
    section.bottom_margin = Inches(margins[2])
    section.left_margin = Inches(margins[3])
```

### 8. Complete Report Template

```python
def create_report(title: str, sections: list, output_path: str):
    """
    Create a complete report.

    sections = [
        {"heading": "Introduction", "content": "Text here...", "level": 1},
        {"heading": "Data", "table": {"headers": [...], "data": [...]}},
        {"heading": "Analysis", "content": "...", "bullets": ["point 1", "point 2"]},
        {"image": "path/to/image.png", "caption": "Figure 1"}
    ]
    """
    doc = Document()
    apply_corporate_template(doc)

    # Title
    doc.add_heading(title, level=0)
    doc.add_paragraph()

    for section in sections:
        if "heading" in section:
            level = section.get("level", 1)
            doc.add_heading(section["heading"], level=level)

        if "content" in section:
            doc.add_paragraph(section["content"])

        if "bullets" in section:
            add_bullet_list(doc, section["bullets"])

        if "table" in section:
            add_styled_table(doc,
                           section["table"]["headers"],
                           section["table"]["data"])
            doc.add_paragraph()

        if "image" in section:
            add_image_with_caption(doc, section["image"],
                                  section.get("caption", ""))

    doc.save(output_path)
    return output_path
```

## Quick Reference

| Task | Code |
|------|------|
| Create document | `doc = Document()` |
| Add heading | `doc.add_heading("Title", level=1)` |
| Add paragraph | `doc.add_paragraph("Text")` |
| Add table | `doc.add_table(rows=3, cols=4)` |
| Add image | `doc.add_picture("img.png", width=Inches(5))` |
| Page break | `doc.add_page_break()` |
| Save | `doc.save("output.docx")` |
| Open existing | `doc = Document("existing.docx")` |

## Common Patterns

### Contract Template
```python
sections = [
    {"heading": "AGREEMENT", "level": 0},
    {"content": "This agreement is made between..."},
    {"heading": "1. Terms", "level": 1},
    {"content": "The following terms apply..."},
    {"heading": "2. Payment", "level": 1},
    {"table": {"headers": ["Item", "Amount"], "data": [["Service", "$1000"]]}}
]
```

### Technical Report
```python
sections = [
    {"heading": "Executive Summary", "level": 1},
    {"content": "..."},
    {"heading": "Methodology", "level": 1},
    {"bullets": ["Step 1", "Step 2", "Step 3"]},
    {"heading": "Results", "level": 1},
    {"image": "chart.png", "caption": "Figure 1: Results"},
    {"heading": "Conclusion", "level": 1}
]
```
