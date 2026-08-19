---
name: invoice-organizer
description: "Sort invoices and receipts for tax prep and expense tracking. Triggers: «organize invoices», «expenses for the month»."
---

# Invoice Organizer Skill

## Overview

Организация счетов и чеков для налоговой отчётности и учёта расходов.

## When to Use

- Подготовка к налоговой отчётности
- Учёт бизнес-расходов
- Организация чеков и счетов
- Expense tracking
- Архивирование финансовых документов

## Folder Structure

```
Finances/
├── 2024/
│   ├── Q1/
│   │   ├── January/
│   │   ├── February/
│   │   └── March/
│   └── ...
├── By-Category/
│   ├── Software/
│   ├── Hardware/
│   ├── Services/
│   ├── Travel/
│   ├── Office/
│   └── Other/
├── Tax-Deductible/
│   ├── Business-Expenses/
│   ├── Home-Office/
│   └── Professional-Development/
└── Reports/
    ├── Monthly/
    └── Annual/
```

## Naming Convention

```
YYYY-MM-DD_Vendor_Amount_Category.pdf

Examples:
2024-01-15_AWS_125.99_Software.pdf
2024-01-20_Uber_35.50_Travel.pdf
2024-02-01_Adobe_54.99_Software.pdf
```

## Data Extraction

### Extract from PDF/Image

```python
import re
from datetime import datetime

def extract_invoice_data(text: str) -> dict:
    """Extract key data from invoice text"""

    # Date patterns
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}',
    ]

    # Amount patterns
    amount_patterns = [
        r'Total:?\s*\$?([\d,]+\.?\d*)',
        r'Amount:?\s*\$?([\d,]+\.?\d*)',
        r'Grand Total:?\s*\$?([\d,]+\.?\d*)',
        r'\$\s*([\d,]+\.?\d*)',
    ]

    # Invoice number patterns
    invoice_patterns = [
        r'Invoice\s*#?\s*:?\s*(\w+)',
        r'Invoice Number:?\s*(\w+)',
        r'Ref:?\s*(\w+)',
    ]

    data = {}

    # Extract date
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data['date'] = match.group(0)
            break

    # Extract amount
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1).replace(',', '')
            data['amount'] = float(amount)
            break

    # Extract invoice number
    for pattern in invoice_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data['invoice_number'] = match.group(1)
            break

    return data
```

### OCR with Tesseract

```python
import pytesseract
from PIL import Image

def ocr_invoice(image_path: str) -> str:
    """Extract text from invoice image"""
    image = Image.open(image_path)

    # Preprocess for better OCR
    image = image.convert('L')  # Grayscale

    text = pytesseract.image_to_string(image)
    return text

def process_invoice_image(image_path: str) -> dict:
    """Full pipeline: OCR + extraction"""
    text = ocr_invoice(image_path)
    data = extract_invoice_data(text)
    return data
```

## Expense Categories

```python
EXPENSE_CATEGORIES = {
    'Software': [
        'adobe', 'microsoft', 'aws', 'google cloud', 'github',
        'slack', 'notion', 'figma', 'jetbrains', 'openai'
    ],
    'Hardware': [
        'apple', 'dell', 'lenovo', 'logitech', 'amazon'
    ],
    'Services': [
        'consulting', 'legal', 'accounting', 'marketing'
    ],
    'Travel': [
        'uber', 'lyft', 'airbnb', 'booking', 'airline', 'hotel'
    ],
    'Office': [
        'office depot', 'staples', 'ikea', 'amazon'
    ],
    'Subscriptions': [
        'netflix', 'spotify', 'gym', 'membership'
    ]
}

def categorize_expense(vendor: str, description: str = "") -> str:
    """Auto-categorize expense by vendor/description"""
    text = (vendor + " " + description).lower()

    for category, keywords in EXPENSE_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return 'Other'
```

## Invoice Database

