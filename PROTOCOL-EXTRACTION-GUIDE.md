# Protocol Extraction Guide - PDF to Structured Data

**Purpose**: Convert real winery protocols (PDFs) into structured JSON/CSV for database seeding  
**Priority Focus**: Pinot Noir, Chardonnay, Cabernet Sauvignon  
**Timeline**: 2-3 days for Priority 1

---

## 📋 What to Extract from Each Protocol

### Header Information
```json
{
  "protocol_metadata": {
    "varietal_name": "Pinot Noir",
    "varietal_code": "PN",
    "color": "RED",
    "winery": "R&G Wines",
    "vintage": 2021,
    "expected_duration_days": 20,
    "expected_temperature_celsius_min": 18,
    "expected_temperature_celsius_max": 22,
    "author": "Winemaker Name",
    "notes": "Sensitive to H2S, requires tight temperature control"
  }
}
```

### Step Information (Ordered)
For EACH step in the protocol, extract:

```json
{
  "step": {
    "step_order": 1,
    "step_type": "YEAST_INOCULATION",
    "expected_day": 0,
    "expected_time_range": "morning",
    "tolerance_hours": 12,
    "description": "Add prepared yeast culture to crushed fruit",
    
    "observations_to_record": [
      "Yeast strain used",
      "Yeast volume (ml or g)",
      "Temperature at inoculation",
      "Brix at crush"
    ],
    
    "decision_points": [
      {
        "if": "Temperature above 25°C",
        "then": "Cool tank before inoculation"
      }
    ],
    
    "is_critical": true,
    "criticality_notes": "Sets fermentation trajectory",
    "h2s_risk_level": "LOW",
    "frequency": "ONCE",
    
    "next_step_trigger": "Fermentation becomes active (24-48 hours)"
  }
}
```

### Key Parameters to Capture

#### Temperature Management
```json
{
  "temperature_protocol": {
    "optimal_range": {
      "min_celsius": 18,
      "max_celsius": 22,
      "preferred_celsius": 20
    },
    "check_frequency": "daily",
    "cooling_available": true,
    "heating_available": false,
    "alarm_thresholds": {
      "too_cold": 16,
      "too_hot": 25,
      "action": "MANUAL_ADJUSTMENT"
    }
  }
}
```

#### H2S Monitoring
```json
{
  "h2s_protocol": {
    "check_frequency": "daily",
    "start_monitoring_day": 1,
    "stop_monitoring_day": 15,
    "severity_levels": [
      {
        "level": "NONE",
        "odor": "Normal fermentation smell",
        "action": "Continue protocol"
      },
      {
        "level": "LIGHT",
        "odor": "Faint rotten-egg smell",
        "action": "Increase aeration, add DAP"
      },
      {
        "level": "STRONG",
        "odor": "Distinct rotten-egg smell",
        "action": "ESCALATE - Punch down immediately, add nutrient"
      }
    ]
  }
}
```

#### Brix (Sugar) Monitoring
```json
{
  "brix_milestones": [
    {
      "milestone": "START",
      "expected_day": 0,
      "expected_brix": 24,
      "tolerance": 1.0
    },
    {
      "milestone": "1/3_DEPLETION",
      "expected_day": 4,
      "expected_brix": 16,
      "tolerance": 1.5,
      "action": "Add DAP/nutrients"
    },
    {
      "milestone": "2/3_DEPLETION",
      "expected_day": 10,
      "expected_brix": 8,
      "tolerance": 1.5,
      "action": "Monitor for completion"
    },
    {
      "milestone": "DRY",
      "expected_day": 18,
      "expected_brix": 0,
      "tolerance": 0.5,
      "action": "Press, move to secondary"
    }
  ]
}
```

#### Punch-Down Schedule (Reds Only)
```json
{
  "punch_down_protocol": {
    "frequency": "daily",
    "start_day": 1,
    "end_day": 15,
    "time_of_day": "morning",
    "depth": "75%",
    "intensity": "vigorous",
    "purpose": "Release CO2, redistribute yeast, cool tank",
    "notes": "For Pinot Noir: gentle to avoid tannin over-extraction"
  }
}
```

#### Nutrient Additions
```json
{
  "nutrient_protocol": {
    "additions": [
      {
        "day": 0,
        "nutrient_type": "YEAST_NUTRIENT",
        "amount": "10g/100L",
        "timing": "At inoculation",
        "purpose": "Support yeast health"
      },
      {
        "day": 3,
        "nutrient_type": "DAP",
        "amount": "15g/100L",
        "timing": "At 1/3 sugar depletion",
        "purpose": "Prevent H2S"
      }
    ]
  }
}
```

---

## 🎯 Priority 1: Extract These Steps

