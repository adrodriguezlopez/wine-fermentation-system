#!/usr/bin/env python3
"""
Automated Protocol Extraction from PDFs

Extracts fermentation protocol steps from Napa Valley winery PDFs
and converts them to JSON/CSV format ready for database loading.

Supports: R&G Wines, LangeTwins protocols
"""

import json
import csv
import pdfplumber
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Protocol directory (relative to project root)
PROTOCOLS_DIR = Path(__file__).parent.parent.parent.parent / "docs" / "Protocols"
OUTPUT_DIR = Path(__file__).parent / "extracted_protocols"

# Priority protocols to extract
PRIORITY_PROTOCOLS = [
    "R&G Pinot Noir 2021.pdf",
    "R&G Chardonnay 2021.pdf",
    "R&G Cabernet Sauvignon 2021.pdf",
]

# Step type patterns to detect from text (Feb 10, 2026: Updated to use StepType categories)
# Maps detected text patterns to new category-based StepType enum values
STEP_PATTERNS = {
    # INITIALIZATION steps
    "INITIALIZATION": [
        r"inocul", r"pitch", r"yeast", r"starter",  # YEAST_INOCULATION
        r"cold.*soak", r"pre-soak"                   # COLD_SOAK
    ],
    
    # MONITORING steps
    "MONITORING": [
        r"temperatur", r"temp\b", r"cool", r"ferment.*temp",  # TEMPERATURE_CHECK
        r"h2s", r"hydrogen sulfide", r"smell", r"rotten egg",  # H2S_CHECK
        r"brix", r"sugar", r"density", r"sg\b", r"gravity"     # BRIX_READING
    ],
    
    # ADDITIONS steps
    "ADDITIONS": [
        r"dap\b", r"diammon", r"nutrient.*addition",           # DAP_ADDITION
        r"nutrient", r"yeast nutrient", r"feeding",            # NUTRIENT_ADDITION
        r"so2\b", r"sulfite", r"sulfur",                       # SO2_ADDITION
        r"mlf\b", r"malo.*lactic", r"malolactic"               # MLF_INOCULATION
    ],
    
    # CAP_MANAGEMENT steps
    "CAP_MANAGEMENT": [
        r"punch.*down", r"punchdown", r"cap\s+management",    # PUNCH_DOWN
        r"pump.*over", r"pumpover", r"recircul"               # PUMP_OVER
    ],
    
    # POST_FERMENTATION steps
    "POST_FERMENTATION": [
        r"press", r"dry(?:ing)?",                             # PRESSING
        r"rack", r"transfer", r"clarif"                       # RACKING
    ],
    
    # QUALITY_CHECK steps
    "QUALITY_CHECK": [
        r"inspect", r"observe", r"check.*appearance",         # VISUAL_INSPECTION
        r"tast", r"flavor"                                     # CATA_TASTING
    ],
}

class ProtocolExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.protocol_name = self.pdf_path.stem
        self.text = ""
        self.tables = []
        
    def extract_text(self) -> str:
        """Extract all text from PDF"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
                self.text = "\n".join(text_parts)
                return self.text
        except Exception as e:
            print(f"❌ Error extracting text from {self.pdf_path}: {e}")
            return ""
    
    def extract_tables(self) -> List[List[Dict]]:
        """Extract all tables from PDF"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                all_tables = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)
                self.tables = all_tables
                return all_tables
        except Exception as e:
            print(f"⚠️  Error extracting tables from {self.pdf_path}: {e}")
            return []
    
    def parse_day_number(self, text: str) -> Optional[int]:
        """Extract day number from text like 'Day 0', 'Day 1-3', etc"""
        match = re.search(r'day\s+(\d+)', text.lower())
        if match:
            return int(match.group(1))
        return None
    
    def detect_step_type(self, text: str) -> Optional[str]:
        """Detect step type from text content"""
        text_lower = text.lower()
        for step_type, patterns in STEP_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return step_type
        return "VISUAL_INSPECTION"  # Default fallback
    
    def extract_steps_from_table(self) -> List[Dict]:
        """Extract protocol steps from table format"""
        steps = []
        step_order = 1
        
        for table in self.tables:
            # Tables usually have: [Day, Action/Task, Notes] format
            for row in table[1:]:  # Skip header row
                if len(row) >= 2:
                    day_text = row[0] or ""
                    action_text = row[1] or ""
                    notes = row[2] if len(row) > 2 else ""
                    
                    if not action_text.strip():
                        continue
                    
                    day = self.parse_day_number(day_text) or step_order
                    step_type = self.detect_step_type(action_text)
                    
                    step = {
                        "step_order": step_order,
                        "step_type": step_type,
                        "description": action_text.strip(),
                        "expected_day": day,
                        "tolerance_hours": 6,  # Default 6 hour tolerance
                        "is_critical": self._is_critical(step_type),
                        "notes": notes.strip() if notes else "",
                    }
                    steps.append(step)
                    step_order += 1
        
        return steps
    
    def extract_steps_from_text(self) -> List[Dict]:
        """Extract protocol steps from free-form text"""
        steps = []
        step_order = 1
        
        # Split by day markers
        day_pattern = r'day\s+(\d+)[:\s]+(.*?)(?=day\s+\d+|$)'
        matches = re.finditer(day_pattern, self.text.lower(), re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            day = int(match.group(1))
            day_content = match.group(2)
            
            # Split tasks within day
            tasks = re.split(r'\n\d+\.\s+|\n[•-]\s+', day_content)
            
            for task in tasks:
                task = task.strip()
                if len(task) > 10:  # Only significant tasks
                    step_type = self.detect_step_type(task)
                    step = {
                        "step_order": step_order,
                        "step_type": step_type,
                        "description": task[:200],  # First 200 chars
                        "expected_day": day,
                        "tolerance_hours": self._tolerance_for_step(step_type),
                        "is_critical": self._is_critical(step_type),
                        "notes": "",
                    }
                    steps.append(step)
                    step_order += 1
        
        return steps
    
    def _is_critical(self, step_type: str) -> bool:
        """Determine if step is critical to protocol (Feb 10, 2026: Updated for category-based types)"""
        # Most MONITORING and ADDITIONS steps are critical
        # CAP_MANAGEMENT is typically not critical
        critical_categories = {
            "INITIALIZATION",  # Yeast inoculation is critical
            "MONITORING",      # Temperature, H2S, Brix checks are critical
            "ADDITIONS",       # Nutrient additions are critical
            "POST_FERMENTATION"  # Pressing is critical
        }
        return step_type in critical_categories
    
    def _tolerance_for_step(self, step_type: str) -> int:
        """Get tolerance window for step type (Feb 10, 2026: Updated for category-based types)"""
        # Different categories have different tolerance windows
        tolerances = {
            "INITIALIZATION": 2,      # Very tight for yeast inoculation
            "MONITORING": 6,          # Moderate for checks
            "ADDITIONS": 4,           # Tight for nutrient additions
            "CAP_MANAGEMENT": 12,     # More flexible for punch down/pump over
            "POST_FERMENTATION": 12,  # Flexible for racking/settling
            "QUALITY_CHECK": 24,      # Very flexible for tasting
        }
        return tolerances.get(step_type, 12)  # Default 12 hours
    
    def extract_metadata(self) -> Dict:
        """Extract protocol metadata"""
        # Parse filename: "R&G Pinot Noir 2021.pdf" → winery, varietal, year
        parts = self.protocol_name.split()
        
        winery = parts[0]  # "R&G" or "LTW"
        varietal_name = " ".join(parts[1:-1])  # "Pinot Noir" or "Chardonnay"
        year = parts[-1]  # "2021" or "2024"
        
        # Determine color from text
        color = "RED"
        if any(x in varietal_name.lower() for x in ["chardonnay", "sauvignon", "grigio", "muscat", "viognier", "vermentino", "chenin", "blanc"]):
            color = "WHITE"
        if "rosé" in varietal_name.lower():
            color = "ROSÉ"
        
        # Varietal code (2-3 letters)
        code_map = {
            "Cabernet Sauvignon": "CS",
            "Pinot Noir": "PN",
            "Chardonnay": "CH",
            "Sauvignon Blanc": "SB",
            "Pinot Grigio": "PG",
            "Muscat Canelli": "MC",
            "Viognier": "VG",
            "Vermentino": "VM",
            "Chenin Blanc": "CNB",
            "Petite Sirah": "PS",
            "Zinfandel": "ZF",
            "Teroldego": "TG",
            "White Zinfandel": "WZ",
        }
        code = code_map.get(varietal_name, varietal_name[:2].upper())
        
        return {
            "winery": winery,
            "varietal_code": code,
            "varietal_name": varietal_name,
            "year": year,
            "color": color,
            "protocol_name": f"{code}-{year}-Standard",
            "version": "1.0",
        }
    
    def extract(self) -> Dict:
        """Complete extraction: text + tables + metadata"""
        print(f"\n📄 Extracting: {self.protocol_name}")
        
        # Extract all content
        self.extract_text()
        self.extract_tables()
        
        # Parse steps (prefer table format if available)
        if self.tables:
            print(f"   ✓ Found {len(self.tables)} table(s)")
            steps = self.extract_steps_from_table()
        else:
            print(f"   ✓ Parsing from text format")
            steps = self.extract_steps_from_text()
        
        # Get metadata
        metadata = self.extract_metadata()
        
        print(f"   ✓ Extracted {len(steps)} steps")
        print(f"   ✓ Protocol: {metadata['varietal_name']} ({metadata['color']})")
        
        return {
            "metadata": metadata,
            "steps": steps,
            "extracted_at": datetime.now().isoformat(),
            "source_pdf": self.protocol_name,
        }

class ProtocolWriter:
    """Write extracted protocols to JSON/CSV"""
    
    @staticmethod
    def write_json(data: Dict, output_path: Path):
        """Write to JSON format"""
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"   ✓ Saved: {output_path.name}")
    
    @staticmethod
    def write_csv(data: Dict, output_path: Path):
        """Write to CSV format (simple flat format)"""
        metadata = data['metadata']
        steps = data['steps']
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'varietal_name', 'varietal_code', 'color', 'protocol_name',
                'step_order', 'step_type', 'description', 'expected_day',
                'tolerance_hours', 'is_critical', 'notes'
            ])
            writer.writeheader()
            
            for step in steps:
                row = {**metadata, **step}
                writer.writerow(row)
        
        print(f"   ✓ Saved: {output_path.name}")

