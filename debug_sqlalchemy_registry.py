"""
Script de Debugging para SQLAlchemy Registry Issue

Este script te ayuda a investigar el problema de "Multiple classes found"
en el registry de SQLAlchemy.

Uso:
    python debug_sqlalchemy_registry.py

Qué hace:
    1. Muestra el estado del registry ANTES de importar modelos
    2. Importa los modelos y muestra el estado DESPUÉS
    3. Intenta crear instancias para ver dónde falla
    4. Muestra información detallada del error
"""

import sys
from pathlib import Path

# Agregar el path del proyecto
project_root = Path(__file__).parent / "src" / "modules" / "fermentation"
sys.path.insert(0, str(project_root.parent.parent))

print("=" * 80)
print("DEBUGGING SQLAlchemy Registry Issue")
print("=" * 80)
print()

# ==============================================================================
# PASO 1: Estado inicial del registry
# ==============================================================================
print("PASO 1: Inspeccionando Base ANTES de imports")
print("-" * 80)

from src.shared.infra.orm.base_entity import Base, BaseEntity

print(f"Base class: {Base}")
print(f"Base.__subclasses__(): {Base.__subclasses__()}")
print(f"Base.registry: {Base.registry}")
print(f"Base.registry._class_registry keys: {list(Base.registry._class_registry.keys())[:10]}")  # Primeros 10
print()

# ==============================================================================
# PASO 2: Importar modelos UNO POR UNO y ver qué pasa
# ==============================================================================
print("PASO 2: Importando modelos UNO POR UNO")
print("-" * 80)

try:
    print("Importando Winery...")
    from src.modules.winery.src.domain.entities.winery import Winery
    print(f"  ✓ Winery importado. Registry size: {len(Base.registry._class_registry)}")
    
    print("Importando HarvestLot...")
    from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
    print(f"  ✓ HarvestLot importado. Registry size: {len(Base.registry._class_registry)}")
    
    print("Importando User...")
    from src.modules.fermentation.src.domain.entities.user import User
    print(f"  ✓ User importado. Registry size: {len(Base.registry._class_registry)}")
    print(f"  User en registry: {Base.registry._class_registry.get('User', 'NOT FOUND')}")
    
    print("Importando Fermentation...")
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
    print(f"  ✓ Fermentation importado. Registry size: {len(Base.registry._class_registry)}")
    print(f"  Fermentation en registry: {Base.registry._class_registry.get('Fermentation', 'NOT FOUND')}")
    
    print("Importando BaseSample...")
    from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
    print(f"  ✓ BaseSample importado. Registry size: {len(Base.registry._class_registry)}")
    
except Exception as e:
    print(f"\n❌ ERROR durante imports: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ==============================================================================
# PASO 3: Ver el contenido del registry en detalle
# ==============================================================================
print("PASO 3: Contenido del registry después de todos los imports")
print("-" * 80)

print("Clases en Base.registry._class_registry:")
for key, value in Base.registry._class_registry.items():
    if not key.startswith("_"):  # Filtrar clases internas
        print(f"  '{key}': {value}")

print()

# ==============================================================================
# PASO 4: Verificar relationships
# ==============================================================================
print("PASO 4: Inspeccionando relationships")
print("-" * 80)

try:
    print(f"User.__mapper__.relationships.keys(): {list(User.__mapper__.relationships.keys())}")
    print(f"Fermentation.__mapper__.relationships.keys(): {list(Fermentation.__mapper__.relationships.keys())}")
    
    # Ver detalles de una relationship
    print("\nDetalles de User.fermentations:")
    user_fermentations_rel = User.__mapper__.relationships.get('fermentations')
    if user_fermentations_rel:
        print(f"  mapper: {user_fermentations_rel.mapper}")
        print(f"  entity: {user_fermentations_rel.entity}")
        print(f"  back_populates: {user_fermentations_rel.back_populates}")
    
except Exception as e:
    print(f"\n❌ ERROR inspeccionando relationships: {e}")
    import traceback
    traceback.print_exc()

print()

# ==============================================================================
# PASO 5: Intentar crear instancias (aquí debería fallar)
# ==============================================================================
print("PASO 5: Intentando crear instancias de modelos")
print("-" * 80)

try:
    print("Creando Winery()...")
    winery = Winery(id=1, name="Test Winery", region="Test Region")
    print(f"  ✓ Winery creado: {winery}")
    
    print("Creando User()...")
    user = User(
        id=1, 
        usernmame="testuser",
        email="test@example.com", 
        password_hash="hash",
        full_name="Test User",
        winery_id=1
    )
    print(f"  ✓ User creado: {user}")
    
    print("Creando Fermentation()...")
    fermentation = Fermentation(
        id=1,
        winery_id=1,
        fermented_by_user_id=1,
        vintage_year=2024,
        yeast_strain="Test Yeast",
        input_mass_kg=100.0,
        initial_sugar_brix=22.0,
        initial_density=1.095,
        start_date="2024-10-05"
    )
    print(f"  ✓ Fermentation creado: {fermentation}")
    
except Exception as e:
    print(f"\n❌ ERROR creando instancias: {e}")
    print(f"\nTipo de error: {type(e).__name__}")
    print("\nTraceback completo:")
    import traceback
    traceback.print_exc()
    
    # Información adicional para debugging
    print("\n" + "=" * 80)
    print("INFORMACIÓN ADICIONAL PARA DEBUGGING:")
    print("=" * 80)
    
    if "Multiple classes found" in str(e):
        print("\n⚠️  PROBLEMA CONFIRMADO: Multiple classes found")
        print("\nEsto sucede porque SQLAlchemy está viendo múltiples registros")
        print("de la misma clase en su registry.")
        print("\nPosibles causas:")
        print("  1. Imports múltiples del mismo módulo")
        print("  2. Relationships bidireccionales sin fully qualified paths")
        print("  3. DeclarativeBase sin registry explícito")
        print("  4. Reimports durante hot reload")
        
        # Buscar duplicados en el registry
        print("\nBuscando duplicados en el registry...")
        from collections import defaultdict
        class_counts = defaultdict(int)
        
        for key in Base.registry._class_registry.keys():
            if not key.startswith("_"):
                class_counts[key] += 1
        
        print("\nClases registradas más de una vez:")
        for class_name, count in class_counts.items():
            if count > 1:
                print(f"  {class_name}: {count} veces")
    
    sys.exit(1)

print()
print("=" * 80)
print("✅ DEBUG COMPLETADO SIN ERRORES")
print("=" * 80)
print("\nSi llegaste aquí, significa que NO hay problema de registry")
print("en imports normales. El problema debe ser específico de los tests.")