### For PINOT NOIR:
**Files**: R&G Pinot Noir 2021.pdf (744 KB)  
**Expected Steps**: 15-20 steps over 20 days

Focus areas:
- [ ] Daily H2S monitoring schedule (critical for Pinot)
- [ ] Temperature control regimen (tight 18-22°C window)
- [ ] Punch-down timing and intensity (gentle for Pinot)
- [ ] DAP additions (likely on days 3-4 and 7)
- [ ] Pressing decision criteria (day 18-22)
- [ ] MLF follow-up notes (if applicable)

### For CHARDONNAY:
**Files**: R&G Chardonnay 2021.pdf (555 KB)  
**Expected Steps**: 12-16 steps over 16 days

Focus areas:
- [ ] Cold settling procedure (white wine specific)
- [ ] Temperature monitoring (14-18°C range)
- [ ] SO2 addition timing and amounts
- [ ] Racking schedule (whites have different schedules than reds)
- [ ] MLF decision points (important for Chardonnay)
- [ ] Clarification/filtering steps

### For CABERNET SAUVIGNON:
**Files**: R&G Cabernet Sauvignon 2021.pdf (783 KB)  
**Expected Steps**: 18-24 steps over 30 days

Focus areas:
- [ ] Extended maceration notes (28-30 days typical)
- [ ] Punch-down frequency (possibly twice-daily for extended extraction)
- [ ] H2S monitoring (moderate risk, daily checks)
- [ ] Temperature range (warmer: 24-28°C)
- [ ] Multiple DAP additions (days 3, 7, maybe 10)
- [ ] Pressing decision (later than Pinot: day 25-30)

---

## 📊 Template for Structured Output

### CSV Format (Simple)

```csv
protocol_id,step_order,step_type,expected_day,tolerance_hours,description,is_critical,criticality_score,h2s_risk,frequency
PN_2021,1,YEAST_INOCULATION,0,12,"Add yeast culture to crushed fruit",true,2.0,LOW,ONCE
PN_2021,2,H2S_CHECK,1,6,"Monitor for H2S smell - sniff tank",true,2.0,HIGH,DAILY
PN_2021,3,TEMPERATURE_CHECK,1,6,"Check tank temperature",true,2.0,CRITICAL,DAILY
PN_2021,4,PUNCH_DOWN,1,8,"Punch down cap - gentle for Pinot",true,1.2,MEDIUM,DAILY
PN_2021,5,DAP_ADDITION,3,12,"Add DAP at 1/3 sugar depletion (~16 Brix)",true,1.5,MEDIUM,ONCE
...
```

### JSON Format (Comprehensive)

```json
{
  "protocol": {
    "varietal": "Pinot Noir",
    "code": "PN",
    "color": "RED",
    "vintage": 2021,
    "expected_duration_days": 20,
    "winery": "R&G Wines",
    "steps": [
      {
        "step_order": 1,
        "step_type": "YEAST_INOCULATION",
        "expected_day": 0,
        "tolerance_hours": 12,
        "description": "Add prepared yeast culture to crushed fruit",
        "is_critical": true,
        "criticality_score": 2.0,
        "observations": ["Yeast strain", "Volume", "Temperature"],
        "h2s_risk": "LOW",
        "frequency": "ONCE"
      },
      {
        "step_order": 2,
        "step_type": "H2S_CHECK",
        "expected_day": 1,
        "tolerance_hours": 6,
        "description": "Monitor for H2S smell by sniffing tank",
        "is_critical": true,
        "criticality_score": 2.0,
        "observations": ["H2S level (NONE/LIGHT/STRONG)", "Temperature"],
        "h2s_risk": "HIGH",
        "frequency": "DAILY",
        "decision_points": [
          {
            "if": "H2S detected",
            "then": "Add aeration via punch-down"
          }
        ]
      }
    ]
  }
}
```

---

## 🛠️ Extraction Tools

### Option 1: Adobe Acrobat (Professional)
**Pros**: Exact extraction, preserves formatting, table recognition  
**Cons**: Requires Adobe subscription  
**Steps**:
1. Open PDF in Adobe Acrobat
2. Use "Export PDF" → "Spreadsheet (Excel)"
3. Review for accuracy
4. Save as CSV/Excel

### Option 2: Online Converter (Fast)
**Pros**: Free, no installation, quick  
**Cons**: May lose some formatting  
**Steps**:
1. Visit ILovePDF.com or SmallPDF.com
2. Upload PDF
3. Select "PDF to Excel" or "PDF to CSV"
4. Download result
5. Clean up formatting

### Option 3: Python Script (Automated)
**Pros**: Can handle all 16 PDFs at once  
**Cons**: Need to handle parsing variations  
**Tool**: pdfplumber library
**Estimated Time**: 2-3 hours to write, 1 hour to run

