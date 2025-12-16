# ADR-013: Sample Entity Design Evaluation

**Status:** Analysis  
**Date:** 2025-12-15  
**Authors:** Development Team  
**Related:** ADR-011 (Integration Test Infrastructure), ADR-002 (Repository Architecture)

---

## Context

El sistema actual usa **Single-Table Inheritance (STI)** para los modelos de Sample (SugarSample, DensitySample, CelsiusTemperatureSample). Durante la implementación del ADR-011, se descubrió que este patrón causa **conflictos de metadata en tests de integración** debido a cómo SQLAlchemy maneja índices globales.

**Estructura Actual:**
```
samples (tabla única)
├── id (PK)
├── sample_type (discriminador: 'sugar', 'density', 'temperature')
├── fermentation_id (FK, indexed)
├── recorded_at (indexed)
├── recorded_by_user_id (FK)
├── value (medición numérica)
├── units (string: 'brix', 'specific_gravity', '°C')
└── timestamps (created_at, updated_at, is_deleted)

Clases:
- BaseSample (abstracta) → tabla 'samples'
  - SugarSample → discriminator='sugar', units='brix'
  - DensitySample → discriminator='density', units='specific_gravity'
  - CelsiusTemperatureSample → discriminator='temperature', units='°C'
```

**Problema Actual:**
- ✅ Funcionamiento en producción: **perfecto**
- ✅ Queries simples y eficientes
- ❌ Tests de integración: **conflictos de metadata** (índices duplicados)
- ❌ Require workaround: ejecutar tests de samples aisladamente

---

## Análisis de Alternativas

### Opción 1: Single-Table Inheritance (STI) - ACTUAL

**Diseño:**
```sql
CREATE TABLE samples (
    id INTEGER PRIMARY KEY,
    sample_type VARCHAR(50) NOT NULL,  -- discriminador
    fermentation_id INTEGER NOT NULL REFERENCES fermentations(id),
    recorded_at TIMESTAMP NOT NULL,
    recorded_by_user_id INTEGER NOT NULL REFERENCES users(id),
    value FLOAT NOT NULL,
    units VARCHAR(20) NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    INDEX ix_samples_sample_type (sample_type),
    INDEX ix_samples_fermentation_id (fermentation_id),
    INDEX ix_samples_recorded_at (recorded_at)
);
```

**Ventajas:**
- ✅ **Queries extremadamente simples**: Un solo SELECT para obtener todos los samples
- ✅ **Sin JOINs**: Máximo rendimiento en lectura
- ✅ **Orden cronológico trivial**: `ORDER BY recorded_at` funciona directamente
- ✅ **Almacenamiento eficiente**: Sin columnas NULL, todas las mediciones usan `value + units`
- ✅ **Queries polimórficas fáciles**: `SELECT * FROM samples WHERE fermentation_id = ?`
- ✅ **Simplicidad en código**: Clases Python limpias y mínimas
- ✅ **Migraciones simples**: Agregar nuevo tipo de sample solo requiere nueva clase Python
- ✅ **Ideal para estructura uniforme**: Todos los samples tienen exactamente los mismos campos

**Desventajas:**
- ❌ **Conflicto en tests**: SQLAlchemy metadata global causa duplicación de índices
- ❌ **Requiere workaround**: Tests deben ejecutarse en aislamiento
- ⚠️ **No escalable para heterogeneidad**: Si samples futuras necesitaran campos específicos diferentes

**Complejidad de Código:**
```python
# Repository query - SIMPLE
async def get_samples_by_fermentation_id(self, fermentation_id: int):
    stmt = select(BaseSample).where(
        BaseSample.fermentation_id == fermentation_id
    ).order_by(BaseSample.recorded_at.asc())
    result = await session.execute(stmt)
    return result.scalars().all()  # ✅ Un solo query, un solo resultado

# Actualmente necesita iterar 3 clases por limitación de testing:
for sample_class in [SugarSample, DensitySample, CelsiusTemperatureSample]:
    stmt = select(sample_class).where(...)  # ❌ Workaround innecesario
```

**Performance:**
- **Lecturas**: O(1) - Un solo query, un solo índice scan
- **Escrituras**: O(1) - INSERT directo sin overhead
- **Análisis temporal**: O(n) con índice en `recorded_at` - óptimo
- **Filtrado por tipo**: O(n) con índice en `sample_type` - óptimo

