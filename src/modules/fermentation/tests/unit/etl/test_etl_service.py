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
from datetime import datetime

from src.modules.fermentation.src.service_component.etl.etl_service import ETLService, ImportResult
from src.modules.fermentation.src.domain.enums.data_source import DataSource


class TestETLService:
    """Test suite for ETL Service orchestration."""
    
    @pytest.fixture(autouse=True)
    def patch_entities(self, monkeypatch):
        """Patch entity classes to avoid SQLAlchemy initialization in unit tests."""
        # Mock Fermentation
        mock_ferm = MagicMock()
        mock_ferm_instance = MagicMock()
        mock_ferm_instance.id = "test-ferm-id-123"
        mock_ferm.return_value = mock_ferm_instance
        
        # Mock samples
        mock_density = MagicMock()
        mock_temp = MagicMock()
        mock_sugar = MagicMock()
        
        # Mock FermentationLotSource
        mock_lot_source = MagicMock()
        
        # Apply patches
        monkeypatch.setattr('src.modules.fermentation.src.service_component.etl.etl_service.Fermentation', mock_ferm)
        monkeypatch.setattr('src.modules.fermentation.src.service_component.etl.etl_service.DensitySample', mock_density)
        monkeypatch.setattr('src.modules.fermentation.src.service_component.etl.etl_service.CelsiusTemperatureSample', mock_temp)
        monkeypatch.setattr('src.modules.fermentation.src.service_component.etl.etl_service.SugarSample', mock_sugar)
        monkeypatch.setattr('src.modules.fermentation.src.service_component.etl.etl_service.FermentationLotSource', mock_lot_source)
    
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
    def mock_uow(
        self, 
        mock_fermentation_repo, 
        mock_sample_repo,
        mock_vineyard_repo,
        mock_vineyard_block_repo,
        mock_harvest_lot_repo,
        mock_lot_source_repo
    ):
        """Mock unit of work."""
        uow = Mock()
        uow.fermentation_repo = mock_fermentation_repo
        uow.sample_repo = mock_sample_repo
        uow.vineyard_repo = mock_vineyard_repo
        uow.vineyard_block_repo = mock_vineyard_block_repo
        uow.harvest_lot_repo = mock_harvest_lot_repo
        uow.lot_source_repo = mock_lot_source_repo
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.commit = AsyncMock()
        uow.rollback = AsyncMock()
        return uow
    
    @pytest.fixture
    def etl_service(self, mock_uow):
        """Create ETL service with mocked dependencies."""
        return ETLService(unit_of_work=mock_uow)
    
    @pytest.mark.asyncio
    async def test_rejects_file_failing_pre_validation(self, etl_service, tmp_path):
        """ETL should reject files that fail pre-validation."""
        # Create file with missing columns
        excel_file = tmp_path / "invalid_columns.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'vineyard_name': ['Viña Norte']
            # Missing required columns
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert not result.success
        assert result.phase_failed == 'pre_validation'
        assert len(result.errors) > 0
        assert result.fermentations_created == 0
        assert result.samples_created == 0
    
    @pytest.mark.asyncio
    async def test_rejects_file_failing_row_validation(self, etl_service, tmp_path):
        """ETL should reject files that fail row-validation."""
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
    async def test_imports_valid_single_fermentation_with_samples(self, etl_service, mock_uow, tmp_path):
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
        assert mock_uow.commit.called
    
    @pytest.mark.asyncio
    async def test_imports_multiple_fermentations(self, etl_service, mock_uow, tmp_path):
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
    async def test_calls_repository_create_methods(self, etl_service, mock_uow, tmp_path):
        """ETL should call repository create methods for all entities (vineyard, block, harvest lot, fermentation, lot source, samples)."""
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
        
        # Verify all repositories were called
        assert result.success
        
        # Fruit origin entities
        assert mock_uow.vineyard_repo.get_by_code.called
        assert mock_uow.vineyard_repo.create.called
        assert mock_uow.vineyard_block_repo.create.called
        assert mock_uow.harvest_lot_repo.create.called
        
        # Fermentation entities
        assert mock_uow.fermentation_repo.create.called
        assert mock_uow.lot_source_repo.create.called
        assert mock_uow.sample_repo.create.called
        
        # Verify correct number of calls
        assert mock_uow.vineyard_repo.create.call_count == 1
        assert mock_uow.vineyard_block_repo.create.call_count == 1
        assert mock_uow.harvest_lot_repo.create.call_count == 1
        assert mock_uow.fermentation_repo.create.call_count == 1
        assert mock_uow.lot_source_repo.create.call_count == 1
        assert mock_uow.sample_repo.create.call_count == 2  # density + temperature
    
    @pytest.mark.asyncio
    async def test_handles_optional_sugar_brix(self, etl_service, mock_uow, tmp_path):
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
        assert mock_uow.sample_repo.create.call_count == 6
    
    @pytest.mark.asyncio
    async def test_handles_duplicate_vessel_codes_via_database_constraint(self, etl_service, mock_uow, tmp_path):
        """ETL should handle duplicate vessel codes when database constraint is violated."""
        # Make repository raise constraint error on create
        mock_uow.fermentation_repo.create.side_effect = Exception("UNIQUE constraint failed")
        
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
    async def test_rollback_on_database_error(self, etl_service, mock_uow, tmp_path):
        """ETL should rollback transaction if database error occurs."""
        # Make repository raise error on create
        mock_uow.fermentation_repo.create.side_effect = Exception("Database error")
        
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
        
        assert not result.success
        assert mock_uow.rollback.called
        assert not mock_uow.commit.called
    
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
    async def test_reuses_existing_vineyard_for_multiple_fermentations(self, mock_uow, tmp_path):
        """ETL should reuse existing vineyard when importing multiple fermentations from same vineyard."""
        # Setup: First call to get_by_code returns None (create new), subsequent calls return existing
        call_count = [0]
        mock_vineyard = Mock()
        mock_vineyard.id = 1
        mock_vineyard.code = "Viña Norte"
        
        async def get_by_code_side_effect(code, winery_id):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # First vineyard doesn't exist
            else:
                return mock_vineyard  # Subsequent calls find existing vineyard
        
        mock_uow.vineyard_repo.get_by_code = AsyncMock(side_effect=get_by_code_side_effect)
        mock_uow.vineyard_repo.create = AsyncMock(return_value=mock_vineyard)
        
        etl_service = ETLService(unit_of_work=mock_uow)
        
        excel_file = tmp_path / "same_vineyard.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-15'],
            'fermentation_end_date': ['2023-04-10', '2023-04-15'],
            'harvest_date': ['2023-03-05', '2023-03-10'],
            'vineyard_name': ['Viña Norte', 'Viña Norte'],  # Same vineyard
            'grape_variety': ['Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 2000],
            'sample_date': ['2023-03-12', '2023-03-17'],
            'density': [1.090, 1.095],
            'temperature_celsius': [18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert result.success
        # Vineyard should only be created once
        assert mock_uow.vineyard_repo.create.call_count == 1
        # But get_by_code should be called twice (once per fermentation)
        assert mock_uow.vineyard_repo.get_by_code.call_count == 2
    
    @pytest.mark.asyncio
    async def test_handles_missing_vineyard_name_with_default(self, mock_uow, tmp_path):
        """ETL should use 'UNKNOWN' as default when vineyard_name is missing."""
        etl_service = ETLService(unit_of_work=mock_uow)
        
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
        # Verify vineyard was created/searched with "UNKNOWN" name
        mock_uow.vineyard_repo.get_by_code.assert_called_once_with("UNKNOWN", 1)
    
    @pytest.mark.asyncio
    async def test_handles_empty_vineyard_name_with_default(self, mock_uow, tmp_path):
        """ETL should use 'UNKNOWN' as default when vineyard_name is empty string."""
        etl_service = ETLService(unit_of_work=mock_uow)
        
        excel_file = tmp_path / "empty_vineyard.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['  '],  # Empty/whitespace - should default to "UNKNOWN"
            'grape_variety': ['Cabernet'],
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-12'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert result.success
        # Verify vineyard was created/searched with "UNKNOWN" name
        mock_uow.vineyard_repo.get_by_code.assert_called_once_with("UNKNOWN", 1)
    
    @pytest.mark.asyncio
    async def test_handles_missing_grape_variety_with_default(self, mock_uow, tmp_path):
        """ETL should use 'Unknown' as default when grape_variety is missing."""
        etl_service = ETLService(unit_of_work=mock_uow)
        
        excel_file = tmp_path / "missing_variety.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            # grape_variety MISSING - should default to "Unknown"
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-12'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        result = await etl_service.import_file(excel_file, winery_id=1, user_id=1)
        
        assert result.success
        # Verify HarvestLot was created with "Unknown" grape_variety
        call_args = mock_uow.harvest_lot_repo.create.call_args
        assert call_args is not None
        harvest_lot_dto = call_args[0][1]  # Second positional arg is the DTO
        assert harvest_lot_dto.grape_variety == "Unknown"
    
    @pytest.mark.asyncio
    async def test_handles_both_vineyard_and_variety_missing(self, mock_uow, tmp_path):
        """ETL should handle when both vineyard_name and grape_variety are missing."""
        etl_service = ETLService(unit_of_work=mock_uow)
        
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
        # Verify defaults were used
        mock_uow.vineyard_repo.get_by_code.assert_called_once_with("UNKNOWN", 1)
        call_args = mock_uow.harvest_lot_repo.create.call_args
        assert call_args is not None
        harvest_lot_dto = call_args[0][1]
        assert harvest_lot_dto.grape_variety == "Unknown"
    
    @pytest.mark.asyncio
    async def test_uses_provided_winery_and_user_id(self, mock_uow, tmp_path):
        """ETL should use winery_id and user_id from parameters, not hardcoded values."""
        etl_service = ETLService(unit_of_work=mock_uow)
        
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
        
        # Verify winery_id=5 was used in repository calls
        mock_uow.vineyard_repo.get_by_code.assert_called_with("Viña Norte", 5)
        
        # Verify vineyard creation used winery_id=5
        if mock_uow.vineyard_repo.create.called:
            call_args = mock_uow.vineyard_repo.create.call_args
            assert call_args[0][0] == 5  # First arg is winery_id
        
        # Verify VineyardBlock creation used winery_id=5
        call_args = mock_uow.vineyard_block_repo.create.call_args
        assert call_args[0][1] == 5  # Second arg is winery_id
        
        # Verify HarvestLot creation used winery_id=5
        call_args = mock_uow.harvest_lot_repo.create.call_args
        assert call_args[0][0] == 5  # First arg is winery_id


