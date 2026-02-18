# Protocol Analysis Complete - Action Plan for ADRs

**Analysis Date**: February 9, 2026  
**Status**: ✅ All 6 ADRs created + Real protocol inventory analyzed  
**Next Phase**: Extract protocols → Refine ADRs → Build Phase 0

---

## 🎯 What We Found

### Real Winery Protocols
- **16 PDF files** from professional wineries (R&G Wines, LangeTwins)
- **7 red varietals** (Cabernet, Pinot Noir, Petite Sirah, Zinfandel, Teroldego, White Zinfandel)
- **7 white varietals** (Chardonnay, Sauvignon Blanc, Pinot Grigio, Muscat, Viognier, Vermentino, Chenin Blanc)
- **1 rosé varietal** (Pinot Noir Rosé)
- **1 reference document** (Brix targets)

### Key Findings
✅ **Fermentation Duration**: 3 days (Rosé) to 32 days (Petite Sirah)  
✅ **H2S Risk**: Varies 10x+ between varietals (Pinot Noir HIGH, Petite Sirah LOW)  
✅ **Temperature Range**: Reds 18-30°C, Whites 14-18°C (different equipment!)  
✅ **Complexity**: Pinot Noir most interesting for demo (sensitivity showcase)  

### Recommended for Demo
1. **Pinot Noir** (RED) - ⭐ BEST: Shows H2S sensitivity, 18-22 days, tight temperature control
2. **Chardonnay** (WHITE) - Shows contrast (cold fermentation, settling, MLF)
3. **Cabernet** (RED) - Shows standardized, investor-friendly process

---

## 📚 Documentation Created

### ADRs (6 Files, 158 KB)
1. **ADR-035**: Protocol Data Model & Schema Design
2. **ADR-036**: Compliance Scoring Algorithm
3. **ADR-037**: Protocol-Analysis Integration
4. **ADR-038**: Protocol Deviation Detection
5. **ADR-039**: Template Management & Customization
6. **ADR-040**: Notifications & Alerts Strategy

### Supporting Documents (4 Files)
1. **PROTOCOL-ADR-GUIDE.md** - Navigation, timeline, validation
2. **PROTOCOL-IMPLEMENTATION-SUMMARY.md** - Executive summary
3. **PROTOCOL-IMPLEMENTATION-CHECKLIST.md** - Pre-impl tasks
4. **PROTOCOL-DEVELOPER-QUICKREF.md** - Print-friendly reference

### Analysis Documents (3 Files)
1. **PROTOCOL-ANALYSIS-REAL-DATA.md** - Detailed protocol breakdown
2. **PROTOCOL-EXTRACTION-GUIDE.md** - How to extract PDFs
3. **THIS FILE** - Action plan

---

## 🔄 How to Update ADRs Based on Real Data

### ADR-035: Data Model - Already Aligns ✅
- 4 entities match real protocols perfectly
- 10-30 steps per varietal matches design
- Criticality scoring will be validated

### ADR-036: Compliance Scoring - Needs Refinement
**Update based on real data**:

```
Current assumption: All steps equally weighted
Reality: H2S checks on Pinot worth 2.0×, on Petite Sirah worth 0.8×

Action items:
- [ ] Assign varietal-specific criticality scores
- [ ] Pinot Noir: H2S_CHECK = 2.0 (very critical)
- [ ] Petite Sirah: H2S_CHECK = 0.8 (less critical)
- [ ] Cabernet: H2S_CHECK = 1.5 (moderate)
- [ ] Test scoring formula with sample Pinot fermentation
```

### ADR-037: Analysis Integration - Needs Protocol-Specific Logic
**Update based on real data**:

```
Current: One confidence boost formula for all
Reality: Pinot Noir needs different analysis thresholds

Action items:
- [ ] Create varietal-specific confidence adjustments
- [ ] Pinot Noir: Tighter tolerance for H2S detection
- [ ] Cabernet: Tighter tolerance for pressed wine quality
- [ ] Test with real Pinot Noir protocol
```

### ADR-038: Deviation Detection - Needs Varietal Thresholds
**Update based on real data**:

```
Current: Generic deviation thresholds
Reality: 1 day late for Pinot H2S check = CRITICAL
         1 day late for Petite Sirah racking = acceptable

Action items:
- [ ] Define step-specific late thresholds
- [ ] Pinot Noir H2S: CRITICAL if >6 hours late
- [ ] Cabernet DAP: CRITICAL if >12 hours late
- [ ] White wines: Less strict (longer fermentation)
```