```python
import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Invoice:
    id: Optional[int]
    date: date
    vendor: str
    amount: float
    category: str
    description: str
    file_path: str
    tax_deductible: bool = False
    invoice_number: Optional[str] = None

class InvoiceDatabase:
    def __init__(self, db_path: str = "invoices.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                vendor TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT,
                description TEXT,
                file_path TEXT,
                tax_deductible INTEGER DEFAULT 0,
                invoice_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_invoice(self, invoice: Invoice) -> int:
        cursor = self.conn.execute("""
            INSERT INTO invoices (date, vendor, amount, category, description,
                                  file_path, tax_deductible, invoice_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice.date.isoformat(),
            invoice.vendor,
            invoice.amount,
            invoice.category,
            invoice.description,
            invoice.file_path,
            invoice.tax_deductible,
            invoice.invoice_number
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_by_category(self, category: str) -> list:
        cursor = self.conn.execute(
            "SELECT * FROM invoices WHERE category = ?", (category,)
        )
        return cursor.fetchall()

    def get_by_date_range(self, start: date, end: date) -> list:
        cursor = self.conn.execute(
            "SELECT * FROM invoices WHERE date BETWEEN ? AND ?",
            (start.isoformat(), end.isoformat())
        )
        return cursor.fetchall()

    def get_total_by_category(self, year: int) -> dict:
        cursor = self.conn.execute("""
            SELECT category, SUM(amount) as total
            FROM invoices
            WHERE strftime('%Y', date) = ?
            GROUP BY category
        """, (str(year),))
        return dict(cursor.fetchall())

    def get_tax_deductible_total(self, year: int) -> float:
        cursor = self.conn.execute("""
            SELECT SUM(amount)
            FROM invoices
            WHERE strftime('%Y', date) = ? AND tax_deductible = 1
        """, (str(year),))
        result = cursor.fetchone()[0]
        return result or 0.0
```

## Reports

### Monthly Summary

```python
def generate_monthly_report(db: InvoiceDatabase, year: int, month: int) -> str:
    """Generate monthly expense report"""
    from datetime import date
    import calendar

    _, last_day = calendar.monthrange(year, month)
    start = date(year, month, 1)
    end = date(year, month, last_day)

    invoices = db.get_by_date_range(start, end)

    # Group by category
    by_category = {}
    for inv in invoices:
        cat = inv[4]  # category column
        amount = inv[3]  # amount column
        by_category[cat] = by_category.get(cat, 0) + amount

    # Generate report
    report = f"""
# Monthly Expense Report
## {calendar.month_name[month]} {year}

### Summary
- Total Expenses: ${sum(by_category.values()):.2f}
- Number of Invoices: {len(invoices)}

### By Category
"""
    for cat, total in sorted(by_category.items(), key=lambda x: -x[1]):
        report += f"- {cat}: ${total:.2f}\n"

    return report
```

### Tax Report

```python
def generate_tax_report(db: InvoiceDatabase, year: int) -> str:
    """Generate tax-ready expense report"""
    totals = db.get_total_by_category(year)
    tax_deductible = db.get_tax_deductible_total(year)

    report = f"""
# Tax Expense Report {year}

## Summary
- Total Business Expenses: ${sum(totals.values()):.2f}
- Tax Deductible Expenses: ${tax_deductible:.2f}

## Expenses by Category
"""
    for cat, total in sorted(totals.items(), key=lambda x: -x[1]):
        report += f"| {cat} | ${total:.2f} |\n"

    return report
```

## Automation

### Watch Folder

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil

class InvoiceHandler(FileSystemEventHandler):
    def __init__(self, db: InvoiceDatabase, output_dir: str):
        self.db = db
        self.output_dir = output_dir

    def on_created(self, event):
        if event.is_directory:
            return

        if event.src_path.lower().endswith(('.pdf', '.jpg', '.png')):
            self.process_invoice(event.src_path)

    def process_invoice(self, file_path: str):
        # 1. OCR if image
        if file_path.lower().endswith(('.jpg', '.png')):
            text = ocr_invoice(file_path)
        else:
            text = extract_pdf_text(file_path)

        # 2. Extract data
        data = extract_invoice_data(text)

        # 3. Categorize
        category = categorize_expense(data.get('vendor', ''))

        # 4. Rename and move
        date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        new_name = f"{date_str}_{category}_{data.get('amount', 0):.2f}.pdf"
        new_path = os.path.join(self.output_dir, category, new_name)
        shutil.move(file_path, new_path)

        # 5. Add to database
        invoice = Invoice(
            id=None,
            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
            vendor=data.get('vendor', 'Unknown'),
            amount=data.get('amount', 0),
            category=category,
            description='',
            file_path=new_path
        )
        self.db.add_invoice(invoice)

def watch_inbox(inbox_dir: str, output_dir: str):
    """Watch inbox folder for new invoices"""
    db = InvoiceDatabase()
    handler = InvoiceHandler(db, output_dir)
    observer = Observer()
    observer.schedule(handler, inbox_dir, recursive=False)
    observer.start()

    print(f"Watching {inbox_dir} for new invoices...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

## Tips

1. **Scan immediately** - сканируй чеки сразу
2. **Consistent naming** - единый формат названий
3. **Backup** - храни копии в облаке
4. **Regular processing** - обрабатывай еженедельно
5. **Tax categories** - помечай налоговые вычеты
6. **Digital receipts** - настрой пересылку на email
7. **Annual archive** - архивируй по окончании года
