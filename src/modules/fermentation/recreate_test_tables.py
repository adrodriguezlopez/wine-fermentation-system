"""
Script to recreate all test database tables with fresh schema
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from src.shared.infra.orm.base_entity import Base

# Import all entities to ensure they're registered with Base.metadata
from src.shared.auth.domain.entities.user import User
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.entities.recommendation import Recommendation
from src.modules.analysis_engine.src.domain.entities.recommendation_template import RecommendationTemplate

async def recreate_all_tables():
    engine = create_async_engine(
        'postgresql+asyncpg://postgres:postgres@localhost:5433/wine_fermentation_test',
        echo=False
    )
    
    print("Dropping all existing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("Creating fresh tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ All tables recreated successfully!")
    print(f"Created tables: {list(Base.metadata.tables.keys())}")

if __name__ == "__main__":
    asyncio.run(recreate_all_tables())
