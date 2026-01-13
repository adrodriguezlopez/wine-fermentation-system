"""
Unit tests for HistoricalDataService.

Following TDD approach as documented in ADR-032.
Tests are written BEFORE implementation to drive design.

Test Strategy:
- 12 unit tests total (4 methods x 3 test cases each)
- Mock repositories to test service logic in isolation
- Test multi-tenant security (winery_id scoping)
- Test data source filtering (data_source='HISTORICAL')
- Test error handling (not found, unauthorized access)
"""

import pytest
from unittest.mock import Mock, create_autospec, AsyncMock, patch
from datetime import datetime, date
from typing import Optional, List, Dict, Any

# Service under test (will be implemented)
# from src.modules.fermentation.src.service_component.services.historical.historical_data_service import HistoricalDataService

# Repository interfaces
from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository

# Domain entities
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample

# Errors
from src.modules.fermentation.src.service_component.errors import NotFoundError


class TestGetHistoricalFermentations:
    """
    Test suite for HistoricalDataService.get_historical_fermentations()
    
    Business Rules (from ADR-032):
    - Must filter by data_source='HISTORICAL'
    - Must respect multi-tenant boundaries (winery_id)
    - Must support pagination (limit, offset)
    - Must support filtering (date_range, fruit_origin_id, status)
    - Returns list of Fermentation entities
    """
    
    @pytest.fixture
    def mock_fermentation_repo(self) -> Mock:
        """Mock repository for testing service logic in isolation."""
        repo = create_autospec(IFermentationRepository, instance=True)
        # Make async methods return AsyncMock
        repo.get_by_winery.return_value = []
        return repo
    
    @pytest.fixture
    def mock_sample_repo(self) -> Mock:
        """Mock sample repository."""
        return create_autospec(ISampleRepository, instance=True)
    
    @pytest.fixture
    def service(self, mock_fermentation_repo: Mock, mock_sample_repo: Mock):
        """Service instance with mocked dependencies."""
        # Import here to avoid import errors before implementation
        from src.modules.fermentation.src.service_component.services.historical.historical_data_service import HistoricalDataService
        return HistoricalDataService(
            fermentation_repo=mock_fermentation_repo,
            sample_repo=mock_sample_repo
        )
    
    @pytest.mark.asyncio
    async def test_get_historical_fermentations_returns_list_with_filters(
        self,
        service,
        mock_fermentation_repo: Mock
    ):
        """Test that service queries repository with correct filters."""
        # Arrange
        winery_id = 1
        filters = {
            "start_date_from": date(2024, 1, 1),
            "start_date_to": date(2024, 12, 31),
            "fruit_origin_id": 5,
            "status": "completed"
        }
        limit = 50
        offset = 0
        
        mock_fermentations = [
            Mock(spec=Fermentation, id=1, winery_id=winery_id, data_source="HISTORICAL", start_date=filters["start_date_from"], fruit_origin_id=filters["fruit_origin_id"], status=filters["status"]),
            Mock(spec=Fermentation, id=2, winery_id=winery_id, data_source="HISTORICAL", start_date=filters["start_date_to"], fruit_origin_id=filters["fruit_origin_id"], status=filters["status"]),
        ]
        mock_fermentation_repo.list_by_data_source.return_value = mock_fermentations
        
        # Act
        result = await service.get_historical_fermentations(
            winery_id=winery_id,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        # Assert
        assert len(result) == 2
        assert all(f.data_source == "HISTORICAL" for f in result)
        mock_fermentation_repo.list_by_data_source.assert_called_once_with(
            winery_id=winery_id,
            data_source="HISTORICAL",
            include_deleted=False
        )
    
    @pytest.mark.asyncio
    async def test_get_historical_fermentations_with_minimal_filters(
        self,
        service,
        mock_fermentation_repo: Mock
    ):
        """Test query with only required parameters (winery_id)."""
        # Arrange
        winery_id = 2
        mock_fermentation_repo.list_by_data_source.return_value = []
        
        # Act
        result = await service.get_historical_fermentations(
            winery_id=winery_id,
            filters={},
            limit=100,
            offset=0
        )
        
        # Assert
        assert result == []
        mock_fermentation_repo.list_by_data_source.assert_called_once_with(
            winery_id=winery_id,
            data_source="HISTORICAL",
            include_deleted=False
        )
    
    @pytest.mark.asyncio
    async def test_get_historical_fermentations_applies_pagination(
        self,
        service,
        mock_fermentation_repo: Mock
    ):
        """Test that pagination parameters are correctly passed."""
        # Arrange
        winery_id = 1
        limit = 10
        offset = 20
        
        # Create 100 mock fermentations as actual Python list (not Mock)
        all_fermentations = [Mock(spec=Fermentation, id=i, winery_id=winery_id, data_source="HISTORICAL") for i in range(1, 101)]
        mock_fermentation_repo.list_by_data_source.return_value = all_fermentations
        
        # Act
        result = await service.get_historical_fermentations(
            winery_id=winery_id,
            filters={},
            limit=limit,
            offset=offset
        )
        
        # Assert
        assert len(result) == 10
        # Check that we got fermentations 21-30 (offset=20, limit=10)
        assert result[0].id == 21
        assert result[9].id == 30
        mock_fermentation_repo.list_by_data_source.assert_called_once()


class TestGetHistoricalFermentationById:
    """
    Test suite for HistoricalDataService.get_historical_fermentation_by_id()
    
    Business Rules:
    - Must filter by data_source='HISTORICAL'
    - Must verify winery_id matches (multi-tenant security)
    - Returns single Fermentation entity
    - Raises NotFoundError if not found or wrong winery
    """
    
    @pytest.fixture
    def mock_fermentation_repo(self) -> Mock:
        """Mock repository."""
        return create_autospec(IFermentationRepository, instance=True)
    
    @pytest.fixture
    def mock_sample_repo(self) -> Mock:
        """Mock sample repository."""
        return create_autospec(ISampleRepository, instance=True)
    
    @pytest.fixture
    def service(self, mock_fermentation_repo: Mock, mock_sample_repo: Mock):
        """Service instance with mocked dependencies."""
        from src.modules.fermentation.src.service_component.services.historical.historical_data_service import HistoricalDataService
        return HistoricalDataService(
            fermentation_repo=mock_fermentation_repo,
            sample_repo=mock_sample_repo
        )
    
    @pytest.mark.asyncio
    async def test_get_by_id_returns_fermentation_when_found(
        self,
        service,
        mock_fermentation_repo: Mock
    ):
        """Test successful retrieval of historical fermentation."""
        # Arrange
        fermentation_id = 1
        winery_id = 1
        mock_fermentation = Mock(
            spec=Fermentation,
            id=fermentation_id,
            winery_id=winery_id,
            data_source="HISTORICAL"
        )
        mock_fermentation_repo.get_by_id.return_value = mock_fermentation
        
        # Act
        result = await service.get_historical_fermentation_by_id(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        # Assert
        assert result == mock_fermentation
        mock_fermentation_repo.get_by_id.assert_called_once_with(fermentation_id, winery_id)
    
    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found_when_fermentation_not_exists(
        self,
        service,
        mock_fermentation_repo: Mock
    ):
        """Test NotFoundError when fermentation doesn't exist."""
        # Arrange
        fermentation_id = 999
        winery_id = 1
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_historical_fermentation_by_id(
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
        
        assert "not found" in str(exc_info.value).lower()
        mock_fermentation_repo.get_by_id.assert_called_once_with(fermentation_id, winery_id)
    
    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found_when_wrong_winery(
        self,
        service,
        mock_fermentation_repo: Mock
    ):
        """Test NotFoundError when fermentation belongs to different winery (multi-tenant security)."""
        # Arrange
        fermentation_id = 1
        winery_id = 1
        
        # Repository should return None due to multi-tenant filtering
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_historical_fermentation_by_id(
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
        
        assert "not found" in str(exc_info.value).lower()


class TestGetFermentationSamples:
    """
    Test suite for HistoricalDataService.get_fermentation_samples()
    
    Business Rules:
    - Must verify fermentation exists and belongs to winery
    - Must filter samples by data_source='HISTORICAL'
    - Returns list of BaseSample entities (all sample types)
    - Raises NotFoundError if fermentation not found or wrong winery
    """
    
    @pytest.fixture
    def mock_fermentation_repo(self) -> Mock:
        """Mock repository."""
        return create_autospec(IFermentationRepository, instance=True)
    
    @pytest.fixture
    def mock_sample_repo(self) -> Mock:
        """Mock sample repository."""
        repo = create_autospec(ISampleRepository, instance=True)
        repo.get_samples_by_fermentation_id.return_value = []
        return repo
    
    @pytest.fixture
    def service(self, mock_fermentation_repo: Mock, mock_sample_repo: Mock):
        """Service instance with mocked dependencies."""
        from src.modules.fermentation.src.service_component.services.historical.historical_data_service import HistoricalDataService
        return HistoricalDataService(
            fermentation_repo=mock_fermentation_repo,
            sample_repo=mock_sample_repo
        )
    
    @pytest.mark.asyncio
    async def test_get_samples_returns_list_when_fermentation_found(
        self,
        service,
        mock_fermentation_repo: Mock,
        mock_sample_repo: Mock
    ):
        """Test successful retrieval of samples for historical fermentation."""
        # Arrange
        fermentation_id = 1
        winery_id = 1
        
        mock_fermentation = Mock(
            spec=Fermentation,
            id=fermentation_id,
            winery_id=winery_id,
            data_source="HISTORICAL"
        )
        mock_fermentation_repo.get_by_id.return_value = mock_fermentation
        
        mock_samples = [
            Mock(spec=DensitySample, id=1, fermentation_id=fermentation_id, data_source="HISTORICAL"),
            Mock(spec=SugarSample, id=2, fermentation_id=fermentation_id, data_source="HISTORICAL"),
        ]
        mock_sample_repo.get_samples_by_fermentation_id.return_value = mock_samples
        
        # Act
        result = await service.get_fermentation_samples(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        # Assert
        assert len(result) == len(mock_samples)
        mock_fermentation_repo.get_by_id.assert_called_once_with(fermentation_id, winery_id)
        mock_sample_repo.get_samples_by_fermentation_id.assert_called_once_with(
            fermentation_id=fermentation_id
        )
    
    @pytest.mark.asyncio
    async def test_get_samples_raises_not_found_when_fermentation_not_exists(
        self,
        service,
        mock_fermentation_repo: Mock,
        mock_sample_repo: Mock
    ):
        """Test NotFoundError when fermentation doesn't exist."""
        # Arrange
        fermentation_id = 999
        winery_id = 1
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.get_fermentation_samples(
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
        
        mock_fermentation_repo.get_by_id.assert_called_once_with(fermentation_id, winery_id)
        mock_sample_repo.get_samples_by_fermentation_id.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_samples_raises_not_found_when_wrong_winery(
        self,
        service,
        mock_fermentation_repo: Mock,
        mock_sample_repo: Mock
    ):
        """Test NotFoundError when fermentation belongs to different winery."""
        # Arrange
        fermentation_id = 1
        winery_id = 1
        
        # Repository returns None when winery_id doesn't match (multi-tenant filtering)
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.get_fermentation_samples(
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
        
        mock_sample_repo.get_samples_by_fermentation_id.assert_not_called()


class TestExtractPatterns:
    """
    Test suite for HistoricalDataService.extract_patterns()
    
    Business Rules:
    - Must aggregate data across multiple historical fermentations
    - Must filter by winery_id and data_source='HISTORICAL'
    - Optional filters: fruit_origin_id, date_range
    - Returns aggregated metrics for Analysis Engine:
      - avg_initial_density, avg_final_density
      - avg_initial_sugar_brix, avg_final_sugar_brix
      - avg_duration_days
      - success_rate (completed vs stuck)
      - common_issues
    """
    
    @pytest.fixture
    def mock_fermentation_repo(self) -> Mock:
        """Mock repository."""
        repo = create_autospec(IFermentationRepository, instance=True)
        repo.list_by_data_source.return_value = []
        return repo
    
    @pytest.fixture
    def mock_sample_repo(self) -> Mock:
        """Mock sample repository."""
        repo = create_autospec(ISampleRepository, instance=True)
        repo.get_samples_by_fermentation_id.return_value = []
        return repo
    
    @pytest.fixture
    def service(self, mock_fermentation_repo: Mock, mock_sample_repo: Mock):
        """Service instance with mocked dependencies."""
        from src.modules.fermentation.src.service_component.services.historical.historical_data_service import HistoricalDataService
        return HistoricalDataService(
            fermentation_repo=mock_fermentation_repo,
            sample_repo=mock_sample_repo
        )
    
    @pytest.mark.asyncio
    async def test_extract_patterns_returns_aggregated_metrics(
        self,
        service,
        mock_fermentation_repo: Mock,
        mock_sample_repo: Mock
    ):
        """Test pattern extraction with multiple fermentations."""
        # Arrange
        winery_id = 1
        fruit_origin_id = 5
        
        # Mock fermentations with datetime for start_date (not date)
        mock_fermentations = [
            Mock(
                spec=Fermentation,
                id=1,
                winery_id=winery_id,
                data_source="HISTORICAL",
                initial_density=1.100,
                initial_sugar_brix=24.0,
                fruit_origin_id=fruit_origin_id,
                start_date=datetime(2024, 1, 1),  # Use datetime, not date
                end_date=datetime(2024, 1, 15),
                status="completed"
            ),
            Mock(
                spec=Fermentation,
                id=2,
                winery_id=winery_id,
                data_source="HISTORICAL",
                initial_density=1.105,
                initial_sugar_brix=25.0,
                fruit_origin_id=fruit_origin_id,
                start_date=datetime(2024, 2, 1),  # Use datetime, not date
                end_date=datetime(2024, 2, 20),
                status="completed"
            ),
        ]
        mock_fermentation_repo.list_by_data_source.return_value = mock_fermentations
        
        # Mock samples for each fermentation (add data_source and recorded_at)
        mock_sample_repo.get_samples_by_fermentation_id.side_effect = [
            [
                Mock(spec=DensitySample, density=0.995, recorded_at=datetime(2024, 1, 15), data_source="HISTORICAL"),
                Mock(spec=SugarSample, sugar_brix=0.5, recorded_at=datetime(2024, 1, 15), data_source="HISTORICAL")
            ],
            [
                Mock(spec=DensitySample, density=0.990, recorded_at=datetime(2024, 2, 20), data_source="HISTORICAL"),
                Mock(spec=SugarSample, sugar_brix=0.3, recorded_at=datetime(2024, 2, 20), data_source="HISTORICAL")
            ],
        ]
        
        # Act
        result = await service.extract_patterns(
            winery_id=winery_id,
            fruit_origin_id=fruit_origin_id,
            date_range=(date(2024, 1, 1), date(2024, 12, 31))
        )
        
        # Assert
        assert "avg_initial_density" in result
        assert "avg_final_density" in result
        assert "avg_initial_sugar_brix" in result
        assert "avg_final_sugar_brix" in result
        assert "avg_duration_days" in result
        assert "success_rate" in result
        assert "total_fermentations" in result
        
        # Verify repository called with correct filters
        mock_fermentation_repo.list_by_data_source.assert_called_once()
        call_kwargs = mock_fermentation_repo.list_by_data_source.call_args.kwargs
        assert call_kwargs["winery_id"] == winery_id
        assert call_kwargs["data_source"] == "HISTORICAL"
    
    @pytest.mark.asyncio
    async def test_extract_patterns_returns_empty_when_no_data(
        self,
        service,
        mock_fermentation_repo: Mock
    ):
        """Test pattern extraction with no fermentations."""
        # Arrange
        winery_id = 1
        mock_fermentation_repo.list_by_data_source.return_value = []
        
        # Act
        result = await service.extract_patterns(
            winery_id=winery_id,
            fruit_origin_id=None,
            date_range=None
        )
        
        # Assert
        assert result["total_fermentations"] == 0
        assert result["avg_initial_density"] is None or result["avg_initial_density"] == 0
        assert result["avg_duration_days"] is None or result["avg_duration_days"] == 0
    
    @pytest.mark.asyncio
    async def test_extract_patterns_handles_incomplete_fermentations(
        self,
        service,
        mock_fermentation_repo: Mock,
        mock_sample_repo: Mock
    ):
        """Test pattern extraction with fermentations missing end_date."""
        # Arrange
        winery_id = 1
        
        mock_fermentations = [
            Mock(
                spec=Fermentation,
                id=1,
                winery_id=winery_id,
                data_source="HISTORICAL",
                initial_density=1.100,
                initial_sugar_brix=24.0,
                start_date=datetime(2024, 1, 1),
                end_date=None,  # In progress or stuck
                status="stuck"
            ),
        ]
        mock_fermentation_repo.list_by_data_source.return_value = mock_fermentations
        mock_sample_repo.get_samples_by_fermentation_id.return_value = []
        
        # Act
        result = await service.extract_patterns(
            winery_id=winery_id,
            fruit_origin_id=None,
            date_range=None
        )
        
        # Assert
        assert result["total_fermentations"] == 1
        # Should handle None values gracefully
        assert "success_rate" in result
