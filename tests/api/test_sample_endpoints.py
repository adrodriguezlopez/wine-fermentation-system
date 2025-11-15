"""
TDD Tests for Sample API Endpoints

Tests sample measurement endpoints with authentication, authorization,
and multi-tenancy enforcement.

Test Structure:
- Phase 3a: POST /fermentations/{id}/samples (Create sample)
- Phase 3b: GET /fermentations/{id}/samples (List samples)
- Phase 3c: GET /fermentations/{id}/samples/{sample_id} (Get sample)
- Phase 3d: GET /fermentations/{id}/samples/latest (Latest sample)
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta


# ======================================================================================
# PHASE 3a: POST /fermentations/{fermentation_id}/samples - Create Sample
# ======================================================================================

class TestPostSample:
    """Tests for POST /fermentations/{fermentation_id}/samples endpoint."""
    
    def test_create_sample_success(self, client, mock_user_context):
        """
        TDD RED: Should create sample with valid data.
        
        Given: Existing fermentation
        When: POST with valid sample data
        Then: Returns 201 with created sample
        """
        # Create fermentation first
        fermentation_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.0,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        fermentation_response = client.post("/api/v1/fermentations", json=fermentation_data)
        fermentation_id = fermentation_response.json()["id"]
        
        # Create sample
        sample_data = {
            "sample_type": "sugar",
            "value": 20.5,
            "units": "°Brix",
            "recorded_at": "2024-11-02T10:00:00"
        }
        response = client.post(
            f"/api/v1/fermentations/{fermentation_id}/samples",
            json=sample_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["fermentation_id"] == fermentation_id
        assert data["sample_type"] == "sugar"
        assert data["value"] == 20.5
        assert data["units"] == "°Brix"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_sample_fermentation_not_found(self, client):
        """Should return 404 for non-existent fermentation."""
        sample_data = {
            "sample_type": "sugar",
            "value": 20.5,
            "units": "°Brix",
            "recorded_at": "2024-11-02T10:00:00"
        }
        response = client.post(
            "/api/v1/fermentations/99999/samples",
            json=sample_data
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_sample_invalid_data(self, client, mock_user_context):
        """Should return 422 for invalid sample data."""
        # Create fermentation
        fermentation_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.0,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        fermentation_response = client.post("/api/v1/fermentations", json=fermentation_data)
        fermentation_id = fermentation_response.json()["id"]
        
        # Missing required field
        sample_data = {
            "sample_type": "sugar",
            "value": 20.5
            # Missing units and recorded_at
        }
        response = client.post(
            f"/api/v1/fermentations/{fermentation_id}/samples",
            json=sample_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_sample_without_authentication(self, unauthenticated_client):
        """Should reject request without authentication."""
        sample_data = {
            "sample_type": "sugar",
            "value": 20.5,
            "units": "°Brix",
            "recorded_at": "2024-11-02T10:00:00"
        }
        response = unauthenticated_client.post(
            "/api/v1/fermentations/1/samples",
            json=sample_data
        )
        
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


# ======================================================================================
# PHASE 3b: GET /fermentations/{fermentation_id}/samples - List Samples
# ======================================================================================

class TestGetSamples:
    """Tests for GET /fermentations/{fermentation_id}/samples endpoint."""
    
    def test_list_samples_success(self, client, mock_user_context):
        """
        TDD RED: Should list all samples for a fermentation.
        
        Given: Fermentation with multiple samples
        When: GET samples
        Then: Returns 200 with all samples in chronological order
        """
        # Create fermentation
        fermentation_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.0,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        fermentation_response = client.post("/api/v1/fermentations", json=fermentation_data)
        fermentation_id = fermentation_response.json()["id"]
        
        # Create samples
        samples = [
            {
                "sample_type": "sugar",
                "value": 20.5,
                "units": "°Brix",
                "recorded_at": "2024-11-02T10:00:00"
            },
            {
                "sample_type": "temperature",
                "value": 22.0,
                "units": "°C",
                "recorded_at": "2024-11-02T14:00:00"
            },
            {
                "sample_type": "sugar",
                "value": 18.0,
                "units": "°Brix",
                "recorded_at": "2024-11-03T10:00:00"
            }
        ]
        
        for sample in samples:
            client.post(f"/api/v1/fermentations/{fermentation_id}/samples", json=sample)
        
        # Get all samples
        response = client.get(f"/api/v1/fermentations/{fermentation_id}/samples")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        # Should be in chronological order
        assert data[0]["recorded_at"] < data[1]["recorded_at"] < data[2]["recorded_at"]
    
    def test_list_samples_empty(self, client, mock_user_context):
        """Should return empty list for fermentation with no samples."""
        # Create fermentation without samples
        fermentation_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.0,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        fermentation_response = client.post("/api/v1/fermentations", json=fermentation_data)
        fermentation_id = fermentation_response.json()["id"]
        
        response = client.get(f"/api/v1/fermentations/{fermentation_id}/samples")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_list_samples_fermentation_not_found(self, client):
        """Should return 404 for non-existent fermentation."""
        response = client.get("/api/v1/fermentations/99999/samples")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ======================================================================================
# PHASE 3c: GET /fermentations/{fermentation_id}/samples/{sample_id} - Get Sample
# ======================================================================================

class TestGetSample:
    """Tests for GET /fermentations/{fermentation_id}/samples/{sample_id} endpoint."""
    
    def test_get_sample_success(self, client, mock_user_context):
        """
        TDD RED: Should retrieve specific sample.
        
        Given: Fermentation with samples
        When: GET specific sample by ID
        Then: Returns 200 with sample data
        """
        # Create fermentation
        fermentation_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.0,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        fermentation_response = client.post("/api/v1/fermentations", json=fermentation_data)
        fermentation_id = fermentation_response.json()["id"]
        
        # Create sample
        sample_data = {
            "sample_type": "sugar",
            "value": 20.5,
            "units": "°Brix",
            "recorded_at": "2024-11-02T10:00:00"
        }
        create_response = client.post(
            f"/api/v1/fermentations/{fermentation_id}/samples",
            json=sample_data
        )
        sample_id = create_response.json()["id"]
        
        # Get sample
        response = client.get(
            f"/api/v1/fermentations/{fermentation_id}/samples/{sample_id}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_id
        assert data["sample_type"] == "sugar"
        assert data["value"] == 20.5
    
    def test_get_sample_not_found(self, client, mock_user_context):
        """Should return 404 for non-existent sample."""
        # Create fermentation
        fermentation_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.0,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        fermentation_response = client.post("/api/v1/fermentations", json=fermentation_data)
        fermentation_id = fermentation_response.json()["id"]
        
        response = client.get(
            f"/api/v1/fermentations/{fermentation_id}/samples/99999"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ======================================================================================
# PHASE 3d: GET /fermentations/{fermentation_id}/samples/latest - Latest Sample
# ======================================================================================

class TestGetLatestSample:
    """Tests for GET /fermentations/{fermentation_id}/samples/latest endpoint."""
    
    def test_get_latest_sample_success(self, client, mock_user_context):
        """
        TDD RED: Should retrieve most recent sample.
        
        Given: Fermentation with multiple samples
        When: GET latest sample
        Then: Returns 200 with most recent sample
        """
        # Create fermentation
        fermentation_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.0,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        fermentation_response = client.post("/api/v1/fermentations", json=fermentation_data)
        fermentation_id = fermentation_response.json()["id"]
        
        # Create samples at different times
        samples = [
            {
                "sample_type": "sugar",
                "value": 20.5,
                "units": "°Brix",
                "recorded_at": "2024-11-02T10:00:00"
            },
            {
                "sample_type": "sugar",
                "value": 18.0,
                "units": "°Brix",
                "recorded_at": "2024-11-03T10:00:00"
            },
            {
                "sample_type": "sugar",
                "value": 15.5,
                "units": "°Brix",
                "recorded_at": "2024-11-04T10:00:00"  # Latest
            }
        ]
        
        for sample in samples:
            client.post(f"/api/v1/fermentations/{fermentation_id}/samples", json=sample)
        
        # Get latest sample
        response = client.get(
            f"/api/v1/fermentations/{fermentation_id}/samples/latest"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["value"] == 15.5
        assert data["recorded_at"] == "2024-11-04T10:00:00"
    
    def test_get_latest_sample_no_samples(self, client, mock_user_context):
        """Should return 404 when no samples exist."""
        # Create fermentation without samples
        fermentation_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.0,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        fermentation_response = client.post("/api/v1/fermentations", json=fermentation_data)
        fermentation_id = fermentation_response.json()["id"]
        
        response = client.get(
            f"/api/v1/fermentations/{fermentation_id}/samples/latest"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_latest_sample_filter_by_type(self, client, mock_user_context):
        """
        TDD RED: Should filter latest sample by type.
        
        Given: Fermentation with samples of different types
        When: GET latest sample with type filter
        Then: Returns most recent sample of that type
        """
        # Create fermentation
        fermentation_data = {
            "vintage_year": 2024,
            "yeast_strain": "EC-1118",
            "input_mass_kg": 1000.0,
            "initial_sugar_brix": 22.5,
            "initial_density": 1.095,
            "start_date": "2024-11-01T10:00:00"
        }
        fermentation_response = client.post("/api/v1/fermentations", json=fermentation_data)
        fermentation_id = fermentation_response.json()["id"]
        
        # Create mixed samples
        samples = [
            {
                "sample_type": "sugar",
                "value": 20.5,
                "units": "°Brix",
                "recorded_at": "2024-11-02T10:00:00"
            },
            {
                "sample_type": "temperature",
                "value": 22.0,
                "units": "°C",
                "recorded_at": "2024-11-03T10:00:00"  # Latest temperature
            },
            {
                "sample_type": "sugar",
                "value": 18.0,
                "units": "°Brix",
                "recorded_at": "2024-11-04T10:00:00"  # Latest sugar
            }
        ]
        
        for sample in samples:
            client.post(f"/api/v1/fermentations/{fermentation_id}/samples", json=sample)
        
        # Get latest temperature sample
        response = client.get(
            f"/api/v1/fermentations/{fermentation_id}/samples/latest?sample_type=temperature"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sample_type"] == "temperature"
        assert data["value"] == 22.0
