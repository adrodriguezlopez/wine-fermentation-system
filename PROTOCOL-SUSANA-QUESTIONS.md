# Uncertainties for Susana (Enologist) - Protocol Implementation

**Date**: February 7, 2026  
**Purpose**: Validate assumptions before implementing Protocol Compliance Engine  
**Prepared for**: Susana Rodriguez Vasquez

---

## 1. CRITICAL UNCERTAINTIES (MUST RESOLVE BEFORE CODING)

### 1.1 Compliance Scoring Algorithm
**Current Assumption** (from ADR-023):
```
Base = (Completed Steps / Total Steps) × 100
Penalties:
  - Skipped critical step: -10%
  - Step late by 1-2 days: -5%
  - Step late by 3+ days: -15%
```

**Questions**:
1. **Is this scoring reasonable?** Does it match your intuition for "good compliance"?
2. **Should critical steps be weighted differently?** 
   - Example: H2S_CHECK skipped = -20% vs DAP_ADDITION skipped = -5%?
3. **What's "acceptable" compliance?** Is 80% acceptable? 70%? 90%?
4. **Time penalties**: Is ±2 days reasonable tolerance for ALL steps?
   - DAP_ADDITION: Maybe ±1 day (precise timing)?
   - H2S_CHECK: Maybe ±5 days (flexible)?

---

### 1.2 Critical Steps Definition
**Current Assumption**: Some steps are "critical" and skipping them has major penalties

**Questions**:
1. **Which steps are truly CRITICAL?** (affect final wine quality if skipped)
   - H2S_CHECK? YEAST_COUNT? DAP_ADDITION?
   - Which would you NEVER skip, even in emergency?
   
2. **Which steps are IMPORTANT but not critical?** (good to do, but not dire)
   - VISUAL_INSPECTION? CATA_TASTING?
   
3. **Which steps are OPTIONAL?** (depends on conditions)
   - SECOND_NUTRIENT_ADDITION? (Only if fermentation slow)

4. **Can criticality vary by varietal?**
   - Cabernet (darker, thicker skins): Different critical steps than Chardonnay?

---

### 1.3 Protocol Applicability
**Current Assumption**: One protocol per varietal, always applied

**Questions**:
1. **Do protocols change based on conditions?**
   - "Normal fermentation" protocol vs "Problem fermentation" protocol?
   - "Warm vintage" vs "Cool vintage"?
   
2. **Can a fermentation switch protocols mid-execution?**
   - Started with "Standard" but problems emerge → switch to "Intervention" protocol?
   
3. **Can protocols be paused/resumed?**
   - Fermentation gets stuck day 5 → pause protocol → resume when unstuck?

4. **What if fermentation finishes early?**
   - Protocol expects 30 days, finishes in 20 days
   - Remaining steps auto-complete or marked "N/A"?

---

### 1.4 Step Sequencing & Flexibility
**Current Assumption**: Steps must be done in order (1→2→3...)

**Questions**:
1. **Is step order mandatory?**
   - Can TEMPERATURE_CHECK be done before YEAST_COUNT?
   - Or must they follow exact sequence?

2. **Can multiple steps be done same day?**
   - "Day 5: Do PUNCHING_DOWN + TEMPERATURE_CHECK + H2S_CHECK all at once"?
   - Or each has separate "expected day"?

3. **Time windows**: How precise?
   - "Day 5" means Day 5 exactly? Or Day 4-6 (±1 day)?
   - Different windows per step?

---

### 1.5 Skip Legitimacy
**Current Assumption**: Steps can be skipped, but trigger penalties/alerts

**Questions**:
1. **When can a step be legitimately skipped?**
   - Fermentation died → skip remaining steps? (auto-mark as "N/A"?)
   - Equipment broke → skip VISUAL_INSPECTION?
   - Holiday/weekend → skip TEMPERATURE_CHECK?

2. **Who can authorize a skip?**
   - Winemaker can skip their own protocol?
   - Need Winery Admin approval for critical steps?
   - Need external review?

3. **Should there be "skip reasons"?**
   - System logs: "Step H2S_CHECK: SKIPPED - Fermentation stopped"
   - vs "Step H2S_CHECK: SKIPPED - (no reason)"

