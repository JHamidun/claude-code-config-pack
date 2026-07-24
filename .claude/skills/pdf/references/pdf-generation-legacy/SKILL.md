---
name: pdf-generation
description: "PDF Generation & Manipulation Skill"
---

# PDF Generation & Manipulation Skill

## Overview

Expert skill for creating and manipulating PDF documents using Python with reportlab, PyPDF2, and pdfplumber.

## When to Use

- Creating PDF reports from scratch
- Merging/splitting PDFs
- Adding watermarks
- Extracting text/tables from PDFs
- Converting data to PDF format

## Dependencies

```bash
pip install reportlab PyPDF2 pdfplumber
```

## Core Operations

### 1. Create PDF from Scratch (ReportLab)

```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfgen import canvas

def create_professional_pdf(output_path: str, title: str, content: list):
    """Create a professionally formatted PDF."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=30,
        alignment=1  # Center
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c5282'),
        spaceBefore=20,
        spaceAfter=10
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=12
    )

    # Build content
    story = []

    # Title
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))

    for item in content:
        if item['type'] == 'heading':
            story.append(Paragraph(item['text'], heading_style))
        elif item['type'] == 'paragraph':
            story.append(Paragraph(item['text'], body_style))
        elif item['type'] == 'table':
            story.append(create_styled_table(item['data'], item.get('headers')))
            story.append(Spacer(1, 20))
        elif item['type'] == 'image':
            img = Image(item['path'], width=item.get('width', 400))
            story.append(img)
            story.append(Spacer(1, 10))
        elif item['type'] == 'pagebreak':
            story.append(PageBreak())

    doc.build(story)
    return output_path

def create_styled_table(data: list, headers: list = None):
    """Create a styled table."""
    if headers:
        data = [headers] + data

    table = Table(data)

    style = TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

        # Data styling
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#4a5568')),

        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])

    table.setStyle(style)
    return table
```

### 2. PDF with Custom Header/Footer

```python
def create_pdf_with_header_footer(output_path: str, content: list,
                                   header_text: str, footer_text: str):
    """Create PDF with custom header and footer."""

    def add_header_footer(canvas, doc):
        canvas.saveState()

        # Header
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(colors.HexColor('#4a5568'))
        canvas.drawString(72, A4[1] - 40, header_text)
        canvas.line(72, A4[1] - 45, A4[0] - 72, A4[1] - 45)

        # Footer
        canvas.setFont('Helvetica', 9)
        canvas.drawString(72, 30, footer_text)
        canvas.drawRightString(A4[0] - 72, 30, f"Page {doc.page}")
        canvas.line(72, 40, A4[0] - 72, 40)

        canvas.restoreState()

    doc = SimpleDocTemplate(output_path, pagesize=A4)
    doc.build(content, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
```

### 3. Merge PDFs

```python
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

def merge_pdfs(pdf_list: list, output_path: str):
    """Merge multiple PDFs into one."""
    merger = PdfMerger()

    for pdf in pdf_list:
        merger.append(pdf)

    merger.write(output_path)
    merger.close()
    return output_path

def merge_specific_pages(pdf_path: str, pages: list, output_path: str):
    """Extract specific pages from a PDF."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page_num in pages:
        writer.add_page(reader.pages[page_num])

    with open(output_path, 'wb') as output:
        writer.write(output)

    return output_path
```

### 4. Split PDF

```python
def split_pdf(input_path: str, output_dir: str):
    """Split PDF into individual pages."""
    reader = PdfReader(input_path)
    output_files = []

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)

        output_path = f"{output_dir}/page_{i+1}.pdf"
        with open(output_path, 'wb') as output:
            writer.write(output)
        output_files.append(output_path)

    return output_files

def split_pdf_ranges(input_path: str, ranges: list, output_dir: str):
    """Split PDF by page ranges.

    ranges = [(1, 5), (6, 10), (11, 15)]  # Page numbers (1-indexed)
    """
    reader = PdfReader(input_path)
    output_files = []

    for i, (start, end) in enumerate(ranges):
        writer = PdfWriter()

        for page_num in range(start - 1, end):
            writer.add_page(reader.pages[page_num])

        output_path = f"{output_dir}/section_{i+1}.pdf"
        with open(output_path, 'wb') as output:
            writer.write(output)
        output_files.append(output_path)

    return output_files
```

### 5. Add Watermark