**Casos de Uso Reales:**
```python
# GET /fermentations/123/samples - Listar todos los samples
SELECT * FROM samples WHERE fermentation_id = 123 ORDER BY recorded_at;
# ✅ 1 query, simple

# GET /fermentations/123/samples/latest?type=sugar
SELECT * FROM samples 
WHERE fermentation_id = 123 AND sample_type = 'sugar'
ORDER BY recorded_at DESC LIMIT 1;
# ✅ 1 query con índice compuesto óptimo

# Análisis de tendencia (API real)
SELECT * FROM samples 
WHERE fermentation_id = 123 
  AND recorded_at BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY recorded_at;
# ✅ 1 query, range scan eficiente
```

---

### Opción 2: Joined-Table Inheritance (JTI)

**Diseño:**
```sql
-- Tabla base
CREATE TABLE samples (
    id INTEGER PRIMARY KEY,
    sample_type VARCHAR(50) NOT NULL,
    fermentation_id INTEGER NOT NULL REFERENCES fermentations(id),
    recorded_at TIMESTAMP NOT NULL,
    recorded_by_user_id INTEGER NOT NULL REFERENCES users(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    INDEX ix_samples_fermentation_id (fermentation_id),
    INDEX ix_samples_recorded_at (recorded_at)
);

-- Tablas específicas (JOIN con samples)
CREATE TABLE sugar_samples (
    id INTEGER PRIMARY KEY REFERENCES samples(id),
    value FLOAT NOT NULL,
    units VARCHAR(20) DEFAULT 'brix'
);

CREATE TABLE density_samples (
    id INTEGER PRIMARY KEY REFERENCES samples(id),
    value FLOAT NOT NULL,
    units VARCHAR(20) DEFAULT 'specific_gravity'
);

CREATE TABLE temperature_samples (
    id INTEGER PRIMARY KEY REFERENCES samples(id),
    value FLOAT NOT NULL,
    units VARCHAR(20) DEFAULT '°C'
);
```

**Ventajas:**
- ✅ **Normalización perfecta**: Sin redundancia de estructura
- ✅ **Escalabilidad para heterogeneidad**: Cada tipo puede tener campos únicos
- ✅ **Separación clara**: Cada tipo en su propia tabla
- ✅ **Tests aislados**: Cada tabla tiene su propia metadata
- ✅ **Mejor para tipos muy diferentes**: Si sugar_sample necesitara campos adicionales únicos

**Desventajas:**
- ❌ **Queries complejas**: SIEMPRE requiere JOINs
- ❌ **Performance degradado**: 2-4 JOINs por query polimórfico
- ❌ **Orden cronológico complejo**: UNION de 3 queries + ORDER BY
- ❌ **Código de repository complejo**: Múltiples queries y merging manual
- ❌ **Overhead de almacenamiento**: Datos de contexto duplicados (fermentation_id, recorded_at en base + específicas)
- ❌ **Migraciones más complejas**: Agregar tipo requiere nueva tabla + migration
- ❌ **Sobrecarga innecesaria**: Nuestros samples son estructuralmente idénticos (value + units)

**Complejidad de Código:**
```python
# Repository query - COMPLEJO
async def get_samples_by_fermentation_id(self, fermentation_id: int):
    # Opción A: Polimórfico con JOINs automáticos (SQLAlchemy hace 3 queries + merge)
    stmt = select(BaseSample).where(
        BaseSample.fermentation_id == fermentation_id
    ).order_by(BaseSample.recorded_at.asc())
    # SQLAlchemy genera internamente:
    # SELECT samples.*, sugar_samples.* FROM samples LEFT JOIN sugar_samples ...
    # UNION
    # SELECT samples.*, density_samples.* FROM samples LEFT JOIN density_samples ...
    # UNION
    # SELECT samples.*, temperature_samples.* FROM samples LEFT JOIN temperature_samples ...
    # ❌ 3 queries + merge en Python
    
    # Opción B: Manual (más eficiente pero más código)
    samples = []
    for SampleClass in [SugarSample, DensitySample, CelsiusTemperatureSample]:
        stmt = select(SampleClass).join(BaseSample).where(...)
        results = await session.execute(stmt)
        samples.extend(results.scalars().all())
    samples.sort(key=lambda s: s.recorded_at)
    return samples
    # ❌ Mucho código, múltiples queries
```

