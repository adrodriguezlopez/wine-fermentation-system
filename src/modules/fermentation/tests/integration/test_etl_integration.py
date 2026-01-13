"""
Integration tests for ETL Service with real database.

Tests complete import flow with actual database transactions:
- Entity creation and relationships
- Vineyard reuse across fermentations
- Shared default VineyardBlock behavior
- Progress tracking and cancellation
- Performance characteristics (N+1 elimination)

Uses real PostgreSQL test database (not mocks).
"""
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, func

from src.modules.fermentation.src.service_component.etl.etl_service import ETLService
from src.modules.fermentation.src.service_component.etl.cancellation_token import (
    CancellationToken,
    ImportCancelledException
)
from src.shared.testing.integration import TestSessionManager
from src.modules.fruit_origin.src.service_component.services.fruit_origin_service import FruitOriginService
from src.modules.fruit_origin.src.repository_component.repositories.vineyard_repository import VineyardRepository
from src.modules.fruit_origin.src.repository_component.repositories.vineyard_block_repository import VineyardBlockRepository
from src.modules.fruit_origin.src.repository_component.repositories.harvest_lot_repository import HarvestLotRepository
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository
from src.modules.fermentation.src.repository_component.repositories.lot_source_repository import LotSourceRepository
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource
from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample


