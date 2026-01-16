"""
Unit tests for Historical Data API Router.

Tests all 8 endpoints with various scenarios using mocked service layer.
Following TDD approach with comprehensive test coverage.

Related ADR: ADR-032 (Historical Data API Layer), ADR-034 (Refactoring)
"""
import pytest
from datetime import datetime, date
from unittest.mock import Mock, AsyncMock, create_autospec
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.modules.fermentation.src.api_component.historical.routers.historical_router import (
    router,
    get_winery_id
)
from src.modules.fermentation.src.api.dependencies import (
    get_fermentation_service,
    get_pattern_analysis_service,
    get_sample_service
)
from src.modules.fermentation.src.service_component.interfaces.fermentation_service_interface import IFermentationService
from src.modules.fermentation.src.service_component.interfaces.pattern_analysis_service_interface import IPatternAnalysisService
from src.modules.fermentation.src.service_component.interfaces.sample_service_interface import ISampleService
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.service_component.errors import NotFoundError


# Test Fixtures

@pytest.fixture
def app():
    """Create FastAPI app with router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def mock_fermentation_service():
    """Create a mock FermentationService."""
    service = create_autospec(IFermentationService, instance=True)
    service.get_fermentation = AsyncMock()
    service.get_fermentations_by_winery = AsyncMock()
    return service


@pytest.fixture
def mock_pattern_service():
    """Create a mock PatternAnalysisService."""
    service = create_autospec(IPatternAnalysisService, instance=True)
    service.extract_patterns = AsyncMock()
    return service


@pytest.fixture
def mock_sample_service():
    """Create a mock SampleService."""
    service = create_autospec(ISampleService, instance=True)
    service.get_samples_by_fermentation = AsyncMock()
    return service


@pytest.fixture
def client(app, mock_fermentation_service, mock_pattern_service, mock_sample_service):
    """Create test client with dependency overrides."""
    async def override_get_fermentation_service():
        return mock_fermentation_service
    
    async def override_get_pattern_service():
        return mock_pattern_service
    
    async def override_get_sample_service():
        return mock_sample_service
    
    async def override_get_winery_id():
        return 1
    
    app.dependency_overrides[get_fermentation_service] = override_get_fermentation_service
    app.dependency_overrides[get_pattern_analysis_service] = override_get_pattern_service
    app.dependency_overrides[get_sample_service] = override_get_sample_service
    app.dependency_overrides[get_winery_id] = override_get_winery_id
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_fermentation():
    """Create a mock Fermentation entity."""
    fermentation = Mock(spec=Fermentation)
    fermentation.id = 1
    fermentation.winery_id = 1
    fermentation.vintage_year = 2024
    fermentation.yeast_strain = "EC-1118"
    fermentation.input_mass_kg = 1000.0
    fermentation.initial_sugar_brix = 24.5
    fermentation.initial_density = 1.105
    fermentation.vessel_code = "T-001"
    fermentation.start_date = datetime(2024, 1, 1, 8, 0, 0)
    fermentation.end_date = datetime(2024, 1, 15, 10, 0, 0)
    fermentation.status = Mock(value="completed")
    fermentation.data_source = "HISTORICAL"
    fermentation.fruit_origin_id = 5
    fermentation.created_at = datetime(2024, 12, 1, 0, 0, 0)
    return fermentation


@pytest.fixture
def mock_sample():
    """Create a mock BaseSample entity."""
    sample = Mock(spec=BaseSample)
    sample.id = 1
    sample.fermentation_id = 1
    sample.sample_type = Mock(value="density")
    sample.recorded_at = datetime(2024, 1, 2, 10, 0, 0)
    sample.data_source = "HISTORICAL"
    sample.density = 1.095
    sample.sugar_brix = None
    sample.temperature_celsius = None
    return sample


# Test Class: GET /api/fermentation/historical

class TestListHistoricalFermentations:
    """Test cases for listing historical fermentations endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_returns_paginated_response_with_filters(self, client, mock_fermentation_service, mock_fermentation):
        """Test listing fermentations with filters returns paginated response."""
        # Arrange
        mock_fermentation_service.get_fermentations_by_winery.return_value = [mock_fermentation]
        
        # Act
        response = client.get(
            "/api/fermentation/historical",
            params={
                "start_date_from": "2024-01-01",
                "start_date_to": "2024-12-31",
                "fruit_origin_id": 5,
                "status": "completed",
                "limit": 100,
                "offset": 0
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == 1
        assert data["items"][0]["winery_id"] == 1
        assert data["items"][0]["status"] == "completed"
        
        # Verify service was called with correct parameters (ADR-034: uses get_fermentations_by_winery)
        mock_fermentation_service.get_fermentations_by_winery.assert_called_once()
        call_kwargs = mock_fermentation_service.get_fermentations_by_winery.call_args.kwargs
        assert call_kwargs["winery_id"] == 1
        assert call_kwargs["data_source"] == "HISTORICAL"  # ADR-034
        assert call_kwargs["status"] == "completed"
        assert call_kwargs["include_completed"] == True
    
    @pytest.mark.asyncio
    async def test_list_with_minimal_parameters(self, client, mock_fermentation_service, mock_fermentation):
        """Test listing fermentations with only required parameters."""
        # Arrange
        mock_fermentation_service.get_fermentations_by_winery.return_value = [mock_fermentation]
        
        # Act
        response = client.get("/api/fermentation/historical")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        
        # Verify service called with data_source='HISTORICAL' (ADR-034)
        call_kwargs = mock_fermentation_service.get_fermentations_by_winery.call_args.kwargs
        assert call_kwargs["data_source"] == "HISTORICAL"
        assert call_kwargs["include_completed"] == True
    
    @pytest.mark.asyncio
    async def test_list_handles_service_errors(self, client, mock_fermentation_service):
        """Test that service errors are handled gracefully."""
        # Arrange
        mock_fermentation_service.get_fermentations_by_winery.side_effect = Exception("Database error")
        
        # Act
        response = client.get("/api/fermentation/historical")
        
        # Assert
        assert response.status_code == 500
        assert "Failed to retrieve historical fermentations" in response.json()["detail"]


# Test Class: GET /api/fermentation/historical/{id}

class TestGetHistoricalFermentation:
    """Test cases for getting a single historical fermentation endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_returns_fermentation_when_found(self, client, mock_fermentation_service, mock_fermentation):
        """Test getting a fermentation by ID returns the entity."""
        # Arrange
        mock_fermentation_service.get_fermentation.return_value = mock_fermentation
        
        # Act
        response = client.get("/api/fermentation/historical/1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["winery_id"] == 1
        assert data["status"] == "completed"
        
        # Verify service was called (ADR-034: uses get_fermentation directly)
        mock_fermentation_service.get_fermentation.assert_called_once_with(
            fermentation_id=1,
            winery_id=1
        )
    
    @pytest.mark.asyncio
    async def test_get_returns_404_when_not_found(self, client, mock_fermentation_service):
        """Test that 404 is returned when fermentation doesn't exist."""
        # Arrange
        mock_fermentation_service.get_fermentation.return_value = None
        
        # Act
        response = client.get("/api/fermentation/historical/999")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_handles_service_errors(self, client, mock_fermentation_service):
        """Test that service errors are handled gracefully."""
        # Arrange
        mock_fermentation_service.get_fermentation.side_effect = Exception("Database error")
        
        # Act
        response = client.get("/api/fermentation/historical/1")
        
        # Assert
        assert response.status_code == 500
        assert "Failed to retrieve historical fermentation" in response.json()["detail"]


# Test Class: GET /api/fermentation/historical/{id}/samples

class TestGetFermentationSamples:
    """Test cases for getting fermentation samples endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_samples_returns_list(self, client, mock_fermentation_service, mock_sample_service, mock_fermentation, mock_sample):
        """Test getting samples returns list of samples."""
        # Arrange
        mock_fermentation_service.get_fermentation.return_value = mock_fermentation
        mock_sample_service.get_samples_by_fermentation.return_value = [mock_sample]
        
        # Act
        response = client.get("/api/fermentation/historical/1/samples")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["fermentation_id"] == 1
        assert data[0]["sample_type"] == "density"
        
        # Verify services were called (ADR-034)
        mock_fermentation_service.get_fermentation.assert_called_once_with(
            fermentation_id=1,
            winery_id=1
        )
        mock_sample_service.get_samples_by_fermentation.assert_called_once_with(
            fermentation_id=1,
            winery_id=1
        )
    
    @pytest.mark.asyncio
    async def test_get_samples_returns_404_when_fermentation_not_found(self, client, mock_fermentation_service, mock_sample_service):
        """Test that 404 is returned when fermentation doesn't exist."""
        # Arrange
        mock_fermentation_service.get_fermentation.return_value = None
        
        # Act
        response = client.get("/api/fermentation/historical/999/samples")
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_samples_handles_service_errors(self, client, mock_fermentation_service, mock_sample_service):
        """Test that service errors are handled gracefully."""
        # Arrange
        mock_fermentation_service.get_fermentation.side_effect = Exception("Database error")
        
        # Act
        response = client.get("/api/fermentation/historical/1/samples")
        
        # Assert
        assert response.status_code == 500


# Test Class: GET /api/fermentation/historical/patterns/extract

class TestExtractPatterns:
    """Test cases for pattern extraction endpoint."""
    
    @pytest.mark.asyncio
    async def test_extract_patterns_returns_aggregated_metrics(self, client, mock_pattern_service):
        """Test pattern extraction returns aggregated metrics."""
        # Arrange
        patterns_dict = {
            "total_fermentations": 100,
            "avg_initial_density": 1.102,
            "avg_final_density": 0.993,
            "avg_initial_sugar_brix": 24.3,
            "avg_final_sugar_brix": 0.4,
            "avg_duration_days": 14.5,
            "success_rate": 0.95,
            "completed_count": 95,
            "stuck_count": 5
        }
        mock_pattern_service.extract_patterns.return_value = patterns_dict
        
        # Act
        response = client.get(
            "/api/fermentation/historical/patterns/extract",
            params={
                "fruit_origin_id": 5,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_fermentations"] == 100
        assert data["avg_initial_density"] == 1.102
        assert data["success_rate"] == 0.95
        
        # Verify service was called (ADR-034: uses PatternAnalysisService)
        mock_pattern_service.extract_patterns.assert_called_once()
        call_kwargs = mock_pattern_service.extract_patterns.call_args.kwargs
        assert call_kwargs["winery_id"] == 1
        assert call_kwargs["data_source"] == "HISTORICAL"  # ADR-034
        assert call_kwargs["fruit_origin_id"] == 5
        # date_range is now a tuple (start_date, end_date)
        assert call_kwargs["date_range"][0] == date(2024, 1, 1)
        assert call_kwargs["date_range"][1] == date(2024, 12, 31)
    
    @pytest.mark.asyncio
    async def test_extract_patterns_with_minimal_filters(self, client, mock_pattern_service):
        """Test pattern extraction with no filters."""
        # Arrange
        patterns_dict = {
            "total_fermentations": 50,
            "avg_initial_density": None,
            "avg_final_density": None,
            "avg_initial_sugar_brix": None,
            "avg_final_sugar_brix": None,
            "avg_duration_days": None,
            "success_rate": 0.0,
            "completed_count": 0,
            "stuck_count": 0
        }
        mock_pattern_service.extract_patterns.return_value = patterns_dict
        
        # Act
        response = client.get("/api/fermentation/historical/patterns/extract")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_fermentations"] == 50
        
        # Verify service called with HISTORICAL data_source (ADR-034)
        call_kwargs = mock_pattern_service.extract_patterns.call_args.kwargs
        assert call_kwargs["data_source"] == "HISTORICAL"
        assert call_kwargs["fruit_origin_id"] is None
        assert call_kwargs["date_range"] is None
    
    @pytest.mark.asyncio
    async def test_extract_patterns_handles_service_errors(self, client, mock_pattern_service):
        """Test that service errors are handled gracefully."""
        # Arrange
        mock_pattern_service.extract_patterns.side_effect = Exception("Database error")
        
        # Act
        response = client.get("/api/fermentation/historical/patterns/extract")
        
        # Assert
        assert response.status_code == 500


# Test Class: GET /api/fermentation/historical/statistics/dashboard

class TestGetDashboardStatistics:
    """Test cases for dashboard statistics endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_statistics_returns_dashboard_metrics(self, client, mock_pattern_service):
        """Test getting statistics returns dashboard metrics."""
        # Arrange
        patterns_dict = {
            "total_fermentations": 500,
            "avg_initial_density": 1.105,
            "avg_final_density": 0.995,
            "avg_initial_sugar_brix": 24.0,
            "avg_final_sugar_brix": 0.5,
            "avg_duration_days": 15.2,
            "success_rate": 0.92,
            "completed_count": 460,
            "stuck_count": 40
        }
        mock_pattern_service.extract_patterns.return_value = patterns_dict
        
        # Act
        response = client.get("/api/fermentation/historical/statistics/dashboard")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_fermentations"] == 500
        assert data["avg_duration_days"] == 15.2
        assert data["success_rate"] == 0.92
        
        # Verify uses PatternAnalysisService (ADR-034)
        mock_pattern_service.extract_patterns.assert_called_once()
        call_kwargs = mock_pattern_service.extract_patterns.call_args.kwargs
        assert call_kwargs["data_source"] == "HISTORICAL"
    
    @pytest.mark.asyncio
    async def test_get_statistics_handles_service_errors(self, client, mock_pattern_service):
        """Test that service errors are handled gracefully."""
        # Arrange
        mock_pattern_service.extract_patterns.side_effect = Exception("Database error")
        
        # Act
        response = client.get("/api/fermentation/historical/statistics/dashboard")
        
        # Assert
        assert response.status_code == 500


# Test Class: POST /api/fermentation/historical/import

class TestTriggerImport:
    """Test cases for triggering ETL import endpoint."""
    
    @pytest.mark.asyncio
    async def test_trigger_import_returns_job_id(self, client):
        """Test triggering import returns job ID (placeholder)."""
        # Act
        response = client.post("/api/fermentation/historical/import")
        
        # Assert
        assert response.status_code == 202  # Accepted
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert "message" in data
        assert "not yet implemented" in data["message"].lower()


# Test Class: GET /api/fermentation/historical/import/{job_id}

class TestGetImportJobStatus:
    """Test cases for getting import job status endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_job_status_returns_404_placeholder(self, client):
        """Test getting job status returns 404 (placeholder)."""
        # Act
        response = client.get("/api/fermentation/historical/import/1")
        
        # Assert
        assert response.status_code == 404
        assert "not yet implemented" in response.json()["detail"].lower()


# Test Class: GET /api/fermentation/historical/import

class TestListImportJobs:
    """Test cases for listing import jobs endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_jobs_returns_empty_list_placeholder(self, client):
        """Test listing jobs returns empty list (placeholder)."""
        # Act
        response = client.get("/api/fermentation/historical/import")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # Placeholder returns empty
    
    @pytest.mark.asyncio
    async def test_list_jobs_accepts_pagination_params(self, client):
        """Test listing jobs accepts pagination parameters."""
        # Act
        response = client.get(
            "/api/fermentation/historical/import",
            params={"limit": 20, "offset": 10}
        )
        
        # Assert
        assert response.status_code == 200
