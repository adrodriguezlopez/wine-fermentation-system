# ADR-<ID>: <Título>

**Status:** Proposed | Accepted | Superseded  
**Date:** YYYY-MM-DD  
**Authors:** <Nombre/es>

---

## Context
Resumen breve (3–5 frases) del problema / necesidad.  
Mencionar decisiones previas (ADR-XXX) que impactan.  
Enlaces a docs adicionales.

---

## Decision
Lista numerada de decisiones técnicas.  
Cada punto = 1–2 frases, claras.  
Ejemplo:  
1. No generic repo → cada agregado tiene su interfaz.  
2. BaseRepository en infra → helpers técnicos (session, errores, soft-delete).

---

## Implementation Notes
```
<estructura de carpetas y archivos clave>
```

Responsabilidades de cada componente (bullets).  
Opcional: diagrama ASCII si ayuda.

---

## Consequences
- ✅ Beneficios específicos
- ⚠️ Trade-offs y riesgos conocidos
- ❌ Limitaciones aceptadas

---

## TDD Plan (opcional - solo para ADRs técnicos)
- **Componente/método** → condición esperada
- Formato: Qué testear → resultado esperado

---

## Quick Reference
- Bullets estilo checklist con decisiones clave
- Para consulta rápida durante desarrollo
- Máximo 7-8 bullets

---

## API Examples (opcional - solo si hay APIs complejas)
```python
# Ejemplo concreto de uso
# Solo si la API no es obvia
```

---

## Error Catalog (opcional - solo para infra/repos)
- ErrorType (external) → DomainError (internal)
- Solo para layers que mapean errores

---

## Acceptance Criteria (opcional - para ADRs con validación compleja)
- [ ] Criterios verificables y testeable
- [ ] Usar solo si hay múltiples requisitos no obvios

---

## Status
Proposed | Accepted | Superseded  


