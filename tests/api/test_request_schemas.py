"""
Tests for Request Schemas (Pydantic DTOs for incoming data)

Following TDD Red-Green-Refactor:
1. RED: Write tests first (they will fail)
2. GREEN: Implement schemas to make tests pass
3. REFACTOR: Improve code while keeping tests green
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


# =============================================================================
# TEST 1: FermentationCreateRequest - Valid data
# =============================================================================
def test_fermentation_create_request_valid_data():
    """
    Test: FermentationCreateRequest should accept valid fermentation data
    
    RED: Will fail until we create FermentationCreateRequest schema
    """
    from src.modules.fermentation.src.api.schemas.requests.fermentation_requests import FermentationCreateRequest
    
    request = FermentationCreateRequest(
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code="TANK-01",
        input_mass_kg=1000.5,
        initial_sugar_brix=22.5,
        initial_density=1.095,
        start_date=datetime(2024, 11, 1, 10, 0, 0)
    )
    
    assert request.vintage_year == 2024
    assert request.yeast_strain == "EC-1118"
    assert request.vessel_code == "TANK-01"
    assert request.input_mass_kg == 1000.5
    assert request.initial_sugar_brix == 22.5
    assert request.initial_density == 1.095
    assert request.start_date == datetime(2024, 11, 1, 10, 0, 0)


# =============================================================================
# TEST 2: FermentationCreateRequest - Missing required fields
# =============================================================================
def test_fermentation_create_request_missing_required_fields():
    """
    Test: FermentationCreateRequest should reject data with missing required fields
    
    RED: Will fail until validation is implemented
    """
    from src.modules.fermentation.src.api.schemas.requests.fermentation_requests import FermentationCreateRequest
    
    # Missing vintage_year, yeast_strain, etc.
    with pytest.raises(ValidationError) as exc_info:
        FermentationCreateRequest(
            vessel_code="TANK-01"
        )
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    error_fields = {err["loc"][0] for err in errors}
    assert "vintage_year" in error_fields
    assert "yeast_strain" in error_fields
    assert "input_mass_kg" in error_fields


# =============================================================================
# TEST 3: FermentationCreateRequest - Invalid ranges
# =============================================================================
def test_fermentation_create_request_invalid_ranges():
    """
    Test: FermentationCreateRequest should validate numeric ranges
    
    RED: Will fail until Field validators are added
    """
    from src.modules.fermentation.src.api.schemas.requests.fermentation_requests import FermentationCreateRequest
    
    # Negative input_mass_kg should fail
    with pytest.raises(ValidationError) as exc_info:
        FermentationCreateRequest(
            vintage_year=2024,
            yeast_strain="EC-1118",
            input_mass_kg=-100,  # Invalid: negative
            initial_sugar_brix=22.5,
            initial_density=1.095,
            start_date=datetime(2024, 11, 1, 10, 0, 0)
        )
    
    errors = exc_info.value.errors()
    assert any("input_mass_kg" in str(err["loc"]) for err in errors)


# =============================================================================
# TEST 4: FermentationCreateRequest - Optional vessel_code
# =============================================================================
def test_fermentation_create_request_optional_vessel_code():
    """
    Test: FermentationCreateRequest should allow optional vessel_code
    
    GREEN: Will pass once schema is implemented with optional fields
    """
    from src.modules.fermentation.src.api.schemas.requests.fermentation_requests import FermentationCreateRequest
    
    request = FermentationCreateRequest(
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code=None,  # Optional
        input_mass_kg=1000.5,
        initial_sugar_brix=22.5,
        initial_density=1.095,
        start_date=datetime(2024, 11, 1, 10, 0, 0)
    )
    
    assert request.vessel_code is None


# =============================================================================
# TEST 5: FermentationUpdateRequest - Partial updates
# =============================================================================
def test_fermentation_update_request_partial_updates():
    """
    Test: FermentationUpdateRequest should allow updating only specific fields
    
    RED: Will fail until FermentationUpdateRequest is created
    """
    from src.modules.fermentation.src.api.schemas.requests.fermentation_requests import FermentationUpdateRequest
    
    # Update only status
    request = FermentationUpdateRequest(status="COMPLETED")
    assert request.status == "COMPLETED"
    assert request.yeast_strain is None
    assert request.vessel_code is None
    
    # Update multiple fields
    request2 = FermentationUpdateRequest(
        status="ACTIVE",
        vessel_code="TANK-02"
    )
    assert request2.status == "ACTIVE"
    assert request2.vessel_code == "TANK-02"


# =============================================================================
# TEST 6: FermentationUpdateRequest - All fields optional
# =============================================================================
def test_fermentation_update_request_all_optional():
    """
    Test: FermentationUpdateRequest should allow empty update (all fields optional)
    
    GREEN: Will pass once schema allows all optional fields
    """
    from src.modules.fermentation.src.api.schemas.requests.fermentation_requests import FermentationUpdateRequest
    
    # Empty update should be valid (though might be rejected by business logic)
    request = FermentationUpdateRequest()
    
    # All fields should be None
    assert request.status is None
    assert request.yeast_strain is None
    assert request.vessel_code is None


# =============================================================================
# TEST 7: SampleCreateRequest - Valid data
# =============================================================================
def test_sample_create_request_valid_data():
    """
    Test: SampleCreateRequest should accept valid sample data
    
    RED: Will fail until we create SampleCreateRequest schema
    """
    from src.modules.fermentation.src.api.schemas.requests.sample_requests import SampleCreateRequest
    
    request = SampleCreateRequest(
        sample_type="glucose",
        value=15.5,
        units="g/L",
        recorded_at=datetime(2024, 11, 2, 14, 30, 0)
    )
    
    assert request.sample_type == "glucose"
    assert request.value == 15.5
    assert request.units == "g/L"
    assert request.recorded_at == datetime(2024, 11, 2, 14, 30, 0)


# =============================================================================
# TEST 8: SampleCreateRequest - Missing required fields
# =============================================================================
def test_sample_create_request_missing_fields():
    """
    Test: SampleCreateRequest should reject missing required fields
    
    RED: Will fail until validation is implemented
    """
    from src.modules.fermentation.src.api.schemas.requests.sample_requests import SampleCreateRequest
    
    with pytest.raises(ValidationError) as exc_info:
        SampleCreateRequest(
            sample_type="glucose"
            # Missing value, units, recorded_at
        )
    
    errors = exc_info.value.errors()
    error_fields = {err["loc"][0] for err in errors}
    assert "value" in error_fields
    assert "units" in error_fields
    assert "recorded_at" in error_fields


# =============================================================================
# TEST 9: SampleCreateRequest - String length validation
# =============================================================================
def test_sample_create_request_string_length():
    """
    Test: SampleCreateRequest should validate string field lengths
    
    RED: Will fail until max_length validators are added
    """
    from src.modules.fermentation.src.api.schemas.requests.sample_requests import SampleCreateRequest
    
    # sample_type too long (max 50 chars)
    with pytest.raises(ValidationError) as exc_info:
        SampleCreateRequest(
            sample_type="a" * 51,  # Too long
            value=15.5,
            units="g/L",
            recorded_at=datetime(2024, 11, 2, 14, 30, 0)
        )
    
    errors = exc_info.value.errors()
    assert any("sample_type" in str(err["loc"]) for err in errors)


# =============================================================================
# TEST 10: SampleUpdateRequest - Partial updates
# =============================================================================
def test_sample_update_request_partial():
    """
    Test: SampleUpdateRequest should allow updating only specific fields
    
    RED: Will fail until SampleUpdateRequest is created
    """
    from src.modules.fermentation.src.api.schemas.requests.sample_requests import SampleUpdateRequest
    
    # Update only value
    request = SampleUpdateRequest(value=20.0)
    assert request.value == 20.0
    assert request.units is None
    
    # Update value and units
    request2 = SampleUpdateRequest(value=18.5, units="g/100mL")
    assert request2.value == 18.5
    assert request2.units == "g/100mL"
