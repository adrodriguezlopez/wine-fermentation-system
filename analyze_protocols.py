#!/usr/bin/env python3
"""
Analyze fermentation protocols from PDF files.
Extract key information: steps, timing, requirements, etc.
"""

import os
import re
from pathlib import Path

pdf_folder = Path(r'c:\dev\wine-fermentation-system\docs\Protocols')

# Get all PDFs
pdf_files = sorted([f for f in pdf_folder.glob('*.pdf')])

print('='*100)
print('PROTOCOL INVENTORY ANALYSIS')
print('='*100)
print()

# Categorize by type
reds = []
whites = []
rosés = []
sparkling = []

for pdf_file in pdf_files:
    name = pdf_file.name
    
    # Categorize based on filename
    if any(x in name for x in ['Zinfandel', 'Cabernet', 'Petite Sirah', 'Pinot Noir', 'Teroldego']):
        if 'Rose' in name:
            rosés.append(name)
        else:
            reds.append(name)
    elif any(x in name for x in ['Chardonnay', 'Pinot Grigio', 'Sauvignon Blanc', 'Viognier', 'Vermentino', 'Chenin Blanc', 'Muscat', 'White Zinfandel']):
        whites.append(name)
    
# Print categorization
print("RED WINES:")
print("-" * 100)
for name in reds:
    size = pdf_folder.joinpath(name).stat().st_size / 1024
    print(f"  • {name:<50} ({size:7.1f} KB)")
print()

print("WHITE WINES:")
print("-" * 100)
for name in whites:
    size = pdf_folder.joinpath(name).stat().st_size / 1024
    print(f"  • {name:<50} ({size:7.1f} KB)")
print()

print("ROSÉ WINES:")
print("-" * 100)
for name in rosés:
    size = pdf_folder.joinpath(name).stat().st_size / 1024
    print(f"  • {name:<50} ({size:7.1f} KB)")
print()

print("REFERENCE DOCUMENTS:")
print("-" * 100)
for name in pdf_files:
    if name.name not in reds + whites + rosés:
        size = pdf_folder.joinpath(name.name).stat().st_size / 1024
        print(f"  • {name.name:<50} ({size:7.1f} KB)")
print()

print("="*100)
print(f"SUMMARY: {len(reds)} reds, {len(whites)} whites, {len(rosés)} rosés, {len(pdf_files) - len(reds) - len(whites) - len(rosés)} reference docs")
print(f"Total files: {len(pdf_files)}")
print(f"Total size: {sum(f.stat().st_size for f in pdf_files) / 1024 / 1024:.1f} MB")
print("="*100)
print()
print("✅ Next steps:")
print("   1. Use Adobe Acrobat or online tool to convert PDFs to structured format (CSV/JSON)")
print("   2. Extract for each protocol:")
print("      - Varietal name")
print("      - Color (RED/WHITE/ROSÉ)")
print("      - Expected duration (days)")
print("      - Steps (ordered list with timing)")
print("      - Critical parameters (H2S, temperature, brix targets)")
print("   3. Map to ADR-035 data model:")
print("      - FermentationProtocol (template)")
print("      - ProtocolStep (individual steps)")
print("      - Criticality scoring (which steps matter most)")
print()