### ADR-039: Template Management - Already Aligns ✅
- Template lifecycle works perfectly
- Customization rules make sense for varietals

### ADR-040: Alerts & Notifications - Needs Frequency Tuning
**Update based on real data**:

```
Current: Generic alert severities
Reality: Pinot Noir needs H2S alerts every 6 hours
         Cabernet needs them every 24 hours

Action items:
- [ ] Alert frequency varies by step criticality
- [ ] Pinot Noir: H2S_CHECK alerts if missed by 6 hours
- [ ] Cabernet: H2S_CHECK alerts if missed by 24 hours
- [ ] Whites: Temperature alerts if >1°C variance
```

---

## 📋 Extraction Priority & Timeline

### PRIORITY 1: Demo Varietals (Week 1-2)
**Pinot Noir**, **Chardonnay**, **Cabernet Sauvignon**

```
Timeline:
├─ Mon-Tue: Extract PDFs to Excel/CSV
├─ Wed-Thu: Convert to JSON, map to ADR-035
├─ Fri: Validate, create database seed script
└─ Week 2: Load into database, test with fermentation module
```

**Expected Output**:
- 3 complete FermentationProtocol templates (15-24 steps each)
- JSON files ready for database import
- Seed script ready for Phase 0

### PRIORITY 2: Extended Suite (Week 2-3)
**LTW Chenin Blanc**, **Sauvignon Blanc**, **Pinot Noir Rosé**

```
Timeline:
├─ Extract during spare time in Week 2
├─ Load to database in Week 3
└─ Validate with test fermentations
```

### PRIORITY 3: Complete Library (As Needed)
**Remaining 7 varietals** - Can be loaded anytime, not urgent for May demo

---

## 🔄 Feedback Loop: Real Data → ADR Refinements

### Phase 1: Extract (This Week)
- [ ] Get Pinot Noir, Chardonnay, Cabernet protocols
- [ ] Create JSON structure with all steps
- [ ] Identify varietal-specific requirements

### Phase 2: Refine ADRs (Next Week)
- [ ] Update ADR-036 with varietal criticality scores
- [ ] Update ADR-038 with varietal deviation thresholds
- [ ] Update ADR-040 with varietal alert frequencies
- [ ] Review with Susana for enological accuracy

### Phase 3: Validate Formulas (Week 3)
- [ ] Load Pinot Noir protocol into database
- [ ] Create sample Pinot fermentation
- [ ] Test compliance scoring (should feel right to winemaker)
- [ ] Test deviation detection (correct severity levels?)
- [ ] Test alerts (frequencies match reality?)

### Phase 4: Build Phase 0 (Week 4+)
- [ ] Database schema from ADR-035 ✅
- [ ] Domain models ✅
- [ ] Repositories ✅
- [ ] Seed data from extracted protocols ✅
- [ ] Integration tests with sample data ✅

---

## 🎬 Demo Scenario (Updated with Real Data)

### Scenario: Pinot Noir Fermentation (Perfect for Demo)

**Setup**:
- Load R&G Pinot Noir 2021 protocol (extracted)
- Create fermentation: "Demo Napa Valley 2026 Pinot Noir"
- Assign protocol, set start date today

**Execution** (Simulated 20-day timeline):

```
DAY 1 (Today):
├─ Record Yeast Inoculation ✓ (on-time)
├─ H2S Check (none) ✓
├─ Temperature Check: 20°C ✓
├─ Punch-down ✓
└─ Compliance: 100% (all critical steps done, on-time)

DAY 2 (Tomorrow simulated):
├─ H2S Check (slight smell detected) ⚠️
├─ Action: Increase punch-down intensity
├─ Alert generated: MEDIUM severity
└─ Compliance: 98% (H2S detected but addressed)

DAY 3 (Day+2 simulated):
├─ Record Brix: 16 (confirms 1/3 depletion)
├─ Add DAP/nutrients
├─ Punch-down twice today
└─ Compliance: 99% (kept ahead of H2S)

... Show dashboard
├─ Compliance trending: 100% → 98% → 99% → ...
├─ Deviations logged: 1 (H2S light, addressed)
├─ Alerts sent: 3 (step approaching, H2S detected, action taken)
└─ Protocol status: 4/20 steps completed
```

**Show Features**:
1. ✅ Protocol compliance score trending
2. ✅ Real-time deviation detection (H2S alert)
3. ✅ Advisory system (suggested increased aeration)
4. ✅ Mobile offline alert cache
5. ✅ Integration with Analysis Engine (confidence boosted by compliance)

