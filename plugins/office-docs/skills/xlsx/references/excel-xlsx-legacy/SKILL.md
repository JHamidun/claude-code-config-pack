---
name: excel-xlsx
description: "Excel / XLSX Skill"
---

# Excel / XLSX Skill

## Overview

Expert skill for creating professional Excel spreadsheets. Core principle: enrich visuals while ensuring content clarity. Every visual element should serve the content, not decorate it.

## When to Use

- Creating Excel reports with formatting
- Data analysis and manipulation
- Financial reports and dashboards
- Converting data to/from Excel
- Multi-sheet workbooks
- Formulas and calculations

## Dependencies

```bash
pip install openpyxl pandas xlsxwriter
```

---

## Part 1: User Needs & Feature Matching

Before creating any Excel, think through what the user needs and match features to user value.

### Help Users Understand Data

| Feature | User Value | When to Use |
|---------|-----------|-------------|
| Bar/Column Chart | Compare values across categories | Categorical comparisons (sales by region, scores by team) |
| Line Chart | See trends over time | Time series data (monthly revenue, daily users) |
| Pie Chart | See proportions of a whole | 3-6 categories that sum to 100% |
| Data Bars | Quick visual comparison within cells | Numeric columns where relative size matters |
| Color Scale | Spot highs and lows at a glance | Dense numeric data (heatmap effect) |
| Sparklines | See per-row trends without a full chart | When each row has its own time series |

### Help Users Find What Matters

| Feature | User Value | When to Use |
|---------|-----------|-------------|
| Pre-sorting | Most important data visible first | Sort by key metric descending |
| Conditional Highlighting | Attention drawn to outliers | Values above/below thresholds |
| Icon Sets | Quick status assessment | Traffic lights for KPI status |
| Bold/Color Emphasis | Key rows stand out | Totals, subtotals, summary rows |
| KEY INSIGHTS Section | Immediate takeaways without analysis | Always include on Overview sheet |

### Help Users Save Time

| Feature | User Value | When to Use |
|---------|-----------|-------------|
| Overview Sheet | Grasp everything in 30 seconds | Always (first sheet in workbook) |
| Pre-calculated Summaries | No manual calculation needed | Totals, averages, percentages |
| Consistent Number Formats | No mental parsing of formats | Apply to every numeric cell |
| Freeze Panes | Headers visible while scrolling | Tables with >10 rows |
| Sheet Index with Links | Navigate quickly between sheets | Workbooks with 3+ sheets |

### Help Users Use Directly

| Feature | User Value | When to Use |
|---------|-----------|-------------|
| Filters | Slice data without editing | Tables with >20 rows |
| Hyperlinks | Navigate to related content | Cross-sheet references, URLs |
| Print-friendly Layout | Clean output on paper | Reports intended for printing |
| Formulas not hardcoded | Users can update inputs | Calculations, projections |
| Data Validation Dropdowns | Guided data entry | Input cells with known options |

### Help Users Trust the Data

| Feature | User Value | When to Use |
|---------|-----------|-------------|
| Data Source Attribution | Know where data came from | Always |
| Generation Date | Know how current data is | Always |
| Data Time Range | Know what period is covered | Time-based data |
| Professional Formatting | Perceive quality and care | Always |
| Consistent Precision | No confusing decimal variation | All numeric columns |

### Help Users Gain Insights

| Feature | User Value | When to Use |
|---------|-----------|-------------|
| Comparison Columns | See differences/changes | Period-over-period data |
| Rank Column | Know relative position | Performance data |
| Grouped Summaries | See patterns by category | Data with natural groupings |
| Trend Indicators | Quick up/down/flat signal | Change metrics |
| Insight Text | Narrative explanation of data | Complex or surprising results |

---

## Part 2: Four-Layer Implementation

### Layer 1: Structure

#### Sheet Organization

| Guideline | Rule |
|-----------|------|
| Ideal sheet count | 3-5 sheets |
| Maximum sheets | 7 (more becomes hard to navigate) |
| First sheet | Always "Overview" or "Summary" |
| Sheet naming | Short, descriptive, no special characters |
| Sheet order | Overview > Detail > Charts > Reference |