@pytest.mark.asyncio
class TestETLIntegration:
    """Integration tests for ETL service with real database."""
    
    @pytest.fixture
    def etl_service(self, db_session):
        """Create ETL service with real repositories."""
        # Create session manager for repositories
        session_manager = TestSessionManager(db_session)
        
        # Create FruitOriginService with real repositories
        vineyard_repo = VineyardRepository(session_manager)
        vineyard_block_repo = VineyardBlockRepository(session_manager)
        harvest_lot_repo = HarvestLotRepository(session_manager)
        
        fruit_origin_service = FruitOriginService(
            vineyard_repo=vineyard_repo,
            harvest_lot_repo=harvest_lot_repo,
            vineyard_block_repo=vineyard_block_repo
        )
        
        # Create ETL service with session_manager (ADR-031)
        return ETLService(
            session_manager=session_manager,
            fruit_origin_service=fruit_origin_service
        )
    
    @pytest.fixture
    def sample_excel_file(self, tmp_path):
        """Create sample Excel file for testing."""
        excel_file = tmp_path / "test_fermentations.xlsx"
        
        # Create test data with 3 fermentations from 2 vineyards
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-001', 'FERM-002', 'FERM-002', 'FERM-003'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-12', '2023-03-12', '2023-03-15'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-12', '2023-04-12', '2023-04-15'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05', '2023-03-05', '2023-03-10'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte', 'Viña Norte', 'Viña Sur'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet', 'Cabernet', 'Merlot'],
            'harvest_mass_kg': [1500, 1500, 1500, 1500, 1200],
            'sample_date': ['2023-03-12', '2023-03-17', '2023-03-14', '2023-03-19', '2023-03-17'],
            'density': [1.090, 1.085, 1.092, 1.088, 1.095],
            'temperature_celsius': [18, 19, 18, 19, 20]
        })
        
        df.to_excel(excel_file, index=False, engine='openpyxl')
        return excel_file
    
    async def test_complete_import_flow_creates_all_entities(
        self, 
        etl_service, 
        sample_excel_file, 
        db_session, 
        test_winery,
        test_user
    ):
        """
        Integration test: Complete import creates all entities with correct relationships.
        
        Verifies:
        - Vineyards created
        - VineyardBlocks created (default blocks)
        - HarvestLots created
        - Fermentations created
        - FermentationLotSources created (links)
        - Samples created
        """
        # Import file
        result = await etl_service.import_file(
            sample_excel_file,
            winery_id=test_winery.id,
            user_id=test_user.id
        )
        
        # Verify import success
        assert result.success
        assert result.fermentations_created == 3
        assert result.samples_created == 10  # 5 rows * 2 samples (density + temperature) = 10
        assert len(result.failed_fermentations) == 0
        
        # Verify Vineyards created (2 unique: Viña Norte, Viña Sur)
        vineyards = await db_session.execute(
            select(Vineyard).where(Vineyard.winery_id == test_winery.id)
        )
        vineyard_list = vineyards.scalars().all()
        assert len(vineyard_list) == 2
        vineyard_codes = {v.code for v in vineyard_list}
        assert 'VIÑA-NORTE' in vineyard_codes
        assert 'VIÑA-SUR' in vineyard_codes
        
        # Verify VineyardBlocks created (2 default blocks, one per vineyard)
        blocks = await db_session.execute(
            select(VineyardBlock).join(Vineyard).where(Vineyard.winery_id == test_winery.id)
        )
        block_list = blocks.scalars().all()
        assert len(block_list) == 2
        block_codes = {b.code for b in block_list}
        assert 'VIÑA-NORTE-DEFAULT' in block_codes
        assert 'VIÑA-SUR-DEFAULT' in block_codes
        
        # Verify HarvestLots created (2 lots: Viña Norte + Viña Sur)
        # FERM-001 and FERM-002 share the same harvest lot (same vineyard + harvest date)
        lots = await db_session.execute(
            select(HarvestLot).where(HarvestLot.winery_id == test_winery.id)
        )
        lot_list = lots.scalars().all()
        assert len(lot_list) == 2
        
        # Verify Fermentations created (3 fermentations)
        fermentations = await db_session.execute(
            select(Fermentation).where(Fermentation.winery_id == test_winery.id)
        )
        ferm_list = fermentations.scalars().all()
        assert len(ferm_list) == 3
        ferm_codes = {f.vessel_code for f in ferm_list}
        assert 'FERM-001' in ferm_codes
        assert 'FERM-002' in ferm_codes
        assert 'FERM-003' in ferm_codes
        
        # Verify FermentationLotSources (3 links)
        lot_sources = await db_session.execute(
            select(FermentationLotSource)
        )
        source_list = lot_sources.scalars().all()
        assert len(source_list) == 3
        
        # Verify Samples created (5 samples: 2+2+1)
        density_samples = await db_session.execute(
            select(DensitySample)
        )
        density_list = density_samples.scalars().all()
        assert len(density_list) == 5
        
        temp_samples = await db_session.execute(
            select(CelsiusTemperatureSample)
        )
        temp_list = temp_samples.scalars().all()
        assert len(temp_list) == 5
    
    async def test_vineyard_reuse_across_fermentations(
        self,
        etl_service,
        tmp_path,
        db_session,
        test_winery,
        test_user
    ):
        """
        Integration test: Multiple fermentations from same vineyard reuse vineyard entity.
        
        Verifies N+1 query elimination - vineyard created once, reused multiple times.
        """
        excel_file = tmp_path / "same_vineyard.xlsx"
        
        # Create 5 fermentations all from "Viña Norte"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003', 'FERM-004', 'FERM-005'],
            'fermentation_start_date': ['2023-03-10'] * 5,
            'fermentation_end_date': ['2023-04-10'] * 5,
            'harvest_date': ['2023-03-05'] * 5,
            'vineyard_name': ['Viña Norte'] * 5,  # All same vineyard
            'grape_variety': ['Cabernet'] * 5,
            'harvest_mass_kg': [1500] * 5,
            'sample_date': ['2023-03-12'] * 5,
            'density': [1.090] * 5,
            'temperature_celsius': [18] * 5
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        # Import file
        result = await etl_service.import_file(
            excel_file,
            winery_id=test_winery.id,
            user_id=test_user.id
        )
        
        assert result.success
        assert result.fermentations_created == 5
        
        # Verify only 1 vineyard created (not 5)
        vineyards = await db_session.execute(
            select(Vineyard).where(Vineyard.winery_id == test_winery.id)
        )
        vineyard_list = vineyards.scalars().all()
        assert len(vineyard_list) == 1
        assert vineyard_list[0].code == 'VIÑA-NORTE'
        
        # Verify only 1 default block created (not 5)
        blocks = await db_session.execute(
            select(VineyardBlock).join(Vineyard).where(Vineyard.winery_id == test_winery.id)
        )
        block_list = blocks.scalars().all()
        assert len(block_list) == 1
        assert block_list[0].code == 'VIÑA-NORTE-DEFAULT'
        
        # Verify 5 harvest lots created (one per fermentation)
        lots = await db_session.execute(
            select(HarvestLot).where(HarvestLot.winery_id == test_winery.id)
        )
        lot_list = lots.scalars().all()
        assert len(lot_list) == 1  # All 5 fermentations share same vineyard + harvest date
    
    async def test_shared_default_block_prevents_duplicates(
        self,
        etl_service,
        tmp_path,
        db_session,
        test_winery,
        test_user
    ):
        """
        Integration test: Default VineyardBlock is reused, not duplicated.
        
        Verifies fix for UNIQUE constraint violation bug.
        """
        excel_file = tmp_path / "test_blocks.xlsx"
        
        # Create 3 fermentations from same vineyard
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003'],
            'fermentation_start_date': ['2023-03-10'] * 3,
            'fermentation_end_date': ['2023-04-10'] * 3,
            'harvest_date': ['2023-03-05'] * 3,
            'vineyard_name': ['Viña Test'] * 3,
            'grape_variety': ['Cabernet'] * 3,
            'harvest_mass_kg': [1500] * 3,
            'sample_date': ['2023-03-12'] * 3,
            'density': [1.090] * 3,
            'temperature_celsius': [18] * 3
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        # Import should succeed (no UNIQUE constraint violation)
        result = await etl_service.import_file(
            excel_file,
            winery_id=test_winery.id,
            user_id=test_user.id
        )
        
        assert result.success
        assert result.fermentations_created == 3
        
        # Verify only 1 block exists (shared)
        blocks = await db_session.execute(
            select(VineyardBlock).join(Vineyard)
            .where(Vineyard.winery_id == test_winery.id)
            .where(VineyardBlock.code == 'VIÑA-TEST-DEFAULT')
        )
        block_list = blocks.scalars().all()
        assert len(block_list) == 1
        
        # Verify all 3 harvest lots reference the same block
        lots = await db_session.execute(
            select(HarvestLot).where(HarvestLot.winery_id == test_winery.id)
        )
        lot_list = lots.scalars().all()
        assert len(lot_list) == 1  # All 3 fermentations share same vineyard + harvest date
        
        # Verify the single lot references the shared block
        assert lot_list[0].block_id == block_list[0].id
    
    async def test_progress_tracking_with_real_import(
        self,
        etl_service,
        sample_excel_file,
        test_winery,
        test_user
    ):
        """
        Integration test: Progress callback receives accurate progress updates.
        """
        progress_updates = []
        
        async def progress_callback(current: int, total: int):
            progress_updates.append({'current': current, 'total': total})
        
        result = await etl_service.import_file(
            sample_excel_file,
            winery_id=test_winery.id,
            user_id=test_user.id,
            progress_callback=progress_callback
        )
        
        assert result.success
        assert result.fermentations_created == 3
        
        # Verify progress updates
        assert len(progress_updates) == 3
        assert progress_updates[0] == {'current': 1, 'total': 3}
        assert progress_updates[1] == {'current': 2, 'total': 3}
        assert progress_updates[2] == {'current': 3, 'total': 3}
    
    async def test_cancellation_with_partial_commit(
        self,
        etl_service,
        tmp_path,
        db_session,
        test_winery,
        test_user
    ):
        """
        Integration test: Cancellation commits partial results to database.
        
        Verifies per-fermentation transaction strategy.
        """
        excel_file = tmp_path / "test_cancel.xlsx"
        
        # Create 5 fermentations
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003', 'FERM-004', 'FERM-005'],
            'fermentation_start_date': ['2023-03-10'] * 5,
            'fermentation_end_date': ['2023-04-10'] * 5,
            'harvest_date': ['2023-03-05'] * 5,
            'vineyard_name': ['Viña Norte'] * 5,
            'grape_variety': ['Cabernet'] * 5,
            'harvest_mass_kg': [1500] * 5,
            'sample_date': ['2023-03-12'] * 5,
            'density': [1.090] * 5,
            'temperature_celsius': [18] * 5
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        # Cancel after 2 fermentations
        cancellation_token = CancellationToken()
        
        async def progress_callback(current: int, total: int):
            if current == 2:
                await cancellation_token.cancel()
        
        # Import should raise ImportCancelledException
        with pytest.raises(ImportCancelledException) as exc_info:
            await etl_service.import_file(
                excel_file,
                winery_id=test_winery.id,
                user_id=test_user.id,
                progress_callback=progress_callback,
                cancellation_token=cancellation_token
            )
        
        # Verify partial import details
        assert exc_info.value.imported == 2
        assert exc_info.value.total == 5
        
        # Verify 2 fermentations were committed to database
        fermentations = await db_session.execute(
            select(Fermentation).where(Fermentation.winery_id == test_winery.id)
        )
        ferm_list = fermentations.scalars().all()
        assert len(ferm_list) == 2
        
        # Verify vineyard, block, and harvest lots also committed
        vineyards = await db_session.execute(
            select(Vineyard).where(Vineyard.winery_id == test_winery.id)
        )
        assert len(vineyards.scalars().all()) == 1
        
        blocks = await db_session.execute(
            select(VineyardBlock).join(Vineyard).where(Vineyard.winery_id == test_winery.id)
        )
        assert len(blocks.scalars().all()) == 1
        
        lots = await db_session.execute(
            select(HarvestLot).where(HarvestLot.winery_id == test_winery.id)
        )
        assert len(lots.scalars().all()) == 1  # Both committed fermentations share same vineyard + harvest date
    
    async def test_handles_missing_optional_fields(
        self,
        etl_service,
        tmp_path,
        db_session,
        test_winery,
        test_user
    ):
        """
        Integration test: Import succeeds with missing vineyard_name and grape_variety.
        
        Verifies default value handling (ADR-030).
        """
        excel_file = tmp_path / "missing_fields.xlsx"
        
        # Create data with missing optional fields
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05'],
            'vineyard_name': [None, ''],  # Missing and empty
            'grape_variety': [None, ''],  # Missing and empty
            'harvest_mass_kg': [1500, 1500],
            'sample_date': ['2023-03-12', '2023-03-12'],
            'density': [1.090, 1.090],
            'temperature_celsius': [18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        # Import should succeed
        result = await etl_service.import_file(
            excel_file,
            winery_id=test_winery.id,
            user_id=test_user.id
        )
        
        assert result.success
        assert result.fermentations_created == 2
        
        # Verify UNKNOWN vineyard created
        vineyards = await db_session.execute(
            select(Vineyard).where(Vineyard.winery_id == test_winery.id)
        )
        vineyard_list = vineyards.scalars().all()
        assert len(vineyard_list) == 1
        assert vineyard_list[0].code == 'UNKNOWN'
        
        # Verify harvest lots have "Unknown" grape variety
        lots = await db_session.execute(
            select(HarvestLot).where(HarvestLot.winery_id == test_winery.id)
        )
        lot_list = lots.scalars().all()
        assert len(lot_list) == 1  # Both fermentations share same harvest lot
        assert all(lot.grape_variety == 'UNKNOWN' for lot in lot_list)  # Missing grape_variety defaults to 'UNKNOWN'
