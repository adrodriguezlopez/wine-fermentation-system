"""
Tests for ETL Service.

ETLService orchestrates the complete import process:
- Runs all 3 validation layers
- Creates fermentations and samples with data_source=IMPORTED
- Handles transactions and rollback
- Generates error reports
- Tracks import job progress
"""
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal

from src.modules.fermentation.src.service_component.etl.etl_service import ETLService, ImportResult
from src.modules.fermentation.src.domain.enums.data_source import DataSource
from src.modules.fruit_origin.src.service_component.interfaces.fruit_origin_service_interface import IFruitOriginService


class TestETLService:
    """Test suite for ETL Service orchestration."""
    
    @pytest.fixture(autouse=True)
    def patch_entities(self, monkeypatch):
        """Patch entity classes to avoid SQLAlchemy initialization in unit tests."""
        # Mock samples (still needed as ETL creates sample entities directly)
        mock_density = MagicMock()
        mock_temp = MagicMock()
        mock_sugar = MagicMock()
        
        # Apply patches
        # Note: Fermentation and FermentationLotSource no longer patched - ETL uses DTOs
        monkeypatch.setattr('src.modules.fermentation.src.service_component.etl.etl_service.DensitySample', mock_density)
        monkeypatch.setattr('src.modules.fermentation.src.service_component.etl.etl_service.CelsiusTemperatureSample', mock_temp)
        monkeypatch.setattr('src.modules.fermentation.src.service_component.etl.etl_service.SugarSample', mock_sugar)
    
    @pytest.fixture
    def mock_fermentation_repo(self):
        """Mock fermentation repository."""
        repo = Mock()
        # Return a mock fermentation with id when created
        mock_ferm = Mock()
        mock_ferm.id = "test-ferm-id-123"
        repo.create = AsyncMock(return_value=mock_ferm)
        return repo
    
    @pytest.fixture
    def mock_sample_repo(self):
        """Mock sample repository."""
        repo = Mock()
        repo.create = AsyncMock(return_value=None)
        return repo
    
    @pytest.fixture
    def mock_vineyard_repo(self):
        """Mock vineyard repository."""
        repo = Mock()
        # Return None for get_by_code (vineyard doesn't exist yet)
        repo.get_by_code = AsyncMock(return_value=None)
        # Return mock vineyard when created
        mock_vineyard = Mock()
        mock_vineyard.id = 1
        mock_vineyard.code = "Viña Norte"
        mock_vineyard.name = "Viña Norte"
        repo.create = AsyncMock(return_value=mock_vineyard)
        return repo
    
    @pytest.fixture
    def mock_vineyard_block_repo(self):
        """Mock vineyard block repository."""
        repo = Mock()
        mock_block = Mock()
        mock_block.id = 1
        mock_block.vineyard_id = 1
        mock_block.code = "Viña Norte-IMPORTED-DEFAULT"
        repo.create = AsyncMock(return_value=mock_block)
        return repo
    
    @pytest.fixture
    def mock_harvest_lot_repo(self):
        """Mock harvest lot repository."""
        repo = Mock()
        mock_lot = Mock()
        mock_lot.id = 1
        mock_lot.block_id = 1
        mock_lot.code = "HL-FERM-001"
        mock_lot.harvest_date = datetime(2023, 3, 5).date()
        mock_lot.weight_kg = 1500.0
        repo.create = AsyncMock(return_value=mock_lot)
        return repo
    
    @pytest.fixture
    def mock_lot_source_repo(self):
        """Mock lot source repository."""
        repo = Mock()
        repo.create = AsyncMock(return_value=None)
        return repo
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager for TransactionScope."""
        session_mgr = Mock()
        session_mgr.begin = AsyncMock()
        session_mgr.commit = AsyncMock()
        session_mgr.rollback = AsyncMock()
        return session_mgr
    
    @pytest.fixture
    def mock_fruit_origin_service(self):
        """Mock fruit origin service with orchestration method."""
        service = Mock(spec=IFruitOriginService)
        
        # Mock HarvestLot returned by ensure_harvest_lot_for_import()
        mock_lot = Mock()
        mock_lot.id = 1
        mock_lot.code = "LOT-VIÑA-NORTE-20230305"
        mock_lot.harvest_date = datetime(2023, 3, 5).date()
        mock_lot.weight_kg = 1500.0
        mock_lot.grape_variety = "Cabernet"
        
        service.ensure_harvest_lot_for_import = AsyncMock(return_value=mock_lot)
        return service
    
    @pytest.fixture
    def etl_service(self, mock_session_manager, mock_fruit_origin_service, mock_fermentation_repo, mock_sample_repo, mock_lot_source_repo):
        """Create ETL service with mocked dependencies."""
        # Create service instance
        service = ETLService(
            session_manager=mock_session_manager,
            fruit_origin_service=mock_fruit_origin_service
        )
        
        # Store mocks and patcher objects for test assertions
        service._mock_fermentation_repo = mock_fermentation_repo
        service._mock_sample_repo = mock_sample_repo
        service._mock_lot_source_repo = mock_lot_source_repo
        service._mock_session_manager = mock_session_manager
        
        # Create patchers that will be active for the entire test
        service._patchers = [
            patch('src.modules.fermentation.src.service_component.etl.etl_service.FermentationRepository', return_value=mock_fermentation_repo),
            patch('src.modules.fermentation.src.service_component.etl.etl_service.SampleRepository', return_value=mock_sample_repo),
            patch('src.modules.fermentation.src.service_component.etl.etl_service.LotSourceRepository', return_value=mock_lot_source_repo)
        ]
        
        # Start all patchers
        for patcher in service._patchers:
            patcher.start()
        
        yield service
        
        # Stop all patchers after test completes
        for patcher in service._patchers:
            patcher.stop()
    
    @pytest.mark.asyncio
    async def test_rejects_file_failing_row_validation(self, etl_service, tmp_path):
        """ETL should reject files that fail row validation."""
        excel_file = tmp_path / "invalid_rows.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            'grape_variety': ['Cabernet'],
            'harvest_mass_kg': [-100],  # Invalid: negative
            'sample_date': ['2023-03-14'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert not result.success
        assert result.phase_failed == 'row_validation'
        assert len(result.row_errors) > 0
        assert result.fermentations_created == 0
        assert result.samples_created == 0
    
    @pytest.mark.asyncio
    async def test_rejects_file_failing_post_validation(self, etl_service, tmp_path):
        """ETL should reject files that fail post-validation."""
        excel_file = tmp_path / "invalid_chronology.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-03-05'],  # Before start date
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            'grape_variety': ['Cabernet'],
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-14'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert not result.success
        assert result.phase_failed == 'post_validation'
        assert len(result.row_errors) > 0
        assert result.fermentations_created == 0
        assert result.samples_created == 0
    
    @pytest.mark.asyncio
    async def test_imports_valid_single_fermentation_with_samples(self, etl_service, tmp_path):
        """ETL should successfully import valid fermentation with samples."""
        excel_file = tmp_path / "valid_single.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-001'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500],
            'sample_date': ['2023-03-12', '2023-03-15'],
            'density': [1.090, 1.085],
            'temperature_celsius': [18, 19]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert result.success
        assert result.phase_failed is None
        assert result.fermentations_created == 1
        assert result.samples_created == 4  # 2 rows * 2 samples each (density, temperature)
        assert etl_service._mock_session_manager.commit.called
    
    @pytest.mark.asyncio
    async def test_imports_multiple_fermentations(self, etl_service, tmp_path):
        """ETL should import multiple fermentations from same file."""
        excel_file = tmp_path / "valid_multiple.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-001', 'FERM-002', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-15', '2023-03-15'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-15', '2023-04-15'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-10', '2023-03-10'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Sur', 'Viña Sur'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Merlot', 'Merlot'],
            'harvest_mass_kg': [1500, 1500, 2000, 2000],
            'sample_date': ['2023-03-12', '2023-03-15', '2023-03-17', '2023-03-20'],
            'density': [1.090, 1.085, 1.095, 1.090],
            'temperature_celsius': [18, 19, 18, 19]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert result.success
        assert result.fermentations_created == 2
        assert result.samples_created == 8  # 4 rows * 2 samples each
    
    @pytest.mark.asyncio
    async def test_calls_repository_create_methods(self, etl_service, mock_fruit_origin_service, tmp_path):
        """ETL should call FruitOriginService orchestration and repository create methods."""
        excel_file = tmp_path / "valid_data_source.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            'grape_variety': ['Cabernet'],
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-12'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        # Verify orchestration and repositories were called
        assert result.success
        
        # Fruit origin orchestration (replaces vineyard/block/harvest_lot direct calls)
        assert mock_fruit_origin_service.ensure_harvest_lot_for_import.called
        assert mock_fruit_origin_service.ensure_harvest_lot_for_import.call_count == 1
        
        # Verify correct arguments passed to orchestration
        call_args = mock_fruit_origin_service.ensure_harvest_lot_for_import.call_args
        assert call_args.kwargs['winery_id'] == 1
        assert call_args.kwargs['vineyard_name'] == 'Viña Norte'
        assert call_args.kwargs['grape_variety'] == 'Cabernet'
        assert call_args.kwargs['harvest_mass_kg'] == Decimal('1500')
        
        # Fermentation entities
        assert etl_service._mock_fermentation_repo.create.called
        assert etl_service._mock_lot_source_repo.create.called
        assert etl_service._mock_sample_repo.create.called
        
        # Verify correct number of fermentation entity calls
        assert etl_service._mock_fermentation_repo.create.call_count == 1
        assert etl_service._mock_lot_source_repo.create.call_count == 1
        assert etl_service._mock_sample_repo.create.call_count == 2  # density + temperature
    
    @pytest.mark.asyncio
    async def test_handles_optional_sugar_brix(self, etl_service, tmp_path):
        """ETL should handle optional sugar_brix field and create sugar samples when present."""
        excel_file = tmp_path / "with_sugar.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-001'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500],
            'sample_date': ['2023-03-12', '2023-03-15'],
            'density': [1.090, 1.085],
            'temperature_celsius': [18, 19],
            'sugar_brix': [25, 20]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert result.success
        assert result.samples_created == 6  # 2 rows * 3 samples each (density, temp, sugar)
        # Verify 6 sample create calls were made
        assert etl_service._mock_sample_repo.create.call_count == 6
    
    @pytest.mark.asyncio
    async def test_handles_duplicate_vessel_codes_via_database_constraint(self, etl_service, tmp_path):
        """ETL should handle duplicate vessel codes when database constraint is violated."""
        # Make repository raise constraint error on create
        etl_service._mock_fermentation_repo.create.side_effect = Exception("UNIQUE constraint failed")
        
        excel_file = tmp_path / "duplicate_vessel.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            'grape_variety': ['Cabernet'],
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-12'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert not result.success
        assert result.fermentations_created == 0
    
    @pytest.mark.asyncio
    async def test_rollback_on_database_error(self, etl_service, tmp_path):
        """ETL should handle database errors gracefully with automatic rollback via context manager."""
        # Make repository raise error on create
        etl_service._mock_fermentation_repo.create.side_effect = Exception("Database error")
        
        excel_file = tmp_path / "valid_file.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            'grape_variety': ['Cabernet'],
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-12'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        # Should fail gracefully
        assert not result.success
        assert result.fermentations_created == 0
        assert len(result.failed_fermentations) == 1
        assert 'Database error' in result.failed_fermentations[0]['error']
        
        # Commit should not have been called (error occurred before commit)
        assert not etl_service._mock_session_manager.commit.called
        
        # Note: Rollback is automatic via context manager __aexit__, not explicitly called
    
    @pytest.mark.asyncio
    async def test_returns_summary_statistics(self, etl_service, tmp_path):
        """ETL should return comprehensive import statistics."""
        excel_file = tmp_path / "stats_test.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-001', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-15'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-15'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-10'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Sur'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Merlot'],
            'harvest_mass_kg': [1500, 1500, 2000],
            'sample_date': ['2023-03-12', '2023-03-15', '2023-03-17'],
            'density': [1.090, 1.085, 1.095],
            'temperature_celsius': [18, 19, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert result.total_rows == 3
        assert result.fermentations_created == 2
        assert result.samples_created == 6  # 3 rows * 2 samples each
        assert isinstance(result.duration_seconds, float)
    
    @pytest.mark.asyncio
    async def test_handles_missing_vineyard_name_with_default(self, etl_service, mock_fruit_origin_service, tmp_path):
        """ETL should use 'UNKNOWN' as default when vineyard_name is missing."""
        excel_file = tmp_path / "missing_vineyard.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            # vineyard_name MISSING - should default to "UNKNOWN"
            'grape_variety': ['Cabernet'],
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-12'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert result.success
        # Verify FruitOriginService was called with None vineyard_name
        call_args = mock_fruit_origin_service.ensure_harvest_lot_for_import.call_args
        assert call_args.kwargs['vineyard_name'] is None
    
    @pytest.mark.asyncio
    async def test_handles_empty_vineyard_name_with_default(self, etl_service, mock_fruit_origin_service, tmp_path):
        """ETL should pass None vineyard_name to FruitOriginService when empty/whitespace."""
        excel_file = tmp_path / "empty_vineyard.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['  '],  # Empty/whitespace - should pass None
            'grape_variety': ['Cabernet'],
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-12'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert result.success
        # Verify FruitOriginService was called with None vineyard_name
        call_args = mock_fruit_origin_service.ensure_harvest_lot_for_import.call_args
        assert call_args.kwargs['vineyard_name'] is None
    
    @pytest.mark.asyncio
    async def test_handles_missing_grape_variety_with_default(self, etl_service, mock_fruit_origin_service, tmp_path):
        """ETL should pass None grape_variety to FruitOriginService when missing."""
        excel_file = tmp_path / "missing_variety.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            # grape_variety MISSING - should pass None
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-12'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert result.success
        # Verify FruitOriginService was called with None grape_variety
        call_args = mock_fruit_origin_service.ensure_harvest_lot_for_import.call_args
        assert call_args.kwargs['grape_variety'] is None
    
    @pytest.mark.asyncio
    async def test_handles_both_vineyard_and_variety_missing(self, etl_service, mock_fruit_origin_service, tmp_path):
        """ETL should pass None for both vineyard_name and grape_variety when missing."""
        excel_file = tmp_path / "missing_both.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            # vineyard_name MISSING
            # grape_variety MISSING
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-12'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert result.success
        # Verify FruitOriginService was called with None for both
        call_args = mock_fruit_origin_service.ensure_harvest_lot_for_import.call_args
        assert call_args.kwargs['vineyard_name'] is None
        assert call_args.kwargs['grape_variety'] is None
    
    @pytest.mark.asyncio
    async def test_uses_provided_winery_and_user_id(self, etl_service, mock_fruit_origin_service, tmp_path):
        """ETL should pass winery_id and user_id from parameters to services."""
        excel_file = tmp_path / "winery_user_test.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            'grape_variety': ['Cabernet'],
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-12'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        # Import with specific winery_id=5 and user_id=10
        result = await etl_service.import_file(excel_file, winery_id=5, user_id=10)
        
        assert result.success
        
        # Verify winery_id=5 was passed to FruitOriginService
        call_args = mock_fruit_origin_service.ensure_harvest_lot_for_import.call_args
        assert call_args.kwargs['winery_id'] == 5
    
    @pytest.mark.asyncio
    async def test_partial_success_one_fermentation_fails(self, mock_session_manager, mock_fruit_origin_service, mock_fermentation_repo, mock_sample_repo, mock_lot_source_repo, tmp_path):
        """ETL should save successful fermentations even when one fails (partial success)."""
        # Setup: First fermentation succeeds, second fails
        call_count = [0]
        
        async def ensure_harvest_lot_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call succeeds
                mock_lot = Mock()
                mock_lot.id = 1
                mock_lot.code = "LOT-1"
                return mock_lot
            else:
                # Second call fails
                raise Exception("Harvest lot creation failed")
        
        mock_fruit_origin_service.ensure_harvest_lot_for_import = AsyncMock(side_effect=ensure_harvest_lot_side_effect)
        
        # Create patchers for repositories
        with patch('src.modules.fermentation.src.service_component.etl.etl_service.FermentationRepository', return_value=mock_fermentation_repo), \
             patch('src.modules.fermentation.src.service_component.etl.etl_service.SampleRepository', return_value=mock_sample_repo), \
             patch('src.modules.fermentation.src.service_component.etl.etl_service.LotSourceRepository', return_value=mock_lot_source_repo):
            
            etl_service = ETLService(session_manager=mock_session_manager, fruit_origin_service=mock_fruit_origin_service)
            
            excel_file = tmp_path / "partial_success.xlsx"
            df = pd.DataFrame({
                'fermentation_code': ['FERM-001', 'FERM-001', 'FERM-002', 'FERM-002'],
                'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-15', '2023-03-15'],
                'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-15', '2023-04-15'],
                'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-10', '2023-03-10'],
                'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Sur', 'Viña Sur'],
                'grape_variety': ['Cabernet', 'Cabernet', 'Merlot', 'Merlot'],
                'harvest_mass_kg': [1500, 1500, 2000, 2000],
                'sample_date': ['2023-03-12', '2023-03-15', '2023-03-17', '2023-03-20'],
                'density': [1.090, 1.085, 1.095, 1.090],
                'temperature_celsius': [18, 19, 18, 19]
            })
            df.to_excel(excel_file, index=False, engine='openpyxl')
            
            result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
            
            # Should be successful (partial success)
            assert result.success
            assert result.fermentations_created == 1  # Only first fermentation
            assert result.samples_created == 4  # 2 rows * 2 samples
            assert len(result.failed_fermentations) == 1
            assert result.failed_fermentations[0]['code'] == 'FERM-002'
            assert 'Harvest lot creation failed' in result.failed_fermentations[0]['error']
    
    @pytest.mark.asyncio
    async def test_partial_success_all_fermentations_fail(self, mock_session_manager, mock_fruit_origin_service, mock_fermentation_repo, mock_sample_repo, mock_lot_source_repo, tmp_path):
        """ETL should track all failures when all fermentations fail."""
        # Setup: All calls fail
        mock_fruit_origin_service.ensure_harvest_lot_for_import = AsyncMock(side_effect=Exception("Service error"))
        
        # Create patchers for repositories
        with patch('src.modules.fermentation.src.service_component.etl.etl_service.FermentationRepository', return_value=mock_fermentation_repo), \
             patch('src.modules.fermentation.src.service_component.etl.etl_service.SampleRepository', return_value=mock_sample_repo), \
             patch('src.modules.fermentation.src.service_component.etl.etl_service.LotSourceRepository', return_value=mock_lot_source_repo):
            
            etl_service = ETLService(session_manager=mock_session_manager, fruit_origin_service=mock_fruit_origin_service)
        
        excel_file = tmp_path / "all_fail.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-15'],
            'fermentation_end_date': ['2023-04-10', '2023-04-15'],
            'harvest_date': ['2023-03-05', '2023-03-10'],
            'vineyard_name': ['Viña Norte', 'Viña Sur'],
            'grape_variety': ['Cabernet', 'Merlot'],
            'harvest_mass_kg': [1500, 2000],
            'sample_date': ['2023-03-12', '2023-03-17'],
            'density': [1.090, 1.095],
            'temperature_celsius': [18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        # Should fail (no fermentations succeeded)
        assert not result.success
        assert result.fermentations_created == 0
        assert result.samples_created == 0
        assert len(result.failed_fermentations) == 2
        assert result.failed_fermentations[0]['code'] == 'FERM-001'
        assert result.failed_fermentations[1]['code'] == 'FERM-002'
    
    @pytest.mark.asyncio
    async def test_partial_success_fermentation_create_fails(self, etl_service, tmp_path):
        """ETL should handle failure during fermentation creation (after harvest lot)."""
        # Setup: First fermentation creation succeeds, second fails
        call_count = [0]
        
        async def create_fermentation_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                mock_ferm = Mock()
                mock_ferm.id = "ferm-001"
                return mock_ferm
            else:
                raise Exception("Fermentation creation failed")
        
        etl_service._mock_fermentation_repo.create = AsyncMock(side_effect=create_fermentation_side_effect)
        
        excel_file = tmp_path / "ferm_fail.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-15'],
            'fermentation_end_date': ['2023-04-10', '2023-04-15'],
            'harvest_date': ['2023-03-05', '2023-03-10'],
            'vineyard_name': ['Viña Norte', 'Viña Sur'],
            'grape_variety': ['Cabernet', 'Merlot'],
            'harvest_mass_kg': [1500, 2000],
            'sample_date': ['2023-03-12', '2023-03-17'],
            'density': [1.090, 1.095],
            'temperature_celsius': [18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        # Should be successful (partial)
        assert result.success
        assert result.fermentations_created == 1
        assert len(result.failed_fermentations) == 1
        assert result.failed_fermentations[0]['code'] == 'FERM-002'
    
    @pytest.mark.asyncio
    async def test_progress_callback_invoked_per_fermentation(self, etl_service, tmp_path):
        """Progress callback should be invoked after each fermentation with current/total."""
        # Create file with 3 fermentations
        excel_file = tmp_path / "test_progress.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Sur', 'Viña Este'],
            'grape_variety': ['Cabernet', 'Merlot', 'Syrah'],
            'harvest_mass_kg': [1500, 1200, 1800],
            'sample_date': ['2023-03-12', '2023-03-12', '2023-03-12'],
            'density': [1.090, 1.092, 1.088],
            'temperature_celsius': [18, 19, 17]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        # Track progress callback invocations
        progress_calls = []
        
        async def progress_callback(current: int, total: int):
            progress_calls.append({'current': current, 'total': total})
        
        result = await etl_service.import_file(
            excel_file, 
            winery_id=1, 
            user_id=1,
            progress_callback=progress_callback
        )
        
        # Should have called progress 3 times (once per fermentation)
        assert len(progress_calls) == 3
        assert progress_calls[0] == {'current': 1, 'total': 3}
        assert progress_calls[1] == {'current': 2, 'total': 3}
        assert progress_calls[2] == {'current': 3, 'total': 3}
        assert result.success
        assert result.fermentations_created == 3
    
    @pytest.mark.asyncio
    async def test_cancellation_stops_import_gracefully(self, etl_service, tmp_path):
        """CancellationToken should stop import and return partial results."""
        from src.modules.fermentation.src.service_component.etl.cancellation_token import (
            CancellationToken,
            ImportCancelledException
        )
        
        # Create file with 5 fermentations
        excel_file = tmp_path / "test_cancel.xlsx"
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
        
        # Create cancellation token
        cancellation_token = CancellationToken()
        
        # Cancel after 2 fermentations
        progress_count = 0
        async def progress_callback(current: int, total: int):
            nonlocal progress_count
            progress_count += 1
            if progress_count == 2:
                await cancellation_token.cancel()
        
        # Import should raise ImportCancelledException
        with pytest.raises(ImportCancelledException) as exc_info:
            await etl_service.import_file(
                excel_file,
                winery_id=1,
                user_id=1,
                progress_callback=progress_callback,
                cancellation_token=cancellation_token
            )
        
        # Check exception details
        assert exc_info.value.imported == 2
        assert exc_info.value.total == 5
        assert "cancelled after 2/5" in str(exc_info.value).lower()
        
        # Verify 2 fermentations were committed (partial success)
        assert etl_service._mock_session_manager.commit.call_count == 2
    
    @pytest.mark.asyncio
    async def test_cancellation_without_callback_still_works(self, etl_service, tmp_path):
        """CancellationToken should work even without progress_callback."""
        from src.modules.fermentation.src.service_component.etl.cancellation_token import (
            CancellationToken,
            ImportCancelledException
        )
        
        excel_file = tmp_path / "test_cancel_no_callback.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003'],
            'fermentation_start_date': ['2023-03-10'] * 3,
            'fermentation_end_date': ['2023-04-10'] * 3,
            'harvest_date': ['2023-03-05'] * 3,
            'vineyard_name': ['Viña Norte'] * 3,
            'grape_variety': ['Cabernet'] * 3,
            'harvest_mass_kg': [1500] * 3,
            'sample_date': ['2023-03-12'] * 3,
            'density': [1.090] * 3,
            'temperature_celsius': [18] * 3
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        # Pre-cancel the token
        cancellation_token = CancellationToken()
        await cancellation_token.cancel()
        
        # Import should raise immediately (before first fermentation)
        with pytest.raises(ImportCancelledException) as exc_info:
            await etl_service.import_file(
                excel_file,
                winery_id=1,
                user_id=1,
                cancellation_token=cancellation_token
            )
        
        # Should be cancelled at start (0 imported)
        assert exc_info.value.imported == 0
        assert exc_info.value.total == 3
        
        # No commits should have happened
        assert etl_service._mock_session_manager.commit.call_count == 0
    
    @pytest.mark.asyncio
    async def test_progress_callback_with_async_operations(self, etl_service, tmp_path):
        """Progress callback should handle async operations correctly."""
        excel_file = tmp_path / "test_async_callback.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Sur'],
            'grape_variety': ['Cabernet', 'Merlot'],
            'harvest_mass_kg': [1500, 1200],
            'sample_date': ['2023-03-12', '2023-03-12'],
            'density': [1.090, 1.092],
            'temperature_celsius': [18, 19]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        # Async callback that performs some work
        callback_executions = []
        async def async_progress_callback(current: int, total: int):
            # Simulate async work (e.g., updating database, sending websocket message)
            import asyncio
            await asyncio.sleep(0.01)
            callback_executions.append({'current': current, 'total': total})
        
        result = await etl_service.import_file(
            excel_file,
            winery_id=1,
            user_id=1,
            progress_callback=async_progress_callback
        )
        
        # Should have executed async callback twice
        assert len(callback_executions) == 2
        assert callback_executions[0] == {'current': 1, 'total': 2}
        assert callback_executions[1] == {'current': 2, 'total': 2}
        assert result.success