#### Layout Rules

| Element | Rule |
|---------|------|
| Left margin | Column A, width 3 (visual breathing room) |
| Content start | Cell B2 (never A1) |
| Section spacing | 1 empty row between sections |
| Table spacing | 2 empty rows between tables |
| Right margin | 1 empty column after last data column |

#### Standalone Text Rows

Use standalone text rows (outside tables) for:
- Document title
- Section headers
- KEY INSIGHTS text
- Source attribution and generation date
- Notes and definitions

Do NOT put these inside data tables. They break filters and sorting.

#### Navigation (Sheet Index)

For workbooks with 3+ sheets, add a clickable index on the Overview sheet:

```python
def add_sheet_index(wb, overview_ws, start_row=5, col=2):
    """Add clickable sheet index to Overview sheet."""
    overview_ws.cell(row=start_row, column=col, value="Sheet Index")
    overview_ws.cell(row=start_row, column=col).font = Font(
        name='Source Serif Pro', bold=True, size=13
    )
    for i, sheet_name in enumerate(wb.sheetnames):
        row = start_row + 1 + i
        cell = overview_ws.cell(row=row, column=col, value=sheet_name)
        cell.hyperlink = f"#'{sheet_name}'!A1"
        cell.font = Font(name='Source Sans Pro', color="0563C1", underline="single", size=11)
```

---

### Layer 2: Information

#### Number Formats

| Type | Format | Example |
|------|--------|---------|
| Integer | `#,##0` | 1,234 |
| Decimal | `#,##0.00` | 1,234.56 |
| Percentage | `0.0%` | 12.3% |
| Currency (USD) | `$#,##0.00` | $1,234.56 |
| Currency (RUB) | `#,##0.00 "RUB"` | 1,234.56 RUB |
| Date | `YYYY-MM-DD` | (see git history) |
| Accounting | `_($* #,##0.00_)` | $1,234.56 |

**CRITICAL:** Every numeric cell MUST have `number_format` set, including formula result cells.

```python
# WRONG: formula cell has no format
cell = ws.cell(row=10, column=3)
cell.value = "=SUM(C2:C9)"

# CORRECT: formula cell has explicit format
cell = ws.cell(row=10, column=3)
cell.value = "=SUM(C2:C9)"
cell.number_format = '#,##0.00'
```

#### Data Context

Always include these metadata elements, typically on the Overview sheet:

| Element | Where | Example |
|---------|-------|---------|
| Data Source | Below title | "Source: CRM Export, Salesforce" |
| Time Range | Below source | "Period: Jan 2025 - Dec 2025" |
| Generation Date | Footer or below time range | "Generated: (see git history)" |
| Definitions | Footnotes or separate sheet | "MRR = Monthly Recurring Revenue" |

#### KEY INSIGHTS Section

Add to the Overview sheet, below the title and before detailed data:

```python
def add_key_insights(ws, insights: list[str], start_row=3, col=2):
    """Add KEY INSIGHTS section to a worksheet."""
    cell = ws.cell(row=start_row, column=col, value="KEY INSIGHTS")
    cell.font = Font(name='Source Serif Pro', bold=True, size=12, color="1A1A1A")

    for i, insight in enumerate(insights):
        row = start_row + 1 + i
        cell = ws.cell(row=row, column=col, value=f"  {insight}")
        cell.font = Font(name='Source Sans Pro', size=11, color="333333")
```

#### Content Completeness

Before finalizing, verify:
- [ ] All numeric cells have number_format
- [ ] All tables have headers
- [ ] Source and date are present
- [ ] No empty columns in the middle of data
- [ ] Totals/summaries where expected

---

### Layer 3: Visual

#### Essential Setup

Apply to every worksheet before adding content:

```python
def setup_worksheet(ws):
    """Essential setup for every worksheet."""
    ws.sheet_view.showGridLines = False       # Hide gridlines
    ws.column_dimensions['A'].width = 3       # Left margin
```

