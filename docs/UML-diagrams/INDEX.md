# 📊 What's in This Folder

Welcome to the **UML Diagrams** folder! This folder contains **30+ professional Mermaid diagrams** documenting the entire Wine Fermentation Monitoring System.

## 🚀 Quick Start (Choose Your Path)

### 👤 I'm New to This Project
**⏱️ Time: 15 minutes**

1. Read: [00-QUICK-REFERENCE.md](00-QUICK-REFERENCE.md) ← **Start here!**
2. Read: [README.md](README.md)
3. Skim: [01-GENERAL-ARCHITECTURE.md](01-GENERAL-ARCHITECTURE.md)
4. Explore: Pick any diagram that interests you

### 👨‍💻 I'm a Developer
**⏱️ Time: 30 minutes**

1. Quick overview: [01-GENERAL-ARCHITECTURE.md](01-GENERAL-ARCHITECTURE.md)
2. Your module: Find in [02-COMPONENTS.md](02-COMPONENTS.md)
3. Deep dive: [03-CLASS-DIAGRAMS.md](03-CLASS-DIAGRAMS.md) (classes for your module)
4. Workflows: [04-SEQUENCE-DIAGRAMS.md](04-SEQUENCE-DIAGRAMS.md) (how things interact)

### 🏗️ I'm an Architect
**⏱️ Time: 1 hour**

1. System design: [01-GENERAL-ARCHITECTURE.md](01-GENERAL-ARCHITECTURE.md)
2. All components: [02-COMPONENTS.md](02-COMPONENTS.md)
3. All classes: [03-CLASS-DIAGRAMS.md](03-CLASS-DIAGRAMS.md)
4. Data flow: [06-DEPLOYMENT-INFRASTRUCTURE.md](06-DEPLOYMENT-INFRASTRUCTURE.md)
5. Review everything else

### 🧪 I'm a QA/Tester
**⏱️ Time: 20 minutes**