---

## ✅ Validation Checklist

After extracting each protocol, verify:

- [ ] **Completeness**: All steps captured from "Day 0" to "Fermentation Complete"
- [ ] **Sequence**: Steps are in logical order by day
- [ ] **Timing**: Expected days and tolerance windows are specific (not vague)
- [ ] **Criticality**: Critical vs optional steps clearly marked
- [ ] **Parameters**: Temperature ranges, H2S checks, Brix milestones captured
- [ ] **Decisions**: Decision trees ("If X, then Y") captured
- [ ] **Frequency**: How often each step (ONCE, DAILY, AS_NEEDED)
- [ ] **Duration**: Total fermentation time matches expected
- [ ] **Metadata**: Winery, vintage, author clearly identified
- [ ] **Notes**: Varietal-specific quirks and special instructions captured

---

## 📝 Example: Pinot Noir Steps (Template)

```
DAY 0 - CRUSH & INOCULATION
├─ Step 1: YEAST_INOCULATION
│  Time: Morning
│  Tolerance: ±12 hours
│  Critical: YES (2.0 score)
│  Observe: Yeast strain, volume, temp
│  Action: Add prepared yeast to crushed fruit
│  Next trigger: Fermentation becomes active

DAY 1 - ACTIVE FERMENTATION START
├─ Step 2: H2S_CHECK
│  Time: Morning
│  Tolerance: ±6 hours
│  Critical: YES (2.0 score)
│  Observe: H2S odor, temperature
│  Frequency: DAILY until completion
│  Decision: If detected → escalate punch-down

├─ Step 3: TEMPERATURE_CHECK
│  Time: Morning (+ afternoon check)
│  Tolerance: ±6 hours
│  Critical: YES (2.0 score)
│  Observe: Tank temperature, ambient temp
│  Frequency: DAILY (twice-daily if warm)
│  Decision: If >22°C → cool tank

├─ Step 4: PUNCH_DOWN
│  Time: Morning
│  Tolerance: ±8 hours
│  Critical: YES (1.2 score)
│  Observe: Cap condition, temperature change
│  Frequency: DAILY
│  Intensity: GENTLE (Pinot-specific)

DAY 3 - 1/3 SUGAR DEPLETION
├─ Step 5: BRIX_CHECK
│  Time: Morning
│  Target: 16 Brix (±1.5)
│  Critical: YES (1.0 score)
│  Observe: Precise Brix reading
│  Decision: Confirm approaching 1/3 depletion

├─ Step 6: DAP_ADDITION
│  Time: Morning
│  Amount: 15g/100L
│  Critical: YES (1.5 score)
│  Observe: Full dissolution, no agglomeration
│  Timing: At confirmed 1/3 depletion
│  Purpose: Prevent H2S

... (continues through Day 20)

DAY 18 - DRY FERMENTATION COMPLETE
├─ Step 15: BRIX_CHECK_FINAL
│  Time: Morning
│  Target: 0 Brix (±0.5)
│  Critical: YES (2.0 score)
│  Observe: Precise final reading

├─ Step 16: TASTE/SMELL_CHECK
│  Time: After Brix check
│  Critical: YES (1.5 score)
│  Observe: Dry? Any off-odors?
│  Decision: Ready to press?

├─ Step 17: PRESSING
│  Time: Morning
│  Critical: YES (1.8 score)
│  Observe: Press operation, flow rate
│  Decision: Press all or leave some?
│  Purpose: Separate wine from pomace
```

---

## 🚀 Getting Started

### Week 1 Actions:

**Monday-Tuesday**:
- [ ] Download all 3 Priority files (Pinot, Chardonnay, Cabernet)
- [ ] Choose extraction tool (Acrobat easiest, online converter quickest)
- [ ] Extract to Excel/CSV

**Wednesday-Thursday**:
- [ ] Create JSON structure for each protocol
- [ ] Fill in all steps (ordered by day)
- [ ] Map to ADR-035 data model

**Friday**:
- [ ] Validate extraction (all steps present, reasonable timing)
- [ ] Create database seed script
- [ ] Ready for Week 2: Load into database

---

## 💾 Final Format Expected

By end of extraction:

```
protocols/
├─ pinot_noir_2021.json        (150-200 lines)
├─ chardonnay_2021.json        (120-150 lines)
├─ cabernet_sauvignon_2021.json (200-250 lines)
├─ pinot_noir_2021.csv         (30-40 rows)
├─ chardonnay_2021.csv         (20-30 rows)
└─ cabernet_sauvignon_2021.csv  (40-50 rows)
```

Ready to load into ADR-035 schema. 🍷