#### Theme System

12 built-in themes. Default: Elegant Black. Choose based on context.

| Theme | Header BG | Header Text | Accent | Best For |
|-------|----------|-------------|--------|----------|
| Elegant Black | 1A1A1A | FFFFFF | 2C2C2C | Default, formal reports |
| Corporate Blue | 1F4E79 | FFFFFF | 2E75B6 | Business, corporate |
| Forest Green | 1B5E20 | FFFFFF | 2E7D32 | Environmental, growth |
| Burgundy | 7B1F3A | FFFFFF | A0153E | Premium, executive |
| Slate Gray | 37474F | FFFFFF | 546E7A | Technical, engineering |
| Navy | 0D1B2A | FFFFFF | 1B3A5C | Finance, government |
| Charcoal | 2C2C2C | FFFFFF | 404040 | Minimalist |
| Deep Purple | 311B92 | FFFFFF | 4527A0 | Creative, marketing |
| Teal | 004D40 | FFFFFF | 00695C | Healthcare, wellness |
| Warm Brown | 3E2723 | FFFFFF | 5D4037 | Legal, traditional |
| Royal Blue | 1A237E | FFFFFF | 283593 | Academic, research |
| Olive | 33691E | FFFFFF | 558B2F | Agriculture, sustainability |

```python
THEMES = {
    "elegant_black": {
        "header_bg": "1A1A1A",
        "header_text": "FFFFFF",
        "accent": "2C2C2C",
        "alt_row": "F5F5F5",
        "border": "D0D0D0",
        "chart_colors": ["1A1A1A", "5B5B5B", "8C8C8C", "B0B0B0", "D4D4D4", "E8E8E8"],
    },
    "corporate_blue": {
        "header_bg": "1F4E79",
        "header_text": "FFFFFF",
        "accent": "2E75B6",
        "alt_row": "D6E4F0",
        "border": "9DC3E6",
        "chart_colors": ["1F4E79", "2E75B6", "5B9BD5", "9DC3E6", "BDD7EE", "DEEBF7"],
    },
    "forest_green": {
        "header_bg": "1B5E20",
        "header_text": "FFFFFF",
        "accent": "2E7D32",
        "alt_row": "E8F5E9",
        "border": "A5D6A7",
        "chart_colors": ["1B5E20", "2E7D32", "43A047", "66BB6A", "81C784", "A5D6A7"],
    },
    "burgundy": {
        "header_bg": "7B1F3A",
        "header_text": "FFFFFF",
        "accent": "A0153E",
        "alt_row": "FCE4EC",
        "border": "E57373",
        "chart_colors": ["7B1F3A", "A0153E", "C62828", "E53935", "EF5350", "E57373"],
    },
    "slate_gray": {
        "header_bg": "37474F",
        "header_text": "FFFFFF",
        "accent": "546E7A",
        "alt_row": "ECEFF1",
        "border": "B0BEC5",
        "chart_colors": ["37474F", "546E7A", "78909C", "90A4AE", "B0BEC5", "CFD8DC"],
    },
    "navy": {
        "header_bg": "0D1B2A",
        "header_text": "FFFFFF",
        "accent": "1B3A5C",
        "alt_row": "E3F2FD",
        "border": "90CAF9",
        "chart_colors": ["0D1B2A", "1B3A5C", "1565C0", "1E88E5", "42A5F5", "90CAF9"],
    },
    "charcoal": {
        "header_bg": "2C2C2C",
        "header_text": "FFFFFF",
        "accent": "404040",
        "alt_row": "F5F5F5",
        "border": "BDBDBD",
        "chart_colors": ["2C2C2C", "404040", "616161", "757575", "9E9E9E", "BDBDBD"],
    },
    "deep_purple": {
        "header_bg": "311B92",
        "header_text": "FFFFFF",
        "accent": "4527A0",
        "alt_row": "EDE7F6",
        "border": "B39DDB",
        "chart_colors": ["311B92", "4527A0", "512DA8", "673AB7", "7E57C2", "B39DDB"],
    },
    "teal": {
        "header_bg": "004D40",
        "header_text": "FFFFFF",
        "accent": "00695C",
        "alt_row": "E0F2F1",
        "border": "80CBC4",
        "chart_colors": ["004D40", "00695C", "00897B", "009688", "26A69A", "80CBC4"],
    },
    "warm_brown": {
        "header_bg": "3E2723",
        "header_text": "FFFFFF",
        "accent": "5D4037",
        "alt_row": "EFEBE9",
        "border": "BCAAA4",
        "chart_colors": ["3E2723", "5D4037", "6D4C41", "795548", "8D6E63", "BCAAA4"],
    },
    "royal_blue": {
        "header_bg": "1A237E",
        "header_text": "FFFFFF",
        "accent": "283593",
        "alt_row": "E8EAF6",
        "border": "9FA8DA",
        "chart_colors": ["1A237E", "283593", "303F9F", "3949AB", "5C6BC0", "9FA8DA"],
    },
    "olive": {
        "header_bg": "33691E",
        "header_text": "FFFFFF",
        "accent": "558B2F",
        "alt_row": "F1F8E9",
        "border": "AED581",
        "chart_colors": ["33691E", "558B2F", "689F38", "7CB342", "8BC34A", "AED581"],
    },
}

def get_theme(name: str = "elegant_black") -> dict:
    """Get theme configuration by name."""
    return THEMES.get(name, THEMES["elegant_black"])
```

