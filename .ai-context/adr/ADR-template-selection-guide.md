# ADR Template Selection Guide

## Decision Matrix: ¿Qué template usar?

### 📋 **ADR-template-light.md** (4 secciones)
**Usar cuando:**
- ✅ Decisión arquitectural simple
- ✅ No requiere implementación compleja
- ✅ Team ya conoce el dominio
- ✅ Pocos stakeholders involucrados

**Ejemplos:**
- "Usar PostgreSQL vs MySQL"
- "Estructura de carpetas del proyecto"
- "Naming conventions"
- "Librería X vs Y para feature específica"

### 🏗️ **ADR-template.md** (11 secciones)
**Usar cuando:**
- ✅ Arquitectura de infrastructure/foundational
- ✅ Múltiples teams afectados
- ✅ API contracts complejas
- ✅ Patterns nuevos para el equipo
- ✅ Validación extensa requerida

**Ejemplos:**
- "Repository architecture"  
- "Event sourcing implementation"
- "Microservices communication patterns"
- "Security/auth architecture"

## 🚦 **Decision Process**

### Step 1: Identify ADR complexity
```
¿La decisión requiere Implementation Notes detalladas? 
├─ No → Use ADR-template-light.md
└─ Yes → Continue to Step 2

¿La decisión introduce APIs/contracts nuevos?
├─ No → Use ADR-template-light.md  
└─ Yes → Continue to Step 3

¿La decisión requiere extensive testing strategy?
├─ No → Use ADR-template-light.md
└─ Yes → Use ADR-template.md
```

### Step 2: Validate choice
- **Light**: 1 página max, 30 min para escribir
- **Full**: 2-3 páginas, 2-3 horas para escribir

Si sientes que necesitas más de 1 página → usa template completo.

## 📊 **Usage Prediction**
- **Light**: ~70% de ADRs
- **Full**: ~30% de ADRs (infrastructure, core architecture)

## ✅ **Template Evolution**
- Start with light by default
- Upgrade to full si durante escritura necesitas más secciones
- Never downgrade from full to light (perderías info)