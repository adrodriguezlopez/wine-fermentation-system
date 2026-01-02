"""
Tests for Response Schemas (Pydantic DTOs)

Following TDD Red-Green-Refactor:
1. RED: Write tests first (they will fail)
2. GREEN: Implement schemas to make tests pass
3. REFACTOR: Improve code while keeping tests green
"""

import pytest
from datetime import datetime


# =============================================================================
# TEST 1: FermentationResponse - Basic instantiation from dict
# =============================================================================
def test_fermentation_response_from_entity():
    """
    Test: FermentationResponse should convert from entity-like data
    
    GREEN: Will pass once FermentationResponse schema exists
    """
    from src.modules.fermentation.src.api.schemas.responses.fermentation_responses import FermentationResponse
    
    # Arrange: Create a mock fermentation entity using a simple object
    # We avoid instantiating actual SQLAlchemy entity to prevent relationship issues
    class MockFermentation:
        def __init__(self):
            self.id = 1
            self.winery_id = 1
            self.fermented_by_user_id = 1
            self.vintage_year = 2024
            self.yeast_strain = "EC-1118"
            self.vessel_code = "TANK-01"
            self.input_mass_kg = 1000.5
            self.initial_sugar_brix = 22.5
            self.initial_density = 1.095
            self.status = "ACTIVE"
            self.start_date = datetime(2024, 11, 1, 10, 0, 0)
            self.created_at = datetime(2024, 11, 1, 9, 30, 0)
            self.updated_at = datetime(2024, 11, 1, 9, 30, 0)
            self.is_deleted = False
    
    fermentation = MockFermentation()
    
    # Act
    response = FermentationResponse.from_entity(fermentation)
    
    # Assert
    assert response.id == 1
    assert response.winery_id == 1
    assert response.vintage_year == 2024
    assert response.yeast_strain == "EC-1118"
    assert response.vessel_code == "TANK-01"
    assert response.input_mass_kg == 1000.5
    assert response.initial_sugar_brix == 22.5
    assert response.initial_density == 1.095
    assert response.status == "ACTIVE"
    assert response.start_date == datetime(2024, 11, 1, 10, 0, 0)
    assert response.created_at == datetime(2024, 11, 1, 9, 30, 0)


# =============================================================================
# TEST 2: FermentationResponse - JSON serialization
# =============================================================================
def test_fermentation_response_json_serialization():
    """
    Test: FermentationResponse should serialize to JSON correctly
    
    RED: Will fail until schema is implemented with Pydantic
    """
    from src.modules.fermentation.src.api.schemas.responses.fermentation_responses import FermentationResponse
    
    response = FermentationResponse(
        id=1,
        winery_id=1,
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code="TANK-01",
        input_mass_kg=1000.5,
        initial_sugar_brix=22.5,
        initial_density=1.095,
        status="ACTIVE",
        start_date=datetime(2024, 11, 1, 10, 0, 0),
        created_at=datetime(2024, 11, 1, 9, 30, 0),
        updated_at=datetime(2024, 11, 1, 9, 30, 0)
    )
    
    # Pydantic v2 uses model_dump for dict conversion
    data = response.model_dump()
    
    assert isinstance(data, dict)
    assert data["id"] == 1
    assert data["status"] == "ACTIVE"
    
    # JSON serialization should handle datetime
    json_str = response.model_dump_json()
    assert isinstance(json_str, str)
    assert "TANK-01" in json_str


# =============================================================================
# TEST 3: FermentationResponse - Optional fields
# =============================================================================
def test_fermentation_response_optional_vessel_code():
    """
    Test: FermentationResponse should handle optional vessel_code
    
    RED: Will fail until schema properly defines optional fields
    """
    from src.modules.fermentation.src.api.schemas.responses.fermentation_responses import FermentationResponse
    
    response = FermentationResponse(
        id=1,
        winery_id=1,
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code=None,  # Optional field
        input_mass_kg=1000.5,
        initial_sugar_brix=22.5,
        initial_density=1.095,
        status="ACTIVE",
        start_date=datetime(2024, 11, 1, 10, 0, 0),
        created_at=datetime(2024, 11, 1, 9, 30, 0),
        updated_at=datetime(2024, 11, 1, 9, 30, 0)
    )
    
    assert response.vessel_code is None
    data = response.model_dump()
    assert data["vessel_code"] is None


# =============================================================================
# TEST 4: SampleResponse - Basic instantiation from entity
# =============================================================================
def test_sample_response_from_entity():
    """
    Test: SampleResponse should convert from BaseSample entity
    
    GREEN: Will pass once SampleResponse schema exists
    """
    from src.modules.fermentation.src.api.schemas.responses.sample_responses import SampleResponse
    
    # Arrange: Create a mock sample entity using a simple object
    class MockSample:
        def __init__(self):
            self.id = 1
            self.fermentation_id = 1
            self.sample_type = "glucose"
            self.value = 15.5
            self.units = "g/L"
            self.recorded_at = datetime(2024, 11, 2, 14, 30, 0)
            self.recorded_by_user_id = 1
            self.created_at = datetime(2024, 11, 2, 14, 30, 0)
            self.updated_at = datetime(2024, 11, 2, 14, 30, 0)
            self.is_deleted = False
    
    sample = MockSample()
    
    # Act
    response = SampleResponse.from_entity(sample)
    
    # Assert
    assert response.id == 1
    assert response.fermentation_id == 1
    assert response.sample_type == "glucose"
    assert response.value == 15.5
    assert response.units == "g/L"
    assert response.recorded_at == datetime(2024, 11, 2, 14, 30, 0)
    assert response.created_at == datetime(2024, 11, 2, 14, 30, 0)


# =============================================================================
# TEST 5: SampleResponse - JSON serialization
# =============================================================================
def test_sample_response_json_serialization():
    """
    Test: SampleResponse should serialize to JSON correctly
    
    RED: Will fail until schema is implemented
    """
    from src.modules.fermentation.src.api.schemas.responses.sample_responses import SampleResponse
    
    response = SampleResponse(
        id=1,
        fermentation_id=1,
        sample_type="glucose",
        value=15.5,
        units="g/L",
        recorded_at=datetime(2024, 11, 2, 14, 30, 0),
        created_at=datetime(2024, 11, 2, 14, 30, 0),
        updated_at=datetime(2024, 11, 2, 14, 30, 0)
    )
    
    data = response.model_dump()
    assert isinstance(data, dict)
    assert data["sample_type"] == "glucose"
    assert data["value"] == 15.5
    
    json_str = response.model_dump_json()
    assert "glucose" in json_str


# =============================================================================
# TEST 6: Pydantic validation on invalid data
# =============================================================================
def test_fermentation_response_validation_error():
    """
    Test: FermentationResponse should validate required fields
    
    RED: Will fail until Pydantic validation is set up
    """
    from src.modules.fermentation.src.api.schemas.responses.fermentation_responses import FermentationResponse
    from pydantic import ValidationError
    
    # Missing required fields should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        FermentationResponse(
            id=1,
            # Missing winery_id, vintage_year, etc.
        )
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any(err["type"] == "missing" for err in errors)