#### How Theme Colors Apply

| Element | Color Source |
|---------|------------|
| Table header background | `header_bg` |
| Table header text | `header_text` |
| Section header text | `header_bg` |
| Alternating row fill | `alt_row` |
| Borders | `border` |
| Chart series colors | `chart_colors` list |
| Accent elements (subtotals, highlights) | `accent` |

#### Semantic Colors (Theme-Independent)

| Meaning | Hex | Usage |
|---------|-----|-------|
| Positive / Growth | `2E7D32` | Positive changes, profits, growth |
| Negative / Decline | `C62828` | Negative changes, losses, decline |
| Warning / Attention | `F57C00` | Thresholds, warnings |

#### Row Highlight Colors

| Purpose | Hex | When to Use |
|---------|-----|-------------|
| Emphasis row | `E6F3FF` | Important data rows |
| Section divider | `FFF3E0` | Category group headers |
| Input cell | `FFFDE7` | Cells users should edit |
| Special note | `FFF9C4` | Footnotes, annotations |
| Success | `E8F5E9` | Achieved targets |
| Warning | `FFCCBC` | Below-threshold values |

#### Typography

Use a serif + sans-serif font pairing. Serif for headers and titles (authority, structure), sans-serif for data and body text (readability).

**Recommended Pairings:**

| Serif (Titles/Headers) | Sans-Serif (Data/Body) | Character |
|------------------------|----------------------|-----------|
| Source Serif Pro | Source Sans Pro | Modern professional |
| IBM Plex Serif | IBM Plex Sans | Technical, clean |
| Georgia | Calibri | Safe fallback (installed everywhere) |

**Typography Hierarchy:**

| Element | Font | Weight | Size | Color |
|---------|------|--------|------|-------|
| Document title | Serif | Bold | 18-22 | header_bg from theme |
| Section header | Serif | Bold | 12-14 | header_bg from theme |
| Table header | Serif | Bold | 10-11 | header_text (on header_bg fill) |
| Data cells | Sans-Serif | Normal | 11 | 1A1A1A |
| Notes / footnotes | Sans-Serif | Normal | 9-10 | 666666 |

#### Data Block Definition

A "Data Block" is any rectangular range of cells that forms a logical unit: a table, a summary block, a key metrics panel. Identify data blocks by:
- Contiguous cells with related content
- Common header row
- Consistent column structure

#### Border Rules (Horizontal-Only Style)

Use horizontal-only borders within data blocks. This creates a clean, modern look.

