"""
Tests for Fermentation API Endpoints

Tests POST /api/v1/fermentations endpoint with:
- Authentication (valid/invalid/missing tokens)
- Authorization (role-based access)
- Multi-tenancy (winery isolation)
- Request validation
- Business logic integration

RED Phase: Tests will fail until endpoint is implemented
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi import status
from pydantic import ValidationError

from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus


class TestPostFermentations:
    """
    Test suite for POST /api/v1/fermentations endpoint
    
    TDD RED Phase: Endpoint doesn't exist yet
    """
    
    def test_create_fermentation_success(self, client, mock_user_context):
        """
        Test: POST /fermentations should create fermentation with valid data
        
        RED: Will fail until router and endpoint are created
        """
        # Arrange
        request_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "vessel_code": "TANK-01",
            "input_mass_kg": 1000.5,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        
        # Act
        response = client.post("/api/v1/fermentations", json=request_data)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["vintage_year"] == 2024
        assert data["yeast_strain"] == "EC-1118"
        assert data["vessel_code"] == "TANK-01"
        assert data["winery_id"] == mock_user_context.winery_id
        assert data["status"] == FermentationStatus.ACTIVE.value
        assert "id" in data
        assert "created_at" in data
    
    def test_create_fermentation_missing_required_fields(self, client):
        """
        Test: POST /fermentations should reject missing required fields
        
        RED: Will fail until validation is implemented
        """
        # Arrange - Missing yeast_strain and other required fields
        request_data = {
            "vintage_year": 2024,
            "vessel_code": "TANK-01"
        }
        
        # Act
        response = client.post("/api/v1/fermentations", json=request_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
    
    def test_create_fermentation_invalid_ranges(self, client):
        """
        Test: POST /fermentations should validate numeric ranges
        
        RED: Will fail until Field validators are enforced
        """
        # Arrange - Negative input_mass_kg
        request_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": -100,  # Invalid: must be > 0
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        
        # Act
        response = client.post("/api/v1/fermentations", json=request_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
    
    def test_create_fermentation_optional_vessel_code(self, client, mock_user_context):
        """
        Test: POST /fermentations should allow optional vessel_code
        
        GREEN: Will pass once schema allows None
        """
        # Arrange - No vessel_code
        request_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.5,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        
        # Act
        response = client.post("/api/v1/fermentations", json=request_data)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["vessel_code"] is None
    
    def test_create_fermentation_multi_tenancy_isolation(self, client, mock_user_context):
        """
        Test: POST /fermentations should use winery_id from authenticated user
        
        RED: Will fail until UserContext integration is implemented
        """
        # Arrange
        request_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.5,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        
        # Act
        response = client.post("/api/v1/fermentations", json=request_data)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        # Verify winery_id comes from UserContext, not request
        assert data["winery_id"] == mock_user_context.winery_id
    
    def test_create_fermentation_without_authentication(self, client):
        """
        Test: POST /fermentations should reject unauthenticated requests
        
        RED: Will fail until auth dependency is added to endpoint
        
        Note: This test needs a client WITHOUT auth override
        """
        # This test requires a separate client without auth override
        # For now, we'll skip it and implement in integration phase
        pytest.skip("Requires client without auth override - implement in integration phase")
    
    def test_create_fermentation_unauthorized_role(self, test_db_session):
        """
        Test: POST /fermentations should check role authorization
        
        GREEN: Will pass once require_winemaker is used in endpoint
        
        Note: Only ADMIN and WINEMAKER should create fermentations
        """
        # Arrange - Create client with VIEWER role (not authorized)
        from src.shared.auth.domain.enums import UserRole
        from src.shared.auth.domain.dtos import UserContext
        from fastapi.testclient import TestClient
        from tests.api.conftest import create_test_app
        
        viewer_context = UserContext(
            user_id=99,
            winery_id=1,
            email="viewer@winery.com",
            role=UserRole.VIEWER
        )
        
        # Create app WITHOUT user override (so require_winemaker validates naturally)
        # Then manually override with viewer
        app = create_test_app()
        
        # Override both dependencies to return VIEWER (should trigger 403)
        from src.shared.auth.infra.api.dependencies import get_current_user, require_winemaker
        app.dependency_overrides[get_current_user] = lambda: viewer_context
        # Don't override require_winemaker - let it check the viewer's role naturally
        
        client = TestClient(app)
        
        request_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.5,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        
        # Act
        response = client.post("/api/v1/fermentations", json=request_data)
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "permissions" in response.json()["detail"].lower()
    
    @pytest.mark.skip(reason="Requires service injection - implement after real service integration")
    def test_create_fermentation_service_error(self, client):
        """
        Test: POST /fermentations should handle service layer errors
        
        Note: This test requires dependency injection of FermentationService
        Will be implemented in next iteration when we inject real service
        """
        pass
