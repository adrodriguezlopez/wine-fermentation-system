"""
Script para limpiar la base de datos de test
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from src.shared.infra.orm.base_entity import Base

async def drop_all_tables():
    engine = create_async_engine(
        'postgresql+asyncpg://postgres:postgres@localhost:5433/wine_fermentation_test',
        echo=False
    )
    
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()
    print("All tables dropped successfully!")

if __name__ == "__main__":
    asyncio.run(drop_all_tables())
