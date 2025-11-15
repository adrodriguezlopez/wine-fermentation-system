"""
Script Simple para Debuggear Registry de SQLAlchemy
Sin emojis, compatible con Windows cmd/powershell
"""

import sys
from pathlib import Path

# Agregar el path del proyecto
project_root = Path(__file__).parent / "src" / "modules" / "fermentation"
sys.path.insert(0, str(project_root.parent.parent))

print("=" * 80)
print("DEBUGGING SQLAlchemy Registry")
print("=" * 80)
print()

# ==============================================================================
# PASO 1: Estado del registry ANTES de imports
# ==============================================================================
print("PASO 1: Registry ANTES de importar modelos")
print("-" * 80)

from src.shared.infra.orm.base_entity import Base

print(f"Base class: {Base}")
print(f"Registry object: {Base.registry}")
print(f"Registry._class_registry size: {len(Base.registry._class_registry)}")
print(f"Registry._class_registry keys: {list(Base.registry._class_registry.keys())}")
print()

# ==============================================================================
# PASO 2: Importar modelos y ver el registry después de cada uno
# ==============================================================================
print("PASO 2: Importando modelos UNO POR UNO")
print("-" * 80)

print("Importando Winery...")
from src.modules.winery.src.domain.entities.winery import Winery
print(f"  Registry size: {len(Base.registry._class_registry)}")
print(f"  Clases: {list(Base.registry._class_registry.keys())}")
print()

print("Importando HarvestLot...")
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
print(f"  Registry size: {len(Base.registry._class_registry)}")
print()

print("Importando User...")
from src.modules.fermentation.src.domain.entities.user import User
print(f"  Registry size: {len(Base.registry._class_registry)}")
print()

print("Importando Fermentation...")
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
print(f"  Registry size: {len(Base.registry._class_registry)}")
print()

print("Importando BaseSample...")
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
print(f"  Registry size: {len(Base.registry._class_registry)}")
print()

print("Importando SugarSample...")
from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
print(f"  Registry size: {len(Base.registry._class_registry)}")
print()

# ==============================================================================
# PASO 3: Ver TODAS las clases en el registry
# ==============================================================================
print("PASO 3: Contenido completo del registry")
print("-" * 80)

for i, (key, value) in enumerate(Base.registry._class_registry.items(), 1):
    print(f"{i}. Key: {key}")
    print(f"   Value: {value}")
    print()

# ==============================================================================
# PASO 4: Buscar duplicados de "Fermentation"
# ==============================================================================
print("PASO 4: Buscando 'Fermentation' en el registry")
print("-" * 80)

fermentation_entries = [
    (k, v) for k, v in Base.registry._class_registry.items() 
    if 'Fermentation' in str(k) or 'fermentation' in str(k).lower()
]

if fermentation_entries:
    print(f"Encontradas {len(fermentation_entries)} entradas con 'Fermentation':")
    for key, value in fermentation_entries:
        print(f"  Key: {key}")
        print(f"  Value: {value}")
        print()
else:
    print("No se encontraron entradas con 'Fermentation'")

# ==============================================================================
# PASO 5: Intentar crear instancia
# ==============================================================================
print("PASO 5: Intentando crear instancia de Winery")
print("-" * 80)

try:
    winery = Winery(id=1, name="Test Winery", region="Test Region")
    print(f"OK - Winery creado: {winery}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    print()
    print("Traceback:")
    import traceback
    traceback.print_exc()
