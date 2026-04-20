# ADR Template Selection Guide

## Decision Matrix: ¿Qué template usar?

### 📋 **ADR-template-light.md** (5 secciones)
**Usar cuando:**
- ✅ Decisión arquitectural simple o de alcance limitado
- ✅ No requiere implementación compleja
- ✅ Team ya conoce el dominio
- ✅ Pocos stakeholders involucrados

**Ejemplos:**
- "Usar PostgreSQL vs MySQL"
- "Estructura de carpetas del proyecto"
- "Naming conventions"
- "Librería X vs Y para feature específica"
- Nueva entidad que sigue patrones establecidos

### 🏗️ **ADR-template.md** (secciones base + opcionales)
**Usar cuando:**
- ✅ Arquitectura de infrastructure/foundational
- ✅ Múltiples módulos afectados
- ✅ API contracts nuevos o complejos
- ✅ Patterns nuevos para el equipo
- ✅ Validación extensa requerida
- ✅ Nuevo módulo completo

**Ejemplos:**
- "Repository architecture"
- "Event sourcing implementation"
- "Microservices communication patterns"
- "Security/auth architecture"
- Nuevo módulo con múltiples entidades

## 🚦 **Decision Process**

```
¿La decisión requiere Implementation Notes detalladas?
├─ No → Use ADR-template-light.md
└─ Yes → Continue to Step 2

¿La decisión introduce APIs/contracts nuevos o afecta múltiples módulos?
├─ No → Use ADR-template-light.md
└─ Yes → Continue to Step 3

¿La decisión requiere TDD Plan o Acceptance Criteria explícitos?
├─ No → Use ADR-template-light.md
└─ Yes → Use ADR-template.md
```

## 📊 **Secciones opcionales del template completo — cuándo incluirlas**

| Sección | Incluir cuando... |
|---|---|
| **Implementation Notes** | Hay estructura de carpetas nueva o schema extenso (>30 líneas) |
| **TDD Plan** | ADR técnico con implementación nueva — siempre que haya código |
| **Quick Reference** | Más de 5 decisiones o ADR complejo que se consultará durante desarrollo |
| **API Examples** | Hay contratos de API nuevos o no obvios |
| **Error Catalog** | Layer de infra/repo que mapea errores externos a domain errors |
| **Acceptance Criteria** | Múltiples requisitos verificables que no son obvios de los tests |

**Regla general:** Si sientes que necesitas más de 1 página → usa template completo.

## 📊 **Usage Prediction**
- **Light**: ~70% de ADRs
- **Full**: ~30% de ADRs (infrastructure, core architecture, nuevos módulos)

## ✅ **Template Evolution**
- Start with light by default
- Upgrade to full si durante escritura necesitas más secciones
- Never downgrade from full to light (perderías info)

## 📖 **Referencia de calidad — ADRs reales del proyecto**
Antes de escribir, leer 1-2 ADRs recientes como referencia de calidad:
- **ADR-041** (Action Tracking) — ejemplo de ADR completo con schema detallado
- **ADR-040** (Notifications) — ejemplo de ADR con código y arquitectura
- **ADR-038** (Deviation Detection) — ejemplo de ADR técnico bien estructurado