| Border Element | Style | Where |
|---------------|-------|-------|
| Outer frame | Thin, all 4 sides | Around the entire data block |
| Header bottom | Medium, bottom only | Below the header row |
| Internal horizontal | Thin, bottom only | Between data rows |
| Internal vertical | **NONE** | Never use vertical borders between columns |

```python
from openpyxl.styles import Border, Side

def apply_data_block_borders(ws, min_row, max_row, min_col, max_col, theme_name="elegant_black"):
    """Apply horizontal-only border style to a data block.

    Args:
        ws: Worksheet object
        min_row: First row of the block (header row)
        max_row: Last row of the block
        min_col: First column of the block
        max_col: Last column of the block
        theme_name: Theme to use for border color
    """
    theme = get_theme(theme_name)
    border_color = theme["border"]

    thin = Side(style='thin', color=border_color)
    medium = Side(style='medium', color=border_color)
    no_side = Side(style=None)

    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col + 1):
            cell = ws.cell(row=row, column=col)

            # Determine border sides
            top = thin if row == min_row else no_side
            left = thin if col == min_col else no_side
            right = thin if col == max_col else no_side

            if row == min_row:
                # Header row: medium bottom
                bottom = medium
            elif row == max_row:
                # Last row: thin bottom (outer frame)
                bottom = thin
            else:
                # Internal rows: thin bottom only
                bottom = thin

            cell.border = Border(top=top, bottom=bottom, left=left, right=right)
```

#### Alignment Rules

| Content Type | Horizontal | Indent | Example |
|-------------|-----------|--------|---------|
| Short text (< 20 chars) | Center | 0 | Status, Category |
| Long text (>= 20 chars) | Left | 1 | Description, Notes |
| Numbers | Right | 0 | 1,234.56 |
| Dates | Center | 0 | (see git history) |
| Headers | Center | 0 | Column headers |
| Percentages | Right | 0 | 12.3% |

#### Column Width

Calculate based on content length with padding:

```python
def calculate_column_width(ws, col_idx, min_width=8, max_width=50, padding=3):
    """Calculate optimal column width based on content.

    Formula: max_content_length + padding, clamped to [min_width, max_width].
    """
    max_length = 0
    for row in ws.iter_rows(min_col=col_idx, max_col=col_idx):
        for cell in row:
            if cell.value:
                cell_length = len(str(cell.value))
                # Bold text needs ~10% more space
                if cell.font and cell.font.bold:
                    cell_length = int(cell_length * 1.1)
                max_length = max(max_length, cell_length)

    width = max_length + padding
    return max(min_width, min(width, max_width))
```

#### Row Heights

| Element | Height (points) |
|---------|----------------|
| Document title | 35 |
| Section header | 25 |
| Table header | 30 |
| Standard data row | 18 |
| Wrapped text | lines x 15 + 10 |

#### Merge Cells Guidelines

- DO merge for document titles spanning the content area
- DO merge for section headers
- DO NOT merge within data tables (breaks sorting and filtering)
- When merging, always set alignment to center-left or center

#### Data Visualization

**Data Bars:** Add to numeric columns for in-cell comparison:

```python
from openpyxl.formatting.rule import DataBarRule

rule = DataBarRule(start_type='min', end_type='max',
                   color="5B9BD5", showValue=True)
ws.conditional_formatting.add("C2:C100", rule)
```

**Color Scale:** For heatmap effect on dense data:

```python
from openpyxl.formatting.rule import ColorScaleRule

rule = ColorScaleRule(
    start_type='min', start_color='63BE7B',
    mid_type='percentile', mid_value=50, mid_color='FFEB84',
    end_type='max', end_color='F8696B'
)
ws.conditional_formatting.add("B2:F20", rule)
```

**Charts:** Always use theme `chart_colors` for series:

```python
from openpyxl.chart.series import DataPoint
from openpyxl.drawing.fill import PatternFillProperties, ColorChoice

theme = get_theme("corporate_blue")
# Apply chart_colors to chart series
for i, series in enumerate(chart.series):
    color_idx = i % len(theme["chart_colors"])
    series.graphicalProperties.solidFill = theme["chart_colors"][color_idx]
```