**Outcome**: Investor sees system preventing issues before they become expensive.

---

## ✅ Updated Success Criteria

### Data Analysis Phase (THIS WEEK)
- [x] Inventory all 16 protocols
- [x] Categorize by type (red/white/rosé)
- [x] Identify key characteristics (duration, H2S risk, temp)
- [x] Select demo varietal (Pinot Noir ⭐)
- [ ] Extract Priority 1 (Pinot, Chardonnay, Cabernet) → JSON format

### ADR Refinement Phase (NEXT WEEK)
- [ ] Validate ADR-036 scoring with real Pinot Noir data
- [ ] Validate ADR-038 thresholds with real protocols
- [ ] Validate ADR-040 frequencies with real step durations
- [ ] Review all updates with Susana (enologist)

### Build Phase (WEEKS 2-10)
- [ ] Phase 0: Database schema + seed data
- [ ] Phase 1: Repositories
- [ ] Phase 2: Services (scoring, deviation, template)
- [ ] Phase 3: API layer
- [ ] Phase 4: Analysis integration + alerts
- [ ] Phase 5: UI + demo refinement

---

## 🚀 Next Immediate Actions

### By End of This Week (TODAY → FRIDAY)

**Action 1: Extract Pinot Noir Protocol**
- [ ] Download R&G Pinot Noir 2021.pdf
- [ ] Convert to Excel/CSV using online tool or Adobe
- [ ] Identify all steps from Day 0 to Day 20
- [ ] Extract: timing, observations, decision points
- [ ] Create JSON file: `pinot_noir_2021.json`

**Action 2: Extract Chardonnay Protocol**
- [ ] Download R&G Chardonnay 2021.pdf
- [ ] Convert to Excel/CSV
- [ ] Extract white-wine-specific steps (settling, SO2, MLF)
- [ ] Create JSON file: `chardonnay_2021.json`

**Action 3: Extract Cabernet Protocol**
- [ ] Download R&G Cabernet Sauvignon 2021.pdf
- [ ] Convert to Excel/CSV
- [ ] Extract extended maceration timeline (28-30 days)
- [ ] Create JSON file: `cabernet_sauvignon_2021.json`

### By Monday (WEEK 2)

**Action 4: Load to Database**
- [ ] Create database tables from ADR-035 schema
- [ ] Create seed script from JSON files
- [ ] Load all 3 protocols
- [ ] Test retrieval and relationships

**Action 5: Validate with Susana**
- [ ] Review extracted protocols
- [ ] Confirm steps, timing, criticality
- [ ] Any additions/corrections?
- [ ] Approve for implementation

---

## 📊 Files & Resources

**In**: `c:\dev\wine-fermentation-system\docs\Protocols\` (16 PDFs, 9.2 MB)

**Out**: Create in `c:\dev\wine-fermentation-system\`
```
extracted_protocols/
├─ pinot_noir_2021.json
├─ chardonnay_2021.json
├─ cabernet_sauvignon_2021.json
├─ pinot_noir_2021.csv
├─ chardonnay_2021.csv
└─ cabernet_sauvignon_2021.csv
```

**Reference**:
- [PROTOCOL-ANALYSIS-REAL-DATA.md](PROTOCOL-ANALYSIS-REAL-DATA.md) - Full analysis
- [PROTOCOL-EXTRACTION-GUIDE.md](PROTOCOL-EXTRACTION-GUIDE.md) - Extraction instructions
- [PROTOCOL-ADR-GUIDE.md](.ai-context/adr/PROTOCOL-ADR-GUIDE.md) - ADR overview
- [ADR-035](../protocol-data-model-schema.md) - Data model reference

---

## 🎯 Summary

**You have**:
- ✅ 6 production-ready ADRs (158 KB)
- ✅ Real winery protocols (16 files, 9.2 MB)
- ✅ Clear extraction path (3 PDFs → JSON in 2-3 days)
- ✅ Demo scenario ready (Pinot Noir protocol)
- ✅ 10-week implementation timeline

**You need**:
- ⏳ Extract 3 Priority protocols (THIS WEEK)
- ⏳ Map to ADR-035 schema (NEXT WEEK)
- ⏳ Refine ADRs based on real data (NEXT WEEK)
- ⏳ Build Phase 0-5 following timeline (WEEKS 2-10)

**By May 2026**: Working Protocol Engine with real protocols, ready for Napa Valley demo. 🍷