```python
def add_watermark(input_path: str, watermark_path: str, output_path: str):
    """Add watermark to all pages."""
    reader = PdfReader(input_path)
    watermark = PdfReader(watermark_path)
    writer = PdfWriter()

    watermark_page = watermark.pages[0]

    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    with open(output_path, 'wb') as output:
        writer.write(output)

    return output_path

def create_text_watermark(text: str, output_path: str,
                          font_size: int = 60, opacity: float = 0.3):
    """Create a watermark PDF with text."""
    c = canvas.Canvas(output_path, pagesize=A4)

    c.saveState()
    c.setFillColor(colors.grey)
    c.setFillAlpha(opacity)
    c.setFont('Helvetica-Bold', font_size)

    # Rotate and position watermark
    c.translate(A4[0]/2, A4[1]/2)
    c.rotate(45)
    c.drawCentredString(0, 0, text)

    c.restoreState()
    c.save()

    return output_path
```

### 6. Extract Text from PDF

```python
import pdfplumber

def extract_text(pdf_path: str) -> str:
    """Extract all text from PDF."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_tables(pdf_path: str) -> list:
    """Extract tables from PDF."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            tables.extend(page_tables)
    return tables

def extract_text_by_page(pdf_path: str) -> dict:
    """Extract text with page numbers."""
    pages = {}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            pages[i] = page.extract_text()
    return pages
```

### 7. PDF Metadata

```python
def get_pdf_info(pdf_path: str) -> dict:
    """Get PDF metadata."""
    reader = PdfReader(pdf_path)

    return {
        "pages": len(reader.pages),
        "metadata": dict(reader.metadata) if reader.metadata else {},
        "encrypted": reader.is_encrypted
    }

def set_pdf_metadata(input_path: str, output_path: str, metadata: dict):
    """Set PDF metadata."""
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.add_metadata(metadata)

    with open(output_path, 'wb') as output:
        writer.write(output)

    return output_path
```

### 8. Complete Report Generator

```python
def generate_report(
    output_path: str,
    title: str,
    author: str,
    sections: list,
    include_toc: bool = True
):
    """
    Generate a complete PDF report.

    sections = [
        {"type": "heading", "text": "Introduction", "level": 1},
        {"type": "paragraph", "text": "Content here..."},
        {"type": "table", "headers": ["A", "B"], "data": [[1, 2], [3, 4]]},
        {"type": "image", "path": "chart.png", "width": 400, "caption": "Figure 1"},
        {"type": "pagebreak"}
    ]
    """
    content = []
    styles = getSampleStyleSheet()

    # Title page
    content.append(Spacer(1, 2*inch))
    content.append(Paragraph(title, styles['Title']))
    content.append(Spacer(1, 0.5*inch))
    content.append(Paragraph(f"Author: {author}", styles['Normal']))
    content.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    content.append(PageBreak())

    # Process sections
    for section in sections:
        if section['type'] == 'heading':
            level = section.get('level', 1)
            style = styles[f'Heading{level}']
            content.append(Paragraph(section['text'], style))

        elif section['type'] == 'paragraph':
            content.append(Paragraph(section['text'], styles['Normal']))

        elif section['type'] == 'table':
            table = create_styled_table(section['data'], section.get('headers'))
            content.append(table)
            content.append(Spacer(1, 12))

        elif section['type'] == 'image':
            img = Image(section['path'], width=section.get('width', 400))
            content.append(img)
            if section.get('caption'):
                content.append(Paragraph(
                    f"<i>{section['caption']}</i>",
                    ParagraphStyle('Caption', parent=styles['Normal'],
                                   alignment=1, fontSize=9)
                ))
            content.append(Spacer(1, 12))

        elif section['type'] == 'pagebreak':
            content.append(PageBreak())

    # Build PDF
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    doc.build(content)

    return output_path
```

## Quick Reference

| Task | Library | Code |
|------|---------|------|
| Create PDF | reportlab | `SimpleDocTemplate().build(content)` |
| Read PDF | PyPDF2 | `PdfReader(path)` |
| Merge PDFs | PyPDF2 | `PdfMerger().append()` |
| Extract text | pdfplumber | `page.extract_text()` |
| Add watermark | PyPDF2 | `page.merge_page(watermark)` |
| Split PDF | PyPDF2 | `PdfWriter().add_page()` |

## Tips

1. Use reportlab for creating PDFs from scratch
2. Use PyPDF2 for manipulation (merge, split, watermark)
3. Use pdfplumber for text/table extraction
4. Always close file handles properly
5. For large PDFs, process page by page
