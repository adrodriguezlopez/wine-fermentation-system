"""
Script Simple: Test de Import Doble

Este script simula lo que hacen los tests de integración:
importar los modelos dos veces desde diferentes contextos.

Uso:
    python debug_double_import.py

Resultado esperado:
    - Si falla con "Multiple classes found" = Confirma el problema
    - Si pasa sin errores = El problema es específico del contexto de pytest
"""

import sys
from pathlib import Path

# Agregar el path del proyecto
project_root = Path(__file__).parent / "src" / "modules" / "fermentation"
sys.path.insert(0, str(project_root.parent.parent))

print("=" * 80)
print("TEST: Simulando Double Import (como en pytest)")
print("=" * 80)
print()

# ==============================================================================
# IMPORT #1: Como lo hace conftest.py
# ==============================================================================
print("IMPORT #1: Importando desde __init__.py (como conftest.py)")
print("-" * 80)

try:
    from src.modules.fermentation.src.domain.entities import (
        User as User1,
        Fermentation as Fermentation1,
        BaseSample as BaseSample1
    )
    print("✓ Import #1 exitoso")
    print(f"  User1: {User1}")
    print(f"  Fermentation1: {Fermentation1}")
    print(f"  BaseSample1: {BaseSample1}")
except Exception as e:
    print(f"❌ Import #1 falló: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ==============================================================================
# IMPORT #2: Como lo haría un test
# ==============================================================================
print("IMPORT #2: Importando directo (como haría un test)")
print("-" * 80)

try:
    from src.modules.fermentation.src.domain.entities.user import User as User2
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation as Fermentation2
    from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample as BaseSample2
    print("✓ Import #2 exitoso")
    print(f"  User2: {User2}")
    print(f"  Fermentation2: {Fermentation2}")
    print(f"  BaseSample2: {BaseSample2}")
except Exception as e:
    print(f"❌ Import #2 falló: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ==============================================================================
# VERIFICAR: ¿Son la misma clase?
# ==============================================================================
print("VERIFICACIÓN: ¿Son las mismas clases?")
print("-" * 80)

print(f"User1 is User2: {User1 is User2}")
print(f"Fermentation1 is Fermentation2: {Fermentation1 is Fermentation2}")
print(f"BaseSample1 is BaseSample2: {BaseSample1 is BaseSample2}")

if User1 is not User2:
    print("\n⚠️  PROBLEMA: User1 y User2 son DIFERENTES objetos")
    print("Esto causará 'Multiple classes found'")
else:
    print("\n✓ User1 y User2 son el MISMO objeto (cache de Python funcionando)")

print()

# ==============================================================================
# CREAR INSTANCIA: Aquí debería fallar si hay problema
# ==============================================================================
print("CREACIÓN DE INSTANCIA: Intentando crear Winery")
print("-" * 80)

try:
    from src.modules.winery.src.domain.entities.winery import Winery
    
    winery = Winery(id=1, name="Test Winery", region="Test Region")
    print(f"✓ Winery creado exitosamente: {winery}")
    
    # Ahora crear User (esto debería disparar la configuración de relationships)
    print("\nCreando User (dispara configuración de relationships)...")
    user = User1(
        id=1,
        usernmame="test",
        email="test@test.com",
        password_hash="hash",
        full_name="Test User",
        winery_id=1
    )
    print(f"✓ User creado exitosamente: {user}")
    
    print("\n" + "=" * 80)
    print("✅ ÉXITO: No hay problema de registry en imports normales")
    print("=" * 80)
    print("\nConclusión: El problema es específico del contexto de pytest")
    print("o de cómo se están importando los modelos en los tests.")
    
except Exception as e:
    print(f"\n❌ ERROR al crear instancias: {e}")
    print(f"\nTipo: {type(e).__name__}")
    
    if "Multiple classes found" in str(e):
        print("\n" + "=" * 80)
        print("⚠️  PROBLEMA CONFIRMADO: Multiple classes found")
        print("=" * 80)
        print("\nEl problema EXISTE incluso en imports normales.")
        print("NO es específico de pytest.")
        
        # Extraer el nombre de la clase problemática
        import re
        match = re.search(r'path "(\w+)"', str(e))
        if match:
            problematic_class = match.group(1)
            print(f"\nClase problemática: {problematic_class}")
            
            # Verificar en el registry
            from src.shared.infra.orm.base_entity import Base
            print(f"\nBuscando '{problematic_class}' en el registry...")
            
            registry_items = [
                (k, v) for k, v in Base.registry._class_registry.items() 
                if problematic_class in str(k)
            ]
            
            if registry_items:
                print(f"Encontradas {len(registry_items)} entradas:")
                for key, value in registry_items:
                    print(f"  {key}: {value}")
    
    print("\nTraceback completo:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