---

### Layer 4: Interaction

#### Freeze Panes

Apply when table has more than 10 rows:

```python
# Freeze below header row (row 1 = header)
ws.freeze_panes = 'A2'

# If content starts at B5 with header in row 5
ws.freeze_panes = 'B6'
```

#### Filters

Apply when table has more than 20 rows:

```python
ws.auto_filter.ref = f"B5:{get_column_letter(max_col)}{max_row}"
```

#### Hyperlinks

```python
# Internal link (to another sheet)
cell.hyperlink = "#'Detail Sheet'!A1"
cell.font = Font(color="0563C1", underline="single")

# External link
cell.hyperlink = "https://example.com/report"
cell.font = Font(color="0563C1", underline="single")
```

#### Pre-sorting Rules

| Data Type | Default Sort |
|-----------|-------------|
| Financial/performance | By key metric, descending |
| Time series | Chronological (ascending) |
| Categorical | Alphabetical or by rank |
| Mixed | By importance/relevance |

#### Editability Guidelines

- Mark input cells with yellow background (`FFFDE7`)
- Lock all non-input cells with sheet protection
- Add data validation dropdowns for constrained inputs
- Include instructions for editable fields

---

## Core Operations

### 1. Create New Workbook

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import BarChart, PieChart, LineChart, Reference
import pandas as pd

