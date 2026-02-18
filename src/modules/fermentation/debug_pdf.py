#!/usr/bin/env python3
"""Debug script to inspect PDF table structure"""

import pdfplumber
from pathlib import Path

PROTOCOLS_DIR = Path(__file__).parent.parent.parent.parent / "docs" / "Protocols"
pdf_path = PROTOCOLS_DIR / "R&G Pinot Noir 2021.pdf"

print(f"Opening: {pdf_path}")
print("=" * 60)

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}\n")
    
    for page_num, page in enumerate(pdf.pages, 1):
        print(f"\n📄 PAGE {page_num}")
        print("-" * 60)
        
        # Show text preview
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            print("TEXT CONTENT (first 30 lines):")
            for i, line in enumerate(lines[:30], 1):
                if line.strip():
                    print(f"  {i:2}. {line[:80]}")
        
        # Show tables
        tables = page.extract_tables()
        if tables:
            print(f"\nTABLES FOUND: {len(tables)}")
            for table_num, table in enumerate(tables, 1):
                print(f"\nTable {table_num}: {len(table)} rows × {len(table[0])} cols")
                print("Header row:")
                for col_num, cell in enumerate(table[0], 1):
                    print(f"  Col {col_num}: {str(cell)[:60]}")
                print("\nSample data rows (first 3):")
                for row_num, row in enumerate(table[1:4], 1):
                    print(f"  Row {row_num}: {row}")
