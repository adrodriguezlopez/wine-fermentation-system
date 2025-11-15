import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from domain.enums.sample_type import SampleType
from service_component.interfaces.chronology_validation_service_interface import IChronologyValidationService
from service_component.models.schemas.validations.validation_error import ValidationError
from service_component.models.schemas.validations.validation_result import ValidationResult

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from service_component.interfaces.business_rule_validation_service_interface import IBusinessRuleValidationService
from service_component.interfaces.value_validation_service_interface import IValueValidationService
from service_component.services.validation_orchestrator import ValidationOrchestrator

@pytest.fixture
def mock_chronology_service():
    return Mock(IChronologyValidationService)

@pytest.fixture
def mock_value_validation_service():
    return Mock(IValueValidationService)

@pytest.fixture
def mock_business_rule_validation_service():
    return Mock(IBusinessRuleValidationService)

@pytest.fixture
def validation_orchestrator(
    mock_chronology_service,
    mock_value_validation_service,
    mock_business_rule_validation_service
):
    return ValidationOrchestrator(
        chronology_validator=mock_chronology_service,
        value_validator=mock_value_validation_service,
        business_rules_validator=mock_business_rule_validation_service
    )


@pytest.mark.asyncio
async def test_validate_sample_complete_chronology_failure(
    validation_orchestrator,
    mock_chronology_service,
    mock_value_validation_service,
    mock_business_rule_validation_service
):

    mock_chronology_service.validate_sample_chronology = AsyncMock(return_value=ValidationResult.failure(errors=[
        ValidationError(field="recorded_at", message="Timestamp is before last sample", current_value="2023-10-01T10:00:00Z")
    ]))

    # Asegurarse de que los otros mocks devuelvan ValidationResult reales
    mock_value_validation_service.validate_sample_value = Mock(return_value=ValidationResult.success())
    mock_business_rule_validation_service.validate_sugar_trend = AsyncMock(return_value=ValidationResult.success())
    mock_business_rule_validation_service.validate_temperature_range = AsyncMock(return_value=ValidationResult.success())
    
    result = await validation_orchestrator.validate_sample_complete(fermentation_id=1, new_sample=Mock())
    
    assert not result.is_valid
    assert len(result.errors) == 1
    assert result.errors[0].field == "recorded_at"
    mock_chronology_service.validate_sample_chronology.assert_awaited_once()
    mock_value_validation_service.validate_sample_value.assert_not_called()
    mock_business_rule_validation_service.validate_sugar_trend.assert_not_called()


@pytest.mark.asyncio
async def test_validate_sample_complete_chronology_success(
    validation_orchestrator,
    mock_chronology_service,
    mock_value_validation_service,
    mock_business_rule_validation_service
):

    mock_chronology_service.validate_sample_chronology = AsyncMock(return_value=ValidationResult.success())
    # Asegurarse de que los otros mocks devuelvan ValidationResult reales
    mock_value_validation_service.validate_sample_value = Mock(return_value=ValidationResult.success())
    mock_business_rule_validation_service.validate_sugar_trend = AsyncMock(return_value=ValidationResult.success())
    mock_business_rule_validation_service.validate_temperature_range = AsyncMock(return_value=ValidationResult.success())
    
    result = await validation_orchestrator.validate_sample_complete(fermentation_id=1, new_sample=Mock())
    
    assert result.is_valid
    assert len(result.errors) == 0
    mock_chronology_service.validate_sample_chronology.assert_awaited_once()


@pytest.mark.asyncio
async def test_validate_sample_complete_chronology_and_validation_value_complete_for_sugar(
    validation_orchestrator,
    mock_chronology_service,
    mock_value_validation_service,
    mock_business_rule_validation_service
):
    sample = Mock()
    sample.sample_type = SampleType.SUGAR
    sample.value = 5.0
    
    mock_chronology_service.validate_sample_chronology = AsyncMock(return_value=ValidationResult.success())
    # Asegurarse de que los otros mocks devuelvan ValidationResult reales
    mock_value_validation_service.validate_sample_value = Mock(return_value=ValidationResult.success())
    mock_business_rule_validation_service.validate_sugar_trend = AsyncMock(return_value=ValidationResult.success())
    mock_business_rule_validation_service.validate_temperature_range = AsyncMock(return_value=ValidationResult.success())
    
    result = await validation_orchestrator.validate_sample_complete(fermentation_id=1, new_sample=sample)
    
    assert result.is_valid
    assert len(result.errors) == 0
    mock_chronology_service.validate_sample_chronology.assert_awaited_once()
    mock_value_validation_service.validate_sample_value.assert_called_once()
    mock_business_rule_validation_service.validate_sugar_trend.assert_awaited_once()


@pytest.mark.asyncio
async def test_validate_sample_complete_chronology_and_validation_value_complete_for_temperature(
    validation_orchestrator,
    mock_chronology_service,
    mock_value_validation_service,
    mock_business_rule_validation_service
):
    sample = Mock()
    sample.sample_type = SampleType.TEMPERATURE
    sample.value = 20.0
    
    mock_chronology_service.validate_sample_chronology = AsyncMock(return_value=ValidationResult.success())
    # Asegurarse de que los otros mocks devuelvan ValidationResult reales
    mock_value_validation_service.validate_sample_value = Mock(return_value=ValidationResult.success())
    mock_business_rule_validation_service.validate_sugar_trend = AsyncMock(return_value=ValidationResult.success())
    mock_business_rule_validation_service.validate_temperature_range = AsyncMock(return_value=ValidationResult.success())
    
    result = await validation_orchestrator.validate_sample_complete(fermentation_id=1, new_sample=sample)
    
    assert result.is_valid
    assert len(result.errors) == 0
    mock_chronology_service.validate_sample_chronology.assert_awaited_once()
    mock_value_validation_service.validate_sample_value.assert_called_once()
    # Temperature validation is currently disabled - TODO: enable when FermentationRepository.get_fermentation_temperature_range is implemented
    # mock_business_rule_validation_service.validate_temperature_range.assert_awaited_once()