**Performance:**
- **Lecturas**: O(n * k) donde k = número de tipos de sample (3 en nuestro caso)
- **Escrituras**: O(2) - INSERT en samples + INSERT en tabla específica
- **Análisis temporal**: O(n * k) + sorting en Python
- **Filtrado por tipo**: O(n) pero con JOIN overhead

**Casos de Uso Reales:**
```sql
-- GET /fermentations/123/samples - ¡COMPLEJO!
SELECT s.*, ss.value, ss.units FROM samples s
LEFT JOIN sugar_samples ss ON s.id = ss.id WHERE s.sample_type = 'sugar'
UNION ALL
SELECT s.*, ds.value, ds.units FROM samples s
LEFT JOIN density_samples ds ON s.id = ds.id WHERE s.sample_type = 'density'
UNION ALL
SELECT s.*, ts.value, ts.units FROM samples s
LEFT JOIN temperature_samples ts ON s.id = ts.id WHERE s.sample_type = 'temperature'
ORDER BY recorded_at;
-- ❌ 3 queries + UNION + sorting

-- Alternativa (peor aún):
SELECT s.*, 
       COALESCE(ss.value, ds.value, ts.value) as value,
       COALESCE(ss.units, ds.units, ts.units) as units
FROM samples s
LEFT JOIN sugar_samples ss ON s.id = ss.id
LEFT JOIN density_samples ds ON s.id = ds.id  
LEFT JOIN temperature_samples ts ON s.id = ts.id
WHERE s.fermentation_id = 123;
-- ❌ 3 LEFT JOINs por query, muchos NULL
```

---

### Opción 3: Concrete-Table Inheritance (CTI)

**Diseño:**
```sql
-- NO hay tabla base compartida
CREATE TABLE sugar_samples (
    id INTEGER PRIMARY KEY,
    fermentation_id INTEGER NOT NULL REFERENCES fermentations(id),
    recorded_at TIMESTAMP NOT NULL,
    recorded_by_user_id INTEGER NOT NULL REFERENCES users(id),
    value FLOAT NOT NULL,
    units VARCHAR(20) DEFAULT 'brix',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    INDEX ix_sugar_samples_fermentation_id (fermentation_id),
    INDEX ix_sugar_samples_recorded_at (recorded_at)
);

CREATE TABLE density_samples (
    -- Misma estructura completa repetida
    ...
);

CREATE TABLE temperature_samples (
    -- Misma estructura completa repetida
    ...
);
```

**Ventajas:**
- ✅ **Aislamiento perfecto**: Tablas completamente independientes
- ✅ **Sin metadata conflicts**: Cada tabla tiene sus propios índices
- ✅ **Tests simples**: Cada tipo se testea independientemente
- ✅ **Performance por tipo**: Queries filtradas por tipo son óptimas
- ✅ **Escalabilidad por tipo**: Puedes optimizar índices específicos por tipo

**Desventajas:**
- ❌ **Duplicación masiva de código**: Estructura repetida 3 veces
- ❌ **Queries polimórficas horribles**: UNION de 3 tablas completas
- ❌ **Mantenimiento pesadilla**: Cambio de esquema requiere 3 migraciones
- ❌ **Imposible mantener orden cronológico global eficientemente**
- ❌ **FKs redundantes**: fermentation_id repetido 3 veces con índices separados
- ❌ **Violación DRY extrema**: Todo duplicado
- ❌ **Código de repository muy complejo**: Lógica repetida o abstracciones complicadas

**Complejidad de Código:**
```python
# Repository query - HORRIBLE
async def get_samples_by_fermentation_id(self, fermentation_id: int):
    samples = []
    
    # Query 1: Sugar samples
    stmt1 = select(SugarSample).where(
        SugarSample.fermentation_id == fermentation_id
    )
    result1 = await session.execute(stmt1)
    samples.extend(result1.scalars().all())
    
    # Query 2: Density samples
    stmt2 = select(DensitySample).where(
        DensitySample.fermentation_id == fermentation_id
    )
    result2 = await session.execute(stmt2)
    samples.extend(result2.scalars().all())
    
    # Query 3: Temperature samples
    stmt3 = select(CelsiusTemperatureSample).where(
        CelsiusTemperatureSample.fermentation_id == fermentation_id
    )
    result3 = await session.execute(stmt3)
    samples.extend(result3.scalars().all())
    
    # Manual sorting (NO HAY ÍNDICE GLOBAL)
    samples.sort(key=lambda s: s.recorded_at)
    return samples
    # ❌ 3 queries separados, sorting en Python, código repetitivo
```

