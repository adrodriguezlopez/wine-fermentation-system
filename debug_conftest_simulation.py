"""
Script que simula EXACTAMENTE lo que hace conftest.py
para reproducir el error "Multiple classes found"
"""

import sys
from pathlib import Path

# Agregar el path del proyecto
project_root = Path(__file__).parent / "src" / "modules" / "fermentation"
sys.path.insert(0, str(project_root.parent.parent))

print("=" * 80)
print("Simulando conftest.py - Importando como lo hace db_engine fixture")
print("=" * 80)
print()

from src.shared.infra.orm.base_entity import Base

print("Registry ANTES de imports:")
print(f"  Size: {len(Base.registry._class_registry)}")
print()

# ==============================================================================
# Esto es EXACTAMENTE lo que hace db_engine() en conftest.py
# ==============================================================================
print("Importando EXACTAMENTE como conftest.py:")
print("-" * 80)

# Primera importación: Winery y HarvestLot (directo)
from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
print(f"Después de Winery y HarvestLot: {len(Base.registry._class_registry)} clases")

# Segunda importación: Desde __init__.py (como conftest)
from src.modules.fermentation.src.domain.entities import (
    User,
    Fermentation,
    FermentationNote,
    FermentationLotSource,
    BaseSample,
    SugarSample,
    DensitySample,
    CelsiusTemperatureSample,
)
print(f"Después de imports desde __init__.py: {len(Base.registry._class_registry)} clases")
print()

# ==============================================================================
# Buscar duplicados
# ==============================================================================
print("Buscando 'Fermentation' en registry:")
print("-" * 80)
fermentation_entries = [
    (k, v) for k, v in Base.registry._class_registry.items() 
    if 'Fermentation' in str(k)
]
print(f"Encontradas {len(fermentation_entries)} entradas:")
for key, value in fermentation_entries:
    print(f"  {key}: {value}")
print()

# ==============================================================================
# Intentar crear Winery (esto es lo que falla en conftest)
# ==============================================================================
print("Intentando crear Winery (línea 168 de conftest.py):")
print("-" * 80)

try:
    winery = Winery(id=1, name="Test Winery", region="Test Region")
    print(f"OK - Winery creado exitosamente")
    print()
    
    # Ahora intentar crear User
    print("Intentando crear User:")
    user = User(
        id=1,
        usernmame="test",
        email="test@test.com",
        password_hash="hash",
        full_name="Test User",
        winery_id=1
    )
    print(f"OK - User creado exitosamente")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}")
    print(f"Message: {e}")
    print()
    
    # Si el error menciona "Multiple classes found", mostrar detalles del registry
    if "Multiple classes found" in str(e):
        print("=" * 80)
        print("PROBLEMA CONFIRMADO: Multiple classes found")
        print("=" * 80)
        print()
        print("TODAS las clases en el registry:")
        for i, (key, value) in enumerate(Base.registry._class_registry.items(), 1):
            print(f"{i}. {key}: {value}")