4. **Can a skipped step be "completed retroactively"?**
   - Missed DAP on day 3 → Add it on day 5 (late)?
   - Or is it forever missed?

---

## 2. HIGH-PRIORITY UNCERTAINTIES (NEEDED FOR PHASE 1-2)

### 2.1 Protocol Versions & Changes
**Current Assumption**: Protocol versioned (v1.0, v2.0) and changes tracked

**Questions**:
1. **How often do protocols change?**
   - Every year? Every 5 years? Ad-hoc when something works better?
   
2. **Can in-flight fermentations be affected by protocol changes?**
   - Fermentation A starts with Protocol v1.0
   - You release Protocol v2.0
   - Should Fermentation A stay on v1.0 or upgrade to v2.0?
   
3. **Historical comparison**: When comparing protocols, use original version or current?

4. **New winemakers**: Should they use latest protocol or let them choose version?

---

### 2.2 Notification & Alert Preferences
**Current Assumption**: Different alert types (reminder, overdue, critical)

**Questions**:
1. **What alerts would you WANT to receive?**
   - "Next step due tomorrow" (proactive)?
   - "Step is 1 day overdue" (warning)?
   - "Critical step skipped" (critical)?
   - "Fermentation finishing early" (advisory)?

2. **Notification frequency**: How often is too often?
   - Daily digest?
   - Real-time for critical only?
   - Weekly summary?

3. **Delivery method preference**?
   - In-app dashboard?
   - Email?
   - SMS (only critical)?

4. **Can alerts be customized per winery?**
   - Winery A wants all alerts
   - Winery B wants critical only

---

### 2.3 Historical Data & Templates
**Current Assumption**: Create default templates; wineries can customize

**Questions**:
1. **Do you have example protocols we should use as templates?**
   - "Cabernet Sauvignon - Standard 2026"?
   - "Chardonnay - Cool Vintage"?
   - "Emergency Recovery Protocol"?

2. **Can we use your handwritten protocols (paper/Excel) as reference?**

3. **How detailed should step descriptions be?**
   - "Add DAP" (simple)
   - "Add 1-2 lbs DAP per 1000 gal, monitor CO2 release" (detailed)?

4. **Should we build in "best practices" from your experience?**

---

## 3. MEDIUM-PRIORITY UNCERTAINTIES (FOR LATER PHASES)

### 3.1 Analysis Engine Integration
**Current Assumption** (ADR-024): Compliance score affects anomaly detection confidence

**Questions**:
1. **Does low compliance actually predict problems?**
   - If winemaker skips H2S_CHECK, does VA risk increase?
   - Should system WARN user or just lower confidence?

2. **Which skipped steps correlate with which anomalies?**
   - Skipped H2S_CHECK → Flag for H2S/VA risk
   - Skipped TEMPERATURE_CHECK → Flag for temperature issues
   - Mapping needed

3. **Should compliance score reduce confidence?**
   - Compliance 85% → Reduce anomaly confidence by 15%?
   - Or different formula?

4. **Can protocol data improve recommendations?**
   - "Step X was skipped" → Recommend "Complete step X now"?

---

### 3.2 User Adoption & Training
**Current Assumption**: Winemakers will use the system

**Questions**:
1. **What would make this system useful to you?**
   - Reminder/checklist?
   - Compliance tracking for audits?
   - Learning what works best?

