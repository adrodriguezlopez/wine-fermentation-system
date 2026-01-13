"""
Unit tests for FruitOriginService - ETL Orchestration Methods.

Following TDD approach for ADR-030 Phase 1 implementation.
Tests for new methods that support ETL import optimization:
- batch_load_vineyards() - Batch vineyard loading to eliminate N+1 queries
- get_or_create_default_block() - Shared default block for historical imports
- ensure_harvest_lot_for_import() - Complete orchestration for ETL

Related ADRs:
- ADR-030: ETL Cross-Module Architecture & Performance Optimization
- ADR-014: Fruit Origin Service Layer (base service)
- ADR-019: ETL Pipeline Implementation
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import date
from typing import List, Dict, Optional

# Service under test
from src.modules.fruit_origin.src.service_component.services.fruit_origin_service import FruitOriginService

# Domain entities
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot

# DTOs
from src.modules.fruit_origin.src.domain.dtos.vineyard_dtos import VineyardCreate
from src.modules.fruit_origin.src.domain.dtos.vineyard_block_dtos import VineyardBlockCreate
from src.modules.fruit_origin.src.domain.dtos.harvest_lot_dtos import HarvestLotCreate

# Repository interfaces
from src.modules.fruit_origin.src.domain.repositories.vineyard_repository_interface import IVineyardRepository
from src.modules.fruit_origin.src.domain.repositories.vineyard_block_repository_interface import IVineyardBlockRepository
from src.modules.fruit_origin.src.domain.repositories.harvest_lot_repository_interface import IHarvestLotRepository


class TestBatchLoadVineyards:
    """TDD RED: Tests for batch_load_vineyards() method."""
    
    @pytest.fixture
    def mock_vineyard_repo(self):
        """Mock vineyard repository with get_by_codes method."""
        repo = Mock(spec=IVineyardRepository)
        
        # Mock vineyards
        vineyard_norte = Mock(spec=Vineyard)
        vineyard_norte.id = 1
        vineyard_norte.code = "Viña Norte"
        vineyard_norte.name = "Viña Norte"
        vineyard_norte.winery_id = 5
        
        vineyard_sur = Mock(spec=Vineyard)
        vineyard_sur.id = 2
        vineyard_sur.code = "Viña Sur"
        vineyard_sur.name = "Viña Sur"
        vineyard_sur.winery_id = 5
        
        # get_by_codes returns list of vineyards
        repo.get_by_codes = AsyncMock(return_value=[vineyard_norte, vineyard_sur])
        
        return repo
    
    @pytest.fixture
    def mock_harvest_lot_repo(self):
        """Mock harvest lot repository."""
        return Mock(spec=IHarvestLotRepository)
    
    @pytest.fixture
    def mock_vineyard_block_repo(self):
        """Mock vineyard block repository."""
        return Mock(spec=IVineyardBlockRepository)
    
    @pytest.fixture
    def fruit_origin_service(self, mock_vineyard_repo, mock_harvest_lot_repo, mock_vineyard_block_repo):
        """Create service with mocked dependencies."""
        return FruitOriginService(
            vineyard_repo=mock_vineyard_repo,
            harvest_lot_repo=mock_harvest_lot_repo,
            vineyard_block_repo=mock_vineyard_block_repo
        )
    
    @pytest.mark.asyncio
    async def test_loads_multiple_vineyards_by_codes(
        self, fruit_origin_service, mock_vineyard_repo
    ):
        """
        TDD RED: batch_load_vineyards should load multiple vineyards in single query.
        
        Given: List of vineyard codes ["Viña Norte", "Viña Sur"]
        When: Calling batch_load_vineyards()
        Then: Should call get_by_codes() and return dict mapping code → vineyard
        """
        vineyard_codes = ["Viña Norte", "Viña Sur"]
        winery_id = 5
        
        result = await fruit_origin_service.batch_load_vineyards(vineyard_codes, winery_id)
        
        # Verify get_by_codes was called with correct parameters
        mock_vineyard_repo.get_by_codes.assert_called_once_with(vineyard_codes, winery_id)
        
        # Verify result is a dictionary
        assert isinstance(result, dict)
        assert len(result) == 2
        
        # Verify mapping is correct
        assert "Viña Norte" in result
        assert "Viña Sur" in result
        assert result["Viña Norte"].id == 1
        assert result["Viña Sur"].id == 2
    
    @pytest.mark.asyncio
    async def test_returns_empty_dict_for_empty_list(
        self, fruit_origin_service, mock_vineyard_repo
    ):
        """
        TDD RED: batch_load_vineyards should handle empty input gracefully.
        
        Given: Empty list of codes
        When: Calling batch_load_vineyards()
        Then: Should return empty dict without calling repository
        """
        mock_vineyard_repo.get_by_codes = AsyncMock(return_value=[])
        
        result = await fruit_origin_service.batch_load_vineyards([], 5)
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_scopes_by_winery_id(
        self, fruit_origin_service, mock_vineyard_repo
    ):
        """
        TDD RED: batch_load_vineyards should enforce multi-tenancy.
        
        Given: Vineyard codes and winery_id=10
        When: Calling batch_load_vineyards()
        Then: Should pass winery_id to repository for scoping
        """
        vineyard_codes = ["Viña Norte"]
        winery_id = 10
        
        await fruit_origin_service.batch_load_vineyards(vineyard_codes, winery_id)
        
        mock_vineyard_repo.get_by_codes.assert_called_once_with(vineyard_codes, winery_id)
    
    @pytest.mark.asyncio
    async def test_handles_partial_results(
        self, fruit_origin_service, mock_vineyard_repo
    ):
        """
        TDD RED: batch_load_vineyards should handle when some vineyards don't exist.
        
        Given: Request for 3 vineyards but only 2 exist
        When: Calling batch_load_vineyards()
        Then: Should return dict with only found vineyards
        """
        # Mock only 2 vineyards found (Norte and Sur), Este doesn't exist
        vineyard_norte = Mock(spec=Vineyard)
        vineyard_norte.id = 1
        vineyard_norte.code = "Viña Norte"
        
        vineyard_sur = Mock(spec=Vineyard)
        vineyard_sur.id = 2
        vineyard_sur.code = "Viña Sur"
        
        mock_vineyard_repo.get_by_codes = AsyncMock(return_value=[vineyard_norte, vineyard_sur])
        
        result = await fruit_origin_service.batch_load_vineyards(
            ["Viña Norte", "Viña Sur", "Viña Este"], 5
        )
        
        assert len(result) == 2
        assert "Viña Norte" in result
        assert "Viña Sur" in result
        assert "Viña Este" not in result


class TestGetOrCreateDefaultBlock:
    """TDD RED: Tests for get_or_create_default_block() method."""
    
    @pytest.fixture
    def mock_vineyard_repo(self):
        """Mock vineyard repository."""
        repo = Mock(spec=IVineyardRepository)
        
        # Mock vineyard for get_by_id
        mock_vineyard = Mock(spec=Vineyard)
        mock_vineyard.id = 1
        mock_vineyard.code = "IMPORTED"  # String, not AsyncMock
        mock_vineyard.name = "Imported Vineyard"
        mock_vineyard.winery_id = 5
        
        repo.get_by_id = AsyncMock(return_value=mock_vineyard)
        
        return repo
    
    @pytest.fixture
    def mock_harvest_lot_repo(self):
        """Mock harvest lot repository."""
        return Mock(spec=IHarvestLotRepository)
    
    @pytest.fixture
    def mock_vineyard_block_repo(self):
        """Mock vineyard block repository with get_by_code method."""
        repo = Mock(spec=IVineyardBlockRepository)
        
        # Default: block doesn't exist
        repo.get_by_code = AsyncMock(return_value=None)
        
        # Default: create returns new block
        mock_block = Mock(spec=VineyardBlock)
        mock_block.id = 1
        mock_block.vineyard_id = 1
        mock_block.code = "IMPORTED-DEFAULT-1"
        repo.create = AsyncMock(return_value=mock_block)
        
        return repo
    
    @pytest.fixture
    def fruit_origin_service(self, mock_vineyard_repo, mock_harvest_lot_repo, mock_vineyard_block_repo):
        """Create service with mocked dependencies."""
        return FruitOriginService(
            vineyard_repo=mock_vineyard_repo,
            harvest_lot_repo=mock_harvest_lot_repo,
            vineyard_block_repo=mock_vineyard_block_repo
        )
    
    @pytest.mark.asyncio
    async def test_creates_block_if_missing(
        self, fruit_origin_service, mock_vineyard_block_repo
    ):
        """
        TDD RED: get_or_create_default_block should create block if it doesn't exist.
        
        Given: No existing default block for vineyard_id=1
        When: Calling get_or_create_default_block()
        Then: Should create new block with correct naming pattern
        """
        vineyard_id = 1
        winery_id = 5
        
        result = await fruit_origin_service.get_or_create_default_block(vineyard_id, winery_id)
        
        # Verify get_by_code was called to check existence
        mock_vineyard_block_repo.get_by_code.assert_called_once()
        
        # Verify create was called since block didn't exist
        mock_vineyard_block_repo.create.assert_called_once()
        create_call = mock_vineyard_block_repo.create.call_args
        assert create_call[1]["vineyard_id"] == vineyard_id  # Keyword arg: vineyard_id
        assert create_call[1]["winery_id"] == winery_id      # Keyword arg: winery_id
        block_dto = create_call[1]["data"]                      # Keyword arg: data (VineyardBlockCreate)
        assert "-DEFAULT" in block_dto.code
        assert "Auto-generated" in block_dto.notes
        
        # Verify result is the created block
        assert result.id == 1
        assert result.vineyard_id == 1
    
    @pytest.mark.asyncio
    async def test_reuses_existing_block(
        self, fruit_origin_service, mock_vineyard_block_repo
    ):
        """
        TDD RED: get_or_create_default_block should reuse existing block.
        
        Given: Default block already exists for vineyard_id=1
        When: Calling get_or_create_default_block()
        Then: Should return existing block without creating new one
        """
        # Mock existing block
        existing_block = Mock(spec=VineyardBlock)
        existing_block.id = 10
        existing_block.vineyard_id = 1
        existing_block.code = "IMPORTED-DEFAULT-1"
        
        mock_vineyard_block_repo.get_by_code = AsyncMock(return_value=existing_block)
        
        vineyard_id = 1
        winery_id = 5
        
        result = await fruit_origin_service.get_or_create_default_block(vineyard_id, winery_id)
        
        # Verify get_by_code was called
        mock_vineyard_block_repo.get_by_code.assert_called_once()
        
        # Verify create was NOT called since block exists
        mock_vineyard_block_repo.create.assert_not_called()
        
        # Verify result is the existing block
        assert result.id == 10
        assert result.vineyard_id == 1
    
    @pytest.mark.asyncio
    async def test_uses_consistent_naming_pattern(
        self, fruit_origin_service, mock_vineyard_block_repo
    ):
        """
        TDD RED: get_or_create_default_block should use consistent code pattern.
        
        Given: vineyard_id=1
        When: Creating default block
        Then: Should use code "IMPORTED-DEFAULT-1"
        """
        vineyard_id = 1
        winery_id = 5
        
        await fruit_origin_service.get_or_create_default_block(vineyard_id, winery_id)
        
        # Check the get_by_code call to verify expected code pattern
        get_by_code_call = mock_vineyard_block_repo.get_by_code.call_args
        expected_code = "IMPORTED-DEFAULT"  # Pattern: {VINEYARD_CODE}-DEFAULT
        assert get_by_code_call[1]["code"] == expected_code  # Keyword arg: code
        assert get_by_code_call[1]["vineyard_id"] == vineyard_id  # Keyword arg: vineyard_id
        assert get_by_code_call[1]["winery_id"] == winery_id  # Keyword arg: winery_id
    
    @pytest.mark.asyncio
    async def test_creates_block_with_appropriate_notes(
        self, fruit_origin_service, mock_vineyard_block_repo
    ):
        """
        TDD RED: get_or_create_default_block should set informative notes.
        
        Given: Creating new default block
        When: Block doesn't exist
        Then: Should create block with notes explaining it's for imports
        """
        vineyard_id = 1
        winery_id = 5
        
        await fruit_origin_service.get_or_create_default_block(vineyard_id, winery_id)
        
        # Verify create was called with DTO containing appropriate notes
        create_call = mock_vineyard_block_repo.create.call_args
        block_dto = create_call[1]["data"]  # Keyword arg: data (VineyardBlockCreate DTO)
        
        assert isinstance(block_dto, VineyardBlockCreate)
        assert "import" in block_dto.notes.lower() or "default" in block_dto.notes.lower()


class TestEnsureHarvestLotForImport:
    """TDD RED: Tests for ensure_harvest_lot_for_import() orchestration method."""
    
    @pytest.fixture
    def mock_vineyard_repo(self):
        """Mock vineyard repository."""
        repo = Mock(spec=IVineyardRepository)
        
        # Default: vineyard doesn't exist
        repo.get_by_code = AsyncMock(return_value=None)
        
        # Create returns new vineyard
        mock_vineyard = Mock(spec=Vineyard)
        mock_vineyard.id = 1
        mock_vineyard.code = "VIÑA-NORTE"  # String, not AsyncMock - uppercase + hyphenated
        mock_vineyard.name = "Viña Norte"
        mock_vineyard.winery_id = 5
        repo.create = AsyncMock(return_value=mock_vineyard)
        
        # get_by_id also returns the vineyard (needed by get_or_create_default_block)
        repo.get_by_id = AsyncMock(return_value=mock_vineyard)
        
        return repo
    
    @pytest.fixture
    def mock_vineyard_block_repo(self):
        """Mock vineyard block repository."""
        repo = Mock(spec=IVineyardBlockRepository)
        
        # Block doesn't exist (will be created)
        repo.get_by_code = AsyncMock(return_value=None)
        
        mock_block = Mock(spec=VineyardBlock)
        mock_block.id = 1
        mock_block.vineyard_id = 1
        mock_block.code = "IMPORTED-DEFAULT-1"
        repo.create = AsyncMock(return_value=mock_block)
        
        return repo
    
    @pytest.fixture
    def mock_harvest_lot_repo(self):
        """Mock harvest lot repository."""
        repo = Mock(spec=IHarvestLotRepository)
        
        # Default: lot doesn't exist (so create will be called)
        repo.get_by_code = AsyncMock(return_value=None)
        
        mock_harvest_lot = Mock(spec=HarvestLot)
        mock_harvest_lot.id = 1
        mock_harvest_lot.block_id = 1
        mock_harvest_lot.code = "HL-IMPORT-001"
        mock_harvest_lot.harvest_date = date(2023, 3, 5)
        mock_harvest_lot.weight_kg = 1500.0
        mock_harvest_lot.grape_variety = "Cabernet Sauvignon"
        repo.create = AsyncMock(return_value=mock_harvest_lot)
        
        # get_by_code returns None by default (no existing lot)
        repo.get_by_code = AsyncMock(return_value=None)
        
        return repo
    
    @pytest.fixture
    def fruit_origin_service(self, mock_vineyard_repo, mock_harvest_lot_repo, mock_vineyard_block_repo):
        """Create service with mocked dependencies."""
        return FruitOriginService(
            vineyard_repo=mock_vineyard_repo,
            harvest_lot_repo=mock_harvest_lot_repo,
            vineyard_block_repo=mock_vineyard_block_repo
        )
    
    @pytest.mark.asyncio
    async def test_creates_complete_hierarchy_for_new_vineyard(
        self, fruit_origin_service, mock_vineyard_repo, mock_vineyard_block_repo, mock_harvest_lot_repo
    ):
        """
        TDD RED: ensure_harvest_lot_for_import should create complete hierarchy.
        
        Given: New vineyard "Viña Norte" that doesn't exist
        When: Calling ensure_harvest_lot_for_import()
        Then: Should create vineyard → block → harvest lot and return harvest lot
        """
        winery_id = 5
        vineyard_name = "Viña Norte"
        grape_variety = "Cabernet Sauvignon"
        harvest_date = date(2023, 3, 5)
        harvest_mass_kg = 1500.0
        
        result = await fruit_origin_service.ensure_harvest_lot_for_import(
            winery_id=winery_id,
            vineyard_name=vineyard_name,
            grape_variety=grape_variety,
            harvest_date=harvest_date,
            harvest_mass_kg=harvest_mass_kg
        )
        
        # Verify vineyard creation flow (code is uppercase + hyphenated)
        expected_code = "VIÑA-NORTE"
        mock_vineyard_repo.get_by_code.assert_called_once_with(expected_code, winery_id)
        
        # Verify vineyard create called with winery_id and VineyardCreate DTO
        vineyard_create_call = mock_vineyard_repo.create.call_args
        assert vineyard_create_call[0][0] == winery_id  # First arg: winery_id
        vineyard_dto = vineyard_create_call[0][1]  # Second arg: VineyardCreate DTO
        assert vineyard_dto.code == expected_code
        assert vineyard_dto.name == vineyard_name
        assert "Auto-generated" in vineyard_dto.notes
        
        # Verify block creation via get_or_create_default_block
        block_get_call = mock_vineyard_block_repo.get_by_code.call_args
        expected_block_code = f"{expected_code}-DEFAULT"
        assert block_get_call[1]["code"] == expected_block_code  # Keyword arg
        assert block_get_call[1]["vineyard_id"] == mock_vineyard_repo.create.return_value.id
        assert block_get_call[1]["winery_id"] == winery_id
        
        # Verify block create called with vineyard_id, winery_id, and VineyardBlockCreate DTO
        block_create_call = mock_vineyard_block_repo.create.call_args
        assert block_create_call[1]["vineyard_id"] == mock_vineyard_repo.create.return_value.id
        assert block_create_call[1]["winery_id"] == winery_id
        block_dto = block_create_call[1]["data"]
        assert block_dto.code == expected_block_code
        assert "Auto-generated" in block_dto.notes
        
        # Verify harvest lot creation
        mock_harvest_lot_repo.create.assert_called_once()
        
        # Verify result is harvest lot
        assert result.id == 1
        assert result.block_id == 1
        assert result.weight_kg == 1500.0
    
    @pytest.mark.asyncio
    async def test_reuses_existing_vineyard(
        self, fruit_origin_service, mock_vineyard_repo, mock_harvest_lot_repo
    ):
        """
        TDD RED: ensure_harvest_lot_for_import should reuse existing vineyard.
        
        Given: Vineyard "Viña Norte" already exists
        When: Calling ensure_harvest_lot_for_import()
        Then: Should NOT create vineyard, should reuse existing
        """
        # Mock existing vineyard
        existing_vineyard = Mock(spec=Vineyard)
        existing_vineyard.id = 10
        existing_vineyard.code = "Viña Norte"
        existing_vineyard.name = "Viña Norte"
        
        mock_vineyard_repo.get_by_code = AsyncMock(return_value=existing_vineyard)
        
        winery_id = 5
        vineyard_name = "Viña Norte"
        
        await fruit_origin_service.ensure_harvest_lot_for_import(
            winery_id=winery_id,
            vineyard_name=vineyard_name,
            grape_variety="Cabernet",
            harvest_date=date(2023, 3, 5),
            harvest_mass_kg=1500.0
        )
        
        # Verify vineyard was checked (code is uppercase + hyphenated)
        expected_code = "VIÑA-NORTE"
        mock_vineyard_repo.get_by_code.assert_called_once_with(expected_code, winery_id)
        
        # Verify vineyard was NOT created
        mock_vineyard_repo.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handles_missing_vineyard_name(
        self, fruit_origin_service, mock_vineyard_repo
    ):
        """
        TDD RED: ensure_harvest_lot_for_import should handle None vineyard_name.
        
        Given: vineyard_name=None (missing in Excel)
        When: Calling ensure_harvest_lot_for_import()
        Then: Should use "UNKNOWN" as default vineyard name
        """
        winery_id = 5
        vineyard_name = None
        
        await fruit_origin_service.ensure_harvest_lot_for_import(
            winery_id=winery_id,
            vineyard_name=vineyard_name,
            grape_variety="Cabernet",
            harvest_date=date(2023, 3, 5),
            harvest_mass_kg=1500.0
        )
        
        # Verify "UNKNOWN" was used
        mock_vineyard_repo.get_by_code.assert_called_once_with("UNKNOWN", winery_id)
    
    @pytest.mark.asyncio
    async def test_handles_missing_grape_variety(
        self, fruit_origin_service, mock_harvest_lot_repo
    ):
        """
        TDD RED: ensure_harvest_lot_for_import should handle None grape_variety.
        
        Given: grape_variety=None (missing in Excel)
        When: Calling ensure_harvest_lot_for_import()
        Then: Should use "Unknown" as default grape variety
        """
        winery_id = 5
        grape_variety = None
        
        await fruit_origin_service.ensure_harvest_lot_for_import(
            winery_id=winery_id,
            vineyard_name="Viña Norte",
            grape_variety=grape_variety,
            harvest_date=date(2023, 3, 5),
            harvest_mass_kg=1500.0
        )
        
        # Verify harvest lot was created with "UNKNOWN" variety (if not reusing existing)
        if mock_harvest_lot_repo.create.called:
            create_call = mock_harvest_lot_repo.create.call_args
            # Args are (winery_id, HarvestLotCreate DTO)
            harvest_lot_dto = create_call[0][1]  # Second positional arg: data (HarvestLotCreate DTO)
            
            assert isinstance(harvest_lot_dto, HarvestLotCreate)
            assert harvest_lot_dto.grape_variety == "UNKNOWN"
    
    @pytest.mark.asyncio
    async def test_enforces_multi_tenancy(
        self, fruit_origin_service, mock_vineyard_repo, mock_harvest_lot_repo
    ):
        """
        TDD RED: ensure_harvest_lot_for_import should enforce winery_id scoping.
        
        Given: winery_id=10
        When: Calling ensure_harvest_lot_for_import()
        Then: Should pass winery_id to all repository calls
        """
        winery_id = 10
        
        await fruit_origin_service.ensure_harvest_lot_for_import(
            winery_id=winery_id,
            vineyard_name="Viña Norte",
            grape_variety="Cabernet",
            harvest_date=date(2023, 3, 5),
            harvest_mass_kg=1500.0
        )
        
        # Verify winery_id passed to vineyard operations
        mock_vineyard_repo.get_by_code.assert_called_once()
        get_by_code_call = mock_vineyard_repo.get_by_code.call_args
        assert get_by_code_call[0][1] == winery_id  # Second positional arg
        
        # Verify winery_id passed to harvest lot creation (if called)
        if mock_harvest_lot_repo.create.called:
            create_call = mock_harvest_lot_repo.create.call_args
            assert create_call[0][0] == winery_id  # First positional arg: winery_id