def create_styled_workbook(data: dict, output_path: str, theme_name: str = "elegant_black"):
    """Create a professionally styled Excel workbook using the theme system."""
    theme = get_theme(theme_name)
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    setup_worksheet(ws)

    # Styles from theme
    header_font = Font(
        name='Source Serif Pro', bold=True,
        color=theme["header_text"], size=11
    )
    header_fill = PatternFill(
        start_color=theme["header_bg"],
        end_color=theme["header_bg"],
        fill_type="solid"
    )
    data_font = Font(name='Source Sans Pro', size=11, color="1A1A1A")

    # Write headers
    headers = list(data.keys())
    for col, header in enumerate(headers, 2):  # Start at col B
        cell = ws.cell(row=2, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')

    # Write data
    max_rows = max(len(v) for v in data.values())
    alt_fill = PatternFill(start_color=theme["alt_row"], end_color=theme["alt_row"], fill_type="solid")

    for row in range(max_rows):
        for col, header in enumerate(headers, 2):
            values = data[header]
            value = values[row] if row < len(values) else ""
            cell = ws.cell(row=row + 3, column=col, value=value)
            cell.font = data_font
            if row % 2 == 1:
                cell.fill = alt_fill

    # Apply borders
    apply_data_block_borders(ws, 2, max_rows + 2, 2, len(headers) + 1, theme_name)

    # Auto-adjust column widths
    for col_idx in range(2, len(headers) + 2):
        width = calculate_column_width(ws, col_idx)
        ws.column_dimensions[ws.cell(row=2, column=col_idx).column_letter].width = width

    wb.save(output_path)
    return output_path
```

### 2. Read Excel File

```python
import pandas as pd

def read_excel_smart(file_path: str, sheet_name=None):
    """Read Excel file with automatic type detection."""
    if sheet_name is None:
        xl = pd.ExcelFile(file_path)
        sheets = {name: pd.read_excel(xl, sheet_name=name) for name in xl.sheet_names}
        return sheets

    return pd.read_excel(file_path, sheet_name=sheet_name)

def read_excel_with_headers(file_path: str, header_row: int = 0):
    """Read Excel with specified header row."""
    return pd.read_excel(file_path, header=header_row)
```

### 3. Add Charts

```python
from openpyxl.chart import BarChart, LineChart, PieChart, Reference

def add_bar_chart(ws, data_range: str, title: str, position: str = "E2"):
    """Add a bar chart to worksheet."""
    chart = BarChart()
    chart.type = "col"
    chart.title = title
    chart.style = 10

    data = Reference(ws, range_string=data_range)
    chart.add_data(data, titles_from_data=True)

    ws.add_chart(chart, position)

def add_pie_chart(ws, labels_col: int, data_col: int,
                  min_row: int, max_row: int, title: str, position: str = "E2"):
    """Add a pie chart."""
    chart = PieChart()
    chart.title = title

    labels = Reference(ws, min_col=labels_col, min_row=min_row, max_row=max_row)
    data = Reference(ws, min_col=data_col, min_row=min_row-1, max_row=max_row)

    chart.add_data(data, titles_from_data=True)
    chart.set_categories(labels)

    ws.add_chart(chart, position)

def add_line_chart(ws, data_range: str, title: str, position: str = "E2"):
    """Add a line chart."""
    chart = LineChart()
    chart.title = title
    chart.style = 10
    chart.y_axis.title = "Value"
    chart.x_axis.title = "Period"

    data = Reference(ws, range_string=data_range)
    chart.add_data(data, titles_from_data=True)

    ws.add_chart(chart, position)
```

### 4. Formulas & Calculations

```python
def add_formulas(ws, start_row: int, end_row: int, formula_col: int,
                 data_col: int, formula_type: str = "SUM"):
    """Add formulas to a column. Always set number_format on formula cells."""
    col_letter = ws.cell(row=1, column=data_col).column_letter

    if formula_type == "SUM":
        cell = ws.cell(row=end_row+1, column=formula_col)
        cell.value = f"=SUM({col_letter}{start_row}:{col_letter}{end_row})"
        cell.number_format = '#,##0.00'
    elif formula_type == "AVERAGE":
        cell = ws.cell(row=end_row+1, column=formula_col)
        cell.value = f"=AVERAGE({col_letter}{start_row}:{col_letter}{end_row})"
        cell.number_format = '#,##0.00'
    elif formula_type == "ROW_CALC":
        for row in range(start_row, end_row+1):
            cell = ws.cell(row=row, column=formula_col)
            cell.value = f"=A{row}*B{row}"  # Customize formula
            cell.number_format = '#,##0.00'

def add_conditional_formatting(ws, cell_range: str, threshold: float):
    """Add conditional formatting with color scale and formula-based rules."""
    from openpyxl.formatting.rule import ColorScaleRule, FormulaRule
    from openpyxl.styles import PatternFill

    # Color scale (green to red)
    rule = ColorScaleRule(
        start_type='min', start_color='63BE7B',
        mid_type='percentile', mid_value=50, mid_color='FFEB84',
        end_type='max', end_color='F8696B'
    )
    ws.conditional_formatting.add(cell_range, rule)

    # Formula-based rule
    red_fill = PatternFill(start_color='FF0000', end_color='FF0000', fill_type='solid')
    rule = FormulaRule(formula=[f'A1>{threshold}'], fill=red_fill)
    ws.conditional_formatting.add(cell_range, rule)
```

### 5. DataFrame to Excel with Styling

```python
def dataframe_to_styled_excel(df: pd.DataFrame, output_path: str,
                               sheet_name: str = "Data",
                               theme_name: str = "elegant_black"):
    """Convert DataFrame to styled Excel using the theme system."""
    theme = get_theme(theme_name)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, startcol=1)

        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        setup_worksheet(worksheet)

        # Style headers
        header_font = Font(name='Source Serif Pro', bold=True, color=theme["header_text"], size=11)
        header_fill = PatternFill(start_color=theme["header_bg"], fill_type="solid")

        for col_num, column_title in enumerate(df.columns, 2):
            cell = worksheet.cell(row=2, column=col_num)
            cell.font = header_font
            cell.fill = header_fill

        # Style data cells
        data_font = Font(name='Source Sans Pro', size=11)
        for row in range(3, len(df) + 3):
            for col in range(2, len(df.columns) + 2):
                cell = worksheet.cell(row=row, column=col)
                cell.font = data_font

        # Auto-fit columns
        for col_idx in range(2, len(df.columns) + 2):
            width = calculate_column_width(worksheet, col_idx)
            col_letter = worksheet.cell(row=2, column=col_idx).column_letter
            worksheet.column_dimensions[col_letter].width = width

    return output_path
