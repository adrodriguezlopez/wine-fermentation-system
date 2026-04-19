# ADR-<ID>: <Título>

**Status:** Proposed | Accepted | Superseded  
**Date:** YYYY-MM-DD  
**Authors:** <Nombre/es>  
**Related ADRs:** ADR-XXX (short title), ADR-YYY (short title)

> **📋 Context Files:** Para decisiones arquitectónicas, revisar:
> - [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md) - Principios de diseño
> <!-- Agregar otros archivos específicos según el ADR -->

---

## Context
Resumen breve (3–5 frases) del problema / necesidad.  
Mencionar decisiones previas (ADR-XXX) que impactan.  
Enlaces a docs adicionales.

---

## Decision
Lista numerada de decisiones técnicas.  
Cada punto = 1–2 frases, claras.

**Schema/enums**: Si la decisión define una tabla, enum, o estructura de datos,
incluirla aquí como bloque de código. Si es extensa (>30 líneas), moverla a
Implementation Notes y referenciarla desde aquí.

Ejemplo:  
1. No generic repo → cada agregado tiene su interfaz.  
2. BaseRepository en infra → helpers técnicos (session, errores, soft-delete).

---

## Implementation Notes
```
<estructura de carpetas y archivos clave>
```

Responsabilidades de cada componente (bullets).  
Schemas/enums extensos van aquí si no caben en Decision.  
Opcional: diagrama ASCII si ayuda.

---

## Architectural Considerations (opcional - solo si hay desviaciones)
> **Default:** Este proyecto sigue [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)  
> **Solo documentar aquí:** Desviaciones, trade-offs, o decisiones específicas de arquitectura

- **Deviations from SOLID:** <justificación si no se sigue algún principio>
- **Alternative patterns considered:** <por qué se rechazaron otras opciones>
- **Performance vs Clean Code trade-offs:** <decisiones específicas>
- **Technology constraints:** <limitaciones que afectan arquitectura>

---

## Consequences
- ✅ Beneficios específicos
- ⚠️ Trade-offs y riesgos conocidos
- ❌ Limitaciones aceptadas

---

## Related ADRs
- **[ADR-XXX](./ADR-XXX-title.md)**: Por qué se relaciona (base, extensión, conflicto, dependencia)
- **[ADR-YYY](./ADR-YYY-title.md)**: Por qué se relaciona

---

## TDD Plan (incluir para ADRs técnicos con implementación)
- **Componente/método** → condición esperada
- Formato: Qué testear → resultado esperado
- Omitir solo si el ADR es puramente arquitectural sin implementación nueva

---

## Quick Reference (incluir si hay >5 decisiones o el ADR es complejo)
- Bullets estilo checklist con decisiones clave
- Para consulta rápida durante desarrollo
- Máximo 7-8 bullets

---

## API Examples (incluir solo si hay contratos de API nuevos o no obvios)
```python
# Ejemplo concreto de uso
# Solo si la API no es obvia
```

---

## Error Catalog (incluir solo para infrastructure/repos que mapean errores)
- ErrorType (external) → DomainError (internal)

---

## Acceptance Criteria (incluir si hay múltiples requisitos verificables)
- [ ] Criterios verificables y testeables

---

## Status
Proposed | Accepted | Superseded