def main():
    """Extract priority protocols"""
    print("=" * 60)
    print("🍇 AUTOMATED PROTOCOL EXTRACTION")
    print("=" * 60)
    
    # Verify protocol directory exists
    if not PROTOCOLS_DIR.exists():
        print(f"❌ Protocol directory not found: {PROTOCOLS_DIR}")
        return []
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Extract each priority protocol
    results = []
    for protocol_file in PRIORITY_PROTOCOLS:
        pdf_path = PROTOCOLS_DIR / protocol_file
        
        if not pdf_path.exists():
            print(f"❌ Not found: {pdf_path}")
            continue
        
        try:
            # Extract
            extractor = ProtocolExtractor(pdf_path)
            extracted = extractor.extract()
            results.append(extracted)
            
            # Write outputs
            base_name = pdf_path.stem
            writer = ProtocolWriter()
            writer.write_json(extracted, OUTPUT_DIR / f"{base_name}.json")
            writer.write_csv(extracted, OUTPUT_DIR / f"{base_name}.csv")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Extraction complete: {len(results)} protocols extracted")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print("=" * 60)
    
    # List generated files
    if OUTPUT_DIR.exists():
        files = sorted(OUTPUT_DIR.glob("*"))
        for f in files:
            size_kb = f.stat().st_size / 1024
            print(f"   • {f.name} ({size_kb:.1f} KB)")
    
    return results

if __name__ == "__main__":
    main()