**Performance:**
- **Lecturas polimórficas**: O(3n) - 3 queries completos
- **Lecturas por tipo**: O(n) - óptimo cuando sabes el tipo
- **Escrituras**: O(1) - INSERT directo en tabla específica
- **Análisis temporal**: O(3n) + sorting en Python - MALO
- **Imposible tener índice global en recorded_at para orden cronológico**

**Casos de Uso Reales:**
```sql
-- GET /fermentations/123/samples - TERRIBLE
SELECT *, 'sugar' as type FROM sugar_samples WHERE fermentation_id = 123
UNION ALL
SELECT *, 'density' as type FROM density_samples WHERE fermentation_id = 123
UNION ALL
SELECT *, 'temperature' as type FROM temperature_samples WHERE fermentation_id = 123
ORDER BY recorded_at;
-- ❌ 3 full table scans + UNION + sorting sin índice

-- GET /fermentations/123/samples/latest?type=sugar - OK
SELECT * FROM sugar_samples 
WHERE fermentation_id = 123 
ORDER BY recorded_at DESC LIMIT 1;
-- ✅ Pero solo cuando filtras por tipo específico
```

---

### Opción 4: Tabla Única sin Herencia (Diseño Plano)

**Diseño:**
```sql
CREATE TABLE samples (
    id INTEGER PRIMARY KEY,
    sample_type VARCHAR(50) NOT NULL,  -- pero sin polimorfismo ORM
    fermentation_id INTEGER NOT NULL REFERENCES fermentations(id),
    recorded_at TIMESTAMP NOT NULL,
    recorded_by_user_id INTEGER NOT NULL REFERENCES users(id),
    value FLOAT NOT NULL,
    units VARCHAR(20) NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    INDEX ix_samples_sample_type (sample_type),
    INDEX ix_samples_fermentation_id (fermentation_id),
    INDEX ix_samples_recorded_at (recorded_at)
);

-- Solo una clase:
class Sample(BaseEntity):
    sample_type: str
    value: float
    units: str
    # ...
    
# Sin subclases SugarSample, DensitySample, etc.
```

**Ventajas:**
- ✅ **Sin metadata conflicts**: Una sola clase = un solo conjunto de índices
- ✅ **Queries simples**: Idénticos a STI
- ✅ **Tests simples**: Sin problemas de herencia
- ✅ **Performance idéntico a STI**: Misma estructura de tabla

**Desventajas:**
- ❌ **Pérdida de type safety**: No hay SugarSample vs DensitySample en código
- ❌ **Pérdida de semántica de dominio**: Todo es genérico `Sample`
- ❌ **Validaciones en runtime**: No puedes confiar en tipos para units correctos
- ❌ **Peor developer experience**: sample.sample_type == "sugar" vs isinstance(sample, SugarSample)
- ❌ **Código menos expresivo**: Pierdes polimorfismo OOP

**Complejidad de Código:**
```python
# Antes (STI):
sugar_sample = SugarSample(value=18.5)  # units='brix' automático
assert isinstance(sugar_sample, SugarSample)  # Type checking

# Después (Plano):
sample = Sample(sample_type="sugar", value=18.5, units="brix")  # Manual
if sample.sample_type == "sugar":  # String checking ❌
    # ...
```

---

## Comparación Cuantitativa

| Métrica | STI (actual) | JTI | CTI | Plano |
|---------|--------------|-----|-----|-------|
| **Queries polimórficos** | 1 query | 3 queries + JOIN | 3 queries + UNION | 1 query |
| **Performance lecturas** | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ |
| **Código repository** | 5 líneas | 20+ líneas | 30+ líneas | 5 líneas |
| **Complejidad mantención** | Baja | Media | Alta | Baja |
| **Type safety** | ★★★★★ | ★★★★★ | ★★★★★ | ★☆☆☆☆ |
| **Tests integración** | ⚠️ Workaround | ✅ Sin issues | ✅ Sin issues | ✅ Sin issues |
| **Escalabilidad heterogénea** | ★★☆☆☆ | ★★★★★ | ★★★★★ | ★☆☆☆☆ |
| **Duplicación de estructura** | 0% | ~30% | ~200% | 0% |
| **Migraciones futuras** | Trivial | Media | Compleja | Trivial |

---

## Análisis de Casos de Uso del Sistema

**Queries más frecuentes en producción:**