2. **What would make it annoying/unused?**
   - Too many notifications?
   - Too complex to log steps?
   - Too prescriptive (doesn't trust your judgment)?

3. **How much training/adoption time needed?**
   - Can learn in 1 hour?
   - Needs 1 week of hands-on?

4. **Should system suggest next step or just remind?**
   - "Next step: H2S check (recommended for tomorrow)"?
   - Or just a checkbox list?

---

### 3.3 Compliance vs Quality Correlation
**Current Assumption**: Better compliance → Better wine quality

**Questions**:
1. **Can you think of fermentations with:**
   - High compliance, high quality? (what made it work?)
   - Low compliance, high quality? (luck/skill override protocol?)
   - High compliance, poor quality? (protocol was wrong?)
   - Low compliance, poor quality? (protocol would have helped?)

2. **How much does protocol matter vs:**
   - Grape quality?
   - Weather during harvest?
   - Winemaker's intuition/experience?

3. **Can you share data on:**
   - "Best" fermentations (compliance + quality metrics)?
   - "Problem" fermentations (what went wrong)?
   - This would help us validate the system

---

## 4. BUSINESS UNCERTAINTIES

### 4.1 Value Proposition
**Your Original Concern**: "Anomalies are rare, so maybe we don't need all this analysis"

**Questions**:
1. **Does Protocol Compliance Engine have independent value?**
   - Even if anomalies are rare, is compliance tracking useful for:
     - Audit/compliance purposes?
     - Training new winemakers?
     - Identifying best practices?
     - Standardizing quality?

2. **Cost-benefit**: Is implementing this worth the engineering effort?
   - If it prevents just 1 "bad batch" per year (saves $10K wine), is it worth it?
   - If it helps train 1 new winemaker faster, is it worth it?

3. **Alternative**: Instead of automation, could you just use:
   - Paper checklist?
   - Excel spreadsheet?
   - Simple mobile app (cheaper than full integration)?

---

### 4.2 Scope & MVP
**Questions**:
1. **What's minimum viable product (MVP)?**
   - Just step logging + compliance score (basic)?
   - + Alerts/reminders?
   - + Analysis integration?
   - + Historical analytics?

2. **Should we launch with 1 varietal or all?**
   - Cabernet only (low risk)?
   - All varietals (more useful, more risky)?

3. **Timeline**: How soon do you need this?
   - Next harvest season (6 months)?
   - This year (urgent)?
   - Next year (flexible)?

---

## 5. TECHNICAL UNCERTAINTIES

### 5.1 Data Availability
**Questions**:
1. **Do you have historical protocols documented anywhere?**
   - Paper notes?
   - Excel sheets?
   - Recipes/notebooks?
   - We need this to create initial templates

2. **Do you track when steps were actually done?**
   - Currently logged anywhere?
   - Or would this be new data from day 1?

3. **Can we access past fermentation records?**
   - To correlate protocol adherence with outcomes?

---

### 5.2 Integration with Current Workflow
**Questions**:
1. **How would you use this in practice?**
   - Check app every day at same time?
   - Check when you arrive at winery?
   - Only when something goes wrong?

2. **Where would you log step completions?**
   - In winery office on desktop?
   - In vineyard on mobile?
   - Both?

3. **Would you use on phone while doing the work?**
   - Check next step, do it, log completion?
   - Or log all steps at end of day?

---

## QUESTIONS SUMMARY BY PRIORITY

### 🔴 CRITICAL (Must answer before Phase 0 coding):
- [ ] Is the compliance scoring formula reasonable?
- [ ] Which steps are CRITICAL vs IMPORTANT vs OPTIONAL?
- [ ] Can steps be skipped legitimately? When?
- [ ] Do protocols change? How often?
- [ ] What's the step sequencing (strict order or flexible)?

### 🟠 HIGH (Needed for Phase 1-2):
- [ ] Notification preferences?
- [ ] Protocol versions handling?
- [ ] Example protocols to use as templates?
- [ ] Does compliance actually predict problems?

### 🟡 MEDIUM (For later phases):
- [ ] User adoption concerns?
- [ ] Compliance vs quality correlation?
- [ ] MVP scope definition?
- [ ] Timeline/urgency?

### 🟢 LOW (Nice to have):
- [ ] Historical data availability?
- [ ] Mobile vs desktop usage?

---

## HOW TO PROCEED

**Option A: Deep Interview First** (2-3 hours)
- Schedule formal meeting
- Walk through all questions
- Document answers thoroughly
- Then start implementation

**Option B: Quick Clarification** (30 min)
- Ask only CRITICAL questions
- Start Phase 0 in parallel
- Refine as we go

**Option C: Working Session**
- You work with us during Phase 0
- We build first draft together
- Iterate based on feedback

**Which would work best for you?** 🤔