1. Use cases: [05-USE-CASES.md](05-USE-CASES.md) (what to test)
2. Workflows: [04-SEQUENCE-DIAGRAMS.md](04-SEQUENCE-DIAGRAMS.md) (how to test)
3. Error scenarios: [05-USE-CASES.md](05-USE-CASES.md#error-handling-scenarios)
4. Data isolation: [04-SEQUENCE-DIAGRAMS.md](04-SEQUENCE-DIAGRAMS.md#multi-winery-data-isolation-sequence)

### 👔 I'm a Product Manager
**⏱️ Time: 25 minutes**

1. Features: [05-USE-CASES.md](05-USE-CASES.md)
2. Workflows: [04-SEQUENCE-DIAGRAMS.md](04-SEQUENCE-DIAGRAMS.md)
3. System capacity: [06-DEPLOYMENT-INFRASTRUCTURE.md](06-DEPLOYMENT-INFRASTRUCTURE.md) (scroll to "Scalability")

---

## 📋 File-by-File Guide

### 📌 `00-QUICK-REFERENCE.md` ⭐ **START HERE**
**What**: Visual index of all diagrams  
**Best for**: Finding what you need fast  
**Contains**:
- What's in each file
- Quick lookup table
- Finding specific information
- Learning path recommendation

### 📌 `README.md` ⭐ **READ SECOND**
**What**: Complete navigation guide  
**Best for**: Understanding the full picture  
**Contains**:
- Diagrams by type
- Diagrams by module
- Architecture summary
- Security info
- Data models

### 📌 `01-GENERAL-ARCHITECTURE.md`
**What**: System-level architecture (4 diagrams)  
**Best for**: Understanding how it all fits together  
**Contains**:
- 🏛️ High-level system overview
- 📊 Module dependencies
- 🔄 Data flow for new measurement
- 🎯 Clean architecture layers
- 🏪 Multi-tenancy architecture

### 📌 `02-COMPONENTS.md`
**What**: Detailed component breakdown (4 diagrams)  
**Best for**: Understanding each module's internals  
**Contains**:
- 🍇 Fermentation Module components
- 📊 Analysis Engine components
- 🌍 Fruit Origin Module components
- 🔐 Authentication Module components

### 📌 `03-CLASS-DIAGRAMS.md`
**What**: Entity and class relationships (4 diagrams)  
**Best for**: Understanding data structures  
**Contains**:
- 🍇 Fermentation classes and entity hierarchy
- 📊 Analysis Engine entities and value objects
- 🌍 Fruit Origin entities
- 🔐 User and authentication classes

### 📌 `04-SEQUENCE-DIAGRAMS.md`
**What**: Step-by-step workflows (7 diagrams)  
**Best for**: Understanding how operations work  
**Contains**:
1. ✏️ Create Fermentation (with validation)
2. 📝 Add Sample (with multi-level checks)
3. 🔍 Fermentation Analysis (anomaly detection + recommendations)
4. 🔑 User Login (JWT token generation)
5. 📚 Historical Data Comparison
6. 🏪 Multi-Winery Data Isolation
7. 🗑️ Soft Delete (logical deletion)

### 📌 `05-USE-CASES.md`
**What**: User interactions (5 diagrams + descriptions)  
**Best for**: Understanding what users can do  
**Contains**:
- 🎯 Main system use cases (UC-001 to UC-012)
- 🍇 Fermentation Management workflows
- 📊 Analysis & Recommendations workflows
- 📚 Historical Insights workflows
- ❌ Error handling scenarios
- ✅ Preconditions & postconditions

### 📌 `06-DEPLOYMENT-INFRASTRUCTURE.md`
**What**: System deployment (6 diagrams)  
**Best for**: Understanding deployment and infrastructure  
**Contains**:
- ☁️ Cloud deployment architecture
- 🏢 On-premise deployment option
- 📦 Module interaction & data flow
- 🗄️ Database schema architecture
- 🐳 Docker Compose infrastructure
- 🚀 CI/CD pipeline

### 📌 `GENERATION-SUMMARY.md`
**What**: Summary of what was generated  
**Best for**: Verification and overview  
**Contains**:
- Deliverables checklist
- Diagrams count by type
- Coverage analysis
- Quality metrics

---

## 🎯 Find Answers to Your Questions

### "How does the system work?"
→ [01-GENERAL-ARCHITECTURE.md](01-GENERAL-ARCHITECTURE.md)

### "How do I create a fermentation?"
→ [04-SEQUENCE-DIAGRAMS.md#create-fermentation-sequence](04-SEQUENCE-DIAGRAMS.md#create-fermentation-sequence)

### "How do I add a sample?"
→ [04-SEQUENCE-DIAGRAMS.md#add-sample-to-fermentation-sequence](04-SEQUENCE-DIAGRAMS.md#add-sample-to-fermentation-sequence)

### "How does analysis work?"
→ [04-SEQUENCE-DIAGRAMS.md#fermentation-analysis-sequence](04-SEQUENCE-DIAGRAMS.md#fermentation-analysis-sequence)

### "What can users do?"
→ [05-USE-CASES.md](05-USE-CASES.md)

### "How are users authenticated?"
→ [04-SEQUENCE-DIAGRAMS.md#user-login-sequence](04-SEQUENCE-DIAGRAMS.md#user-login-sequence)

### "How is data isolated between wineries?"
→ [04-SEQUENCE-DIAGRAMS.md#multi-winery-data-isolation-sequence](04-SEQUENCE-DIAGRAMS.md#multi-winery-data-isolation-sequence)

### "What classes and entities exist?"
→ [03-CLASS-DIAGRAMS.md](03-CLASS-DIAGRAMS.md)

### "How do we deploy the system?"
→ [06-DEPLOYMENT-INFRASTRUCTURE.md](06-DEPLOYMENT-INFRASTRUCTURE.md)

### "What's the database schema?"
→ [06-DEPLOYMENT-INFRASTRUCTURE.md#database-schema-architecture](06-DEPLOYMENT-INFRASTRUCTURE.md#database-schema-architecture)

---

## 📊 By the Numbers

```
Total Files:          9 (8 documentation + 1 summary)
Total Diagrams:       30+
Total Content:        44+ KB
Time to Read All:     ~2-3 hours
Time to Read Summary: ~15 minutes

Modules Documented:   6 (Fermentation, Analysis, Fruit Origin, Auth, Winery, Infra)
Workflows Visualized: 7 
Use Cases Covered:    12
Classes Documented:   50+
Entities Modeled:     20+
```

---

## ✨ What You'll Learn

After reading these diagrams, you'll understand:

- ✅ System architecture and all modules
- ✅ How data flows through the system
- ✅ How users interact with the system
- ✅ How fermentations are created and tracked
- ✅ How samples are validated
- ✅ How analysis is performed
- ✅ How recommendations are generated
- ✅ How historical data is used
- ✅ How multi-tenancy is enforced
- ✅ How security works
- ✅ How the system scales
- ✅ How the system is deployed

---

## 🎓 Learning Recommendations

### Day 1
- ⏱️ 30 minutes total
- Read: [00-QUICK-REFERENCE.md](00-QUICK-REFERENCE.md)
- Read: [README.md](README.md)
- Skim: [01-GENERAL-ARCHITECTURE.md](01-GENERAL-ARCHITECTURE.md)

### Day 2
- ⏱️ 45 minutes total
- Deep dive: [02-COMPONENTS.md](02-COMPONENTS.md)
- Deep dive: [03-CLASS-DIAGRAMS.md](03-CLASS-DIAGRAMS.md)

### Day 3
- ⏱️ 45 minutes total
- Study: [04-SEQUENCE-DIAGRAMS.md](04-SEQUENCE-DIAGRAMS.md)
- Review: [05-USE-CASES.md](05-USE-CASES.md)

### Day 4
- ⏱️ 30 minutes total
- Infrastructure: [06-DEPLOYMENT-INFRASTRUCTURE.md](06-DEPLOYMENT-INFRASTRUCTURE.md)
- Refresh anything unclear

### Result
After 2.5 hours, you'll have a complete understanding of the system architecture, design patterns, workflows, and deployment strategy.

---

## 🔍 Diagram Rendering

All diagrams are written in **Mermaid** format and will render automatically in:
- ✅ GitHub (markdown files)
- ✅ VS Code (with Markdown preview or extensions)
- ✅ Notion
- ✅ Confluence
- ✅ Any markdown viewer

### View Diagrams
1. **On GitHub**: Click on any `.md` file in the browser
2. **In VS Code**: Open file and use Markdown preview (Ctrl+Shift+V)
3. **In IDE**: Use built-in markdown preview or Mermaid extensions

---

## 📝 Notes

### Color Coding
- 🟡 Yellow: Domain/Business Logic
- 🟩 Green: Infrastructure/Database
- 🟦 Blue: Services/API
- 🟥 Red/Pink: External/Async
- 🟪 Purple: Testing/Utilities

### Status Indicators
- ✅ Complete (Implemented, fully working)
- 🔄 In Progress (Partially working or planned)
- 📋 Proposed (Not yet started)
- ⏭️ Future (Post-MVP)

---

## ❓ FAQ

**Q: Can I modify these diagrams?**  
A: Yes! They're in plain text Mermaid format. Edit freely and update.

**Q: Can I export as images?**  
A: Yes! GitHub renders them as images. Right-click to save, or use Mermaid CLI.

**Q: Are these up-to-date?**  
A: Generated February 6, 2026. Check Git history for when they were last updated.

**Q: Which one should I read first?**  
A: [00-QUICK-REFERENCE.md](00-QUICK-REFERENCE.md) - it has recommendations based on your role.

---

## 🎯 Next Steps

1. **Pick your role** above (Developer, Architect, QA, Product Manager)
2. **Follow the suggested reading path**
3. **Deep dive into specific diagrams** as needed
4. **Use as reference** while working on the system

---

## 📊 Folder Summary

```
📁 docs/UML-diagrams/
├── 📄 00-QUICK-REFERENCE.md       ⭐ START HERE (visual index)
├── 📄 README.md                   📚 Full navigation guide
├── 📄 01-GENERAL-ARCHITECTURE.md  🏛️ System overview
├── 📄 02-COMPONENTS.md            🔧 Component design
├── 📄 03-CLASS-DIAGRAMS.md        📊 Classes & entities
├── 📄 04-SEQUENCE-DIAGRAMS.md     🔄 Workflows
├── 📄 05-USE-CASES.md             👥 User interactions
├── 📄 06-DEPLOYMENT-INFRASTRUCTURE.md  🚀 Deployment
├── 📄 GENERATION-SUMMARY.md       ✅ What was created
└── 📄 INDEX.md                    ← You are here
```

---

**Happy exploring! 🚀**

Start with [00-QUICK-REFERENCE.md](00-QUICK-REFERENCE.md) →