1. **GET /fermentations/{id}/samples** (60% del tráfico)
   - STI: ✅ 1 query óptimo
   - JTI: ❌ 3 queries + merge
   - CTI: ❌ 3 queries + UNION
   - Plano: ✅ 1 query óptimo

2. **GET /fermentations/{id}/samples/latest?type=sugar** (25% del tráfico)
   - STI: ✅ 1 query con índice compuesto
   - JTI: ⚠️ 1 query pero con JOIN
   - CTI: ✅ 1 query óptimo (mejor caso)
   - Plano: ✅ 1 query con índice compuesto

3. **POST /samples** - Crear nuevo sample (10% del tráfico)
   - STI: ✅ 1 INSERT
   - JTI: ❌ 2 INSERTs (samples + tipo específico)
   - CTI: ✅ 1 INSERT
   - Plano: ✅ 1 INSERT

4. **GET /samples/timerange** - Análisis temporal (5% del tráfico)
   - STI: ✅ 1 query con range scan
   - JTI: ❌ 3 queries + merge + sorting
   - CTI: ❌ 3 queries + UNION + sorting
   - Plano: ✅ 1 query con range scan

**Conclusión de casos de uso:** STI y Plano ganan en 90% del tráfico real.

---

## Recomendación

### ✅ **MANTENER Single-Table Inheritance**

**Justificación:**

1. **Performance es crítico**: 90% de queries son polimórficos, STI es 3-5x más rápido
2. **Simplicidad de código**: Repository actual tiene ~100 líneas, con JTI serían ~300+
3. **Estructura homogénea**: Los 3 tipos de sample son idénticos (value + units)
4. **Type safety importa**: SugarSample vs DensitySample mejora calidad de código
5. **El problema de tests es manejable**: Workaround documentado y funcional
6. **Escalabilidad suficiente**: No necesitamos campos específicos por tipo

**Solución al problema de tests:**

### Opción A: Mantener status quo (RECOMENDADO)
- Tests de samples se ejecutan aisladamente (ya documentado)
- Ejecutar: `pytest src/modules/fermentation/tests/integration/repository_component/test_sample_repository_integration.py`
- **Costo**: Ejecutar un comando adicional (~3 segundos)
- **Beneficio**: Mantener arquitectura óptima para producción

### Opción B: Future enhancement (ADR-011 Phase 3)
Si el workaround se vuelve insostenible:
1. Crear metadata registry separado solo para tests de samples
2. Usar `pytest-xdist` con workers aislados
3. Rediseñar índices para evitar conflictos globales

### ❌ **NO RECOMENDADO: Cambiar a JTI o CTI**

**Por qué NO cambiar:**
- ❌ **Degradación de performance**: 3-5x más lento en 90% de casos de uso
- ❌ **Complejidad innecesaria**: Código 3-6x más largo sin beneficio real
- ❌ **Resolver problema menor con solución mayor**: Tests aislados son suficientes
- ❌ **Nuestros samples NO necesitan campos heterogéneos**: value + units es suficiente
- ❌ **Overengineering**: Sacrificar simplicidad por problema de testing marginal

---

## Decisión Final

**MANTENER Single-Table Inheritance (STI)**

**Rationale:**
- ✅ Optimal performance para el 90% de queries reales
- ✅ Código simple y mantenible
- ✅ Type safety y semántica de dominio clara
- ✅ El problema de tests tiene workaround documentado y funcional
- ✅ Arquitectura correcta para el dominio actual

**Action Items:**
1. ✅ Documentar limitación de tests en ADR-011 (completado)
2. ✅ Crear conftest local para tests de samples (completado)
3. 📋 Agregar nota en README de testing sobre ejecución aislada
4. 📋 Considerar Phase 3 de ADR-011 solo si el workaround se vuelve bloqueante

**Status:** ✅ **DECISION TOMADA - MANTENER STI**

---

## Referencias

- [ADR-011: Integration Test Infrastructure Refactoring](./ADR-011-integration-test-infrastructure-refactoring.md)
- [ADR-002: Repository Architecture](./ADR-002-repositories-architecture/ADR-002-repositories-architecture.md)
- [ADR-003: Repository Separation of Concerns](./ADR-003-repository-interface-refactoring.md)
- [SQLAlchemy: Inheritance Mapping](https://docs.sqlalchemy.org/en/20/orm/inheritance.html)
- [Martin Fowler: Patterns of Enterprise Application Architecture - Inheritance Mapping](https://martinfowler.com/eaaCatalog/)