```

### 6. Multi-Sheet Report

```python
def create_multi_sheet_report(data_dict: dict, output_path: str,
                               theme_name: str = "elegant_black"):
    """Create workbook with multiple themed sheets and an Overview index."""
    theme = get_theme(theme_name)
    wb = Workbook()

    # Create Overview sheet
    overview = wb.active
    overview.title = "Overview"
    setup_worksheet(overview)

    overview.cell(row=2, column=2, value="Report Overview")
    overview.cell(row=2, column=2).font = Font(
        name='Source Serif Pro', bold=True, size=18, color=theme["header_bg"]
    )

    # Create data sheets
    for sheet_name, df in data_dict.items():
        ws = wb.create_sheet(title=sheet_name[:31])  # Excel limit: 31 chars
        setup_worksheet(ws)

        # Write DataFrame
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 2):
            for c_idx, value in enumerate(row, 2):
                ws.cell(row=r_idx, column=c_idx, value=value)

        # Style header row
        for col in range(2, len(df.columns) + 2):
            cell = ws.cell(row=2, column=col)
            cell.font = Font(name='Source Serif Pro', bold=True, color=theme["header_text"])
            cell.fill = PatternFill(start_color=theme["header_bg"], fill_type="solid")

        # Style data with sans-serif font
        for row in range(3, len(df) + 3):
            for col in range(2, len(df.columns) + 2):
                ws.cell(row=row, column=col).font = Font(name='Source Sans Pro', size=11)

    # Add sheet index to Overview
    add_sheet_index(wb, overview, start_row=5, col=2)

    wb.save(output_path)
    return output_path
```

---

## Quick Reference

| Task | Code |
|------|------|
| Create workbook | `wb = Workbook()` |
| Get active sheet | `ws = wb.active` |
| Create sheet | `ws = wb.create_sheet("Name")` |
| Set cell value | `ws['A1'] = "Value"` or `ws.cell(1, 1, "Value")` |
| Read cell | `value = ws['A1'].value` |
| Merge cells | `ws.merge_cells('A1:D1')` |
| Set column width | `ws.column_dimensions['A'].width = 20` |
| Set row height | `ws.row_dimensions[1].height = 30` |
| Freeze panes | `ws.freeze_panes = 'A2'` |
| Add filter | `ws.auto_filter.ref = "A1:D100"` |
| Hide gridlines | `ws.sheet_view.showGridLines = False` |
| Number format | `cell.number_format = '#,##0.00'` |
| Apply theme | `theme = get_theme("corporate_blue")` |
| Save | `wb.save('file.xlsx')` |

## Common Patterns

### Financial Report

```python
# Create P&L statement with theme
data = {
    "Category": ["Revenue", "COGS", "Gross Profit", "OpEx", "Net Income"],
    "Q1": [100000, 40000, 60000, 30000, 30000],
    "Q2": [120000, 48000, 72000, 35000, 37000],
    "Q3": [110000, 44000, 66000, 32000, 34000],
    "Q4": [130000, 52000, 78000, 38000, 40000]
}
create_styled_workbook(data, "financial_report.xlsx", theme_name="navy")
```

### Data Dashboard

```python
# Summary statistics sheet + detail sheet + charts
sheets = {
    "Summary": summary_df,
    "Details": detail_df,
}
create_multi_sheet_report(sheets, "dashboard.xlsx", theme_name="corporate_blue")
```

## Tips

1. Always close workbooks after use
2. Use `with` statement for ExcelWriter
3. Limit sheet names to 31 characters
4. Use `openpyxl` for .xlsx, `xlrd` for .xls (read-only)
5. For large files, use `write_only` mode
6. Always apply a theme -- default to `elegant_black` for formal reports
7. Use `apply_data_block_borders()` on every data table for consistent horizontal-only borders
8. Set `number_format` on EVERY numeric cell, including formula results
9. Pair serif fonts (titles) with sans-serif fonts (data) for professional typography
10. Add KEY INSIGHTS section on Overview sheet so users get value immediately
