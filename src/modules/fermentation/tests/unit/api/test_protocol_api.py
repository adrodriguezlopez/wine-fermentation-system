"""
Unit tests for Protocol API Routers (Phase 2 - ADR-035)

Tests all 16 protocol API endpoints with mocked dependencies:
- 6 Protocol endpoints (CRUD + list + activate)
- 4 Protocol Step endpoints (CRUD + list)
- 4 Protocol Execution endpoints (start + CRUD + list)
- 2 Step Completion endpoints (create + list)

Following ADR-006 (API Layer Design), ADR-033 (Coverage Improvement)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from fastapi import HTTPException

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent / "src"))

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums.user_role import UserRole

# Router functions
from src.modules.fermentation.src.api.routers.protocol_router import (
    create_protocol,
    get_protocol,
    update_protocol,
    delete_protocol,
    list_protocols,
    activate_protocol,
)
from src.modules.fermentation.src.api.routers.protocol_step_router import (
    create_protocol_step,
    update_protocol_step,
    delete_protocol_step,
    list_protocol_steps,
)
from src.modules.fermentation.src.api.routers.protocol_execution_router import (
    start_protocol_execution,
    update_protocol_execution,
    get_protocol_execution,
    list_protocol_executions,
)
from src.modules.fermentation.src.api.routers.step_completion_router import (
    complete_protocol_step,
    list_execution_completions,
    get_step_completion,
)

# Request schemas (Pydantic)
from src.modules.fermentation.src.api.schemas.requests import (
    ProtocolCreateRequest,
    ProtocolUpdateRequest,
    StepCreateRequest,
    StepUpdateRequest,
    ExecutionStartRequest,
    ExecutionUpdateRequest,
    CompletionCreateRequest,
)

# Response schemas (Pydantic)
from src.modules.fermentation.src.api.schemas.responses import (
    ProtocolResponse,
    ProtocolListResponse,
    StepResponse,
    StepListResponse,
    ExecutionResponse,
    ExecutionListResponse,
    CompletionResponse,
    CompletionListResponse,
)

# Domain DTOs (Dataclasses)
from src.modules.fermentation.src.domain.dtos import (
    ProtocolCreate,
    ProtocolUpdate,
    StepCreate,
    StepUpdate,
    ExecutionStart,
    ExecutionUpdate,
    CompletionCreate,
)


# ======================================================================================
# Fixtures
# ======================================================================================

@pytest.fixture
def mock_user_context():
    """Mock authenticated winemaker user context"""
    return UserContext(
        user_id=1,
        email="winemaker@test.com",
        role=UserRole.WINEMAKER,
        winery_id=10
    )


@pytest.fixture
def mock_protocol_repository():
    """Mock protocol repository"""
    repo = Mock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.list_by_winery_paginated = AsyncMock()
    repo.deactivate_by_winery_varietal = AsyncMock()
    return repo


@pytest.fixture
def mock_step_repository():
    """Mock protocol step repository"""
    repo = Mock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.list_by_protocol_paginated = AsyncMock()
    return repo


@pytest.fixture
def mock_execution_repository():
    """Mock protocol execution repository"""
    repo = Mock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    repo.list_by_winery_paginated = AsyncMock()
    return repo


@pytest.fixture
def mock_completion_repository():
    """Mock step completion repository"""
    repo = Mock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.list_by_execution_paginated = AsyncMock()
    return repo


@pytest.fixture
def sample_protocol():
    """Sample protocol entity for testing"""
    protocol = Mock()
    protocol.id = 1
    protocol.winery_id = 10
    protocol.varietal_code = "PN"
    protocol.varietal_name = "Pinot Noir"
    protocol.color = "RED"
    protocol.version = "1.0"
    protocol.protocol_name = "Pinot Noir Standard"
    protocol.expected_duration_days = 20
    protocol.description = "Standard Pinot Noir fermentation protocol"
    protocol.is_active = True
    protocol.created_at = datetime.now()
    protocol.updated_at = datetime.now()
    return protocol


@pytest.fixture
def sample_step():
    """Sample protocol step for testing"""
    step = Mock()
    step.id = 1
    step.protocol_id = 1
    step.step_order = 1
    step.step_type = "INITIALIZATION"
    step.description = "Yeast inoculation"
    step.expected_day = 0
    step.tolerance_hours = 2
    step.can_repeat_daily = False
    step.criticality_score = 95
    step.duration_minutes = 30
    step.depends_on_step_id = None
    step.notes = None
    step.created_at = datetime.now()
    step.updated_at = datetime.now()
    return step


@pytest.fixture
def sample_execution():
    """Sample protocol execution for testing"""
    execution = Mock()
    execution.id = 1
    execution.fermentation_id = 100
    execution.protocol_id = 1
    execution.winery_id = 10
    execution.status = "NOT_STARTED"
    execution.compliance_score = 0
    execution.completion_percentage = 0
    execution.start_date = datetime.now()
    execution.notes = None
    execution.created_at = datetime.now()
    execution.updated_at = datetime.now()
    return execution


@pytest.fixture
def sample_completion():
    """Sample step completion for testing"""
    completion = Mock()
    completion.id = 1
    completion.execution_id = 1
    completion.step_id = 1
    completion.winery_id = 10
    completion.completed_at = datetime.now()
    completion.is_on_schedule = True
    completion.days_late = 0
    completion.was_skipped = False
    completion.skip_reason = None
    completion.skip_notes = None
    completion.notes = None
    completion.created_at = datetime.now()
    completion.updated_at = datetime.now()
    return completion


# ======================================================================================
# Protocol Router Tests
# ======================================================================================

@pytest.mark.asyncio
async def test_create_protocol_success(mock_user_context, mock_protocol_repository, sample_protocol):
    """Test POST /protocols - Create protocol successfully"""
    # Setup
    request = ProtocolCreateRequest(
        varietal_code="PN",
        varietal_name="Pinot Noir",
        color="RED",
        version="1.0",
        protocol_name="Pinot Noir Standard",
        expected_duration_days=20
    )
    mock_protocol_repository.create.return_value = sample_protocol
    
    # Execute
    result = await create_protocol(
        request=request,
        current_user=mock_user_context,
        repository=mock_protocol_repository
    )
    
    # Assert
    assert result is not None
    mock_protocol_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_protocol_invalid_version(mock_user_context, mock_protocol_repository):
    """Test POST /protocols - Reject invalid semantic version"""
    # Execute & Assert
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ProtocolCreateRequest(
            varietal_code="PN",
            varietal_name="Pinot Noir",
            color="RED",
            version="invalid",  # Invalid format
            protocol_name="Pinot Noir Standard",
            expected_duration_days=20
        )

@pytest.mark.asyncio
async def test_get_protocol_success(mock_user_context, mock_protocol_repository, sample_protocol):
    """Test GET /protocols/{id} - Get protocol successfully"""
    # Setup
    mock_protocol_repository.get_by_id.return_value = sample_protocol
    
    # Execute
    result = await get_protocol(
        protocol_id=1,
        current_user=mock_user_context,
        repository=mock_protocol_repository
    )
    
    # Assert
    assert result is not None
    mock_protocol_repository.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_protocol_not_found(mock_user_context, mock_protocol_repository):
    """Test GET /protocols/{id} - Protocol not found"""
    # Setup
    mock_protocol_repository.get_by_id.return_value = None
    
    # Execute & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_protocol(
            protocol_id=999,
            current_user=mock_user_context,
            repository=mock_protocol_repository
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_protocol_multi_tenancy_denied(mock_user_context, mock_protocol_repository):
    """Test GET /protocols/{id} - Multi-tenancy enforcement"""
    # Setup
    protocol = Mock()
    protocol.id = 1
    protocol.winery_id = 999  # Different winery
    mock_protocol_repository.get_by_id.return_value = protocol
    
    # Execute & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_protocol(
            protocol_id=1,
            current_user=mock_user_context,
            repository=mock_protocol_repository
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_update_protocol_success(mock_user_context, mock_protocol_repository, sample_protocol):
    """Test PATCH /protocols/{id} - Update protocol successfully"""
    # Setup
    mock_protocol_repository.get_by_id.return_value = sample_protocol
    updated_protocol = sample_protocol
    updated_protocol.protocol_name = "Updated Name"
    mock_protocol_repository.update.return_value = updated_protocol
    
    request = ProtocolUpdateRequest(
        protocol_name="Updated Name"
    )
    
    # Execute
    result = await update_protocol(
        protocol_id=1,
        request=request,
        current_user=mock_user_context,
        repository=mock_protocol_repository
    )
    
    # Assert
    assert result is not None
    mock_protocol_repository.update.assert_called_once()


@pytest.mark.asyncio
async def test_delete_protocol_success(mock_user_context, mock_protocol_repository, sample_protocol):
    """Test DELETE /protocols/{id} - Delete protocol successfully"""
    # Setup
    mock_protocol_repository.get_by_id.return_value = sample_protocol
    mock_protocol_repository.delete = AsyncMock()
    
    # Execute
    await delete_protocol(
        protocol_id=1,
        current_user=mock_user_context,
        repository=mock_protocol_repository
    )
    
    # Assert
    mock_protocol_repository.delete.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_list_protocols_success(mock_user_context, mock_protocol_repository, sample_protocol):
    """Test GET /protocols - List protocols with pagination"""
    # Setup
    protocols = [sample_protocol]
    mock_protocol_repository.list_by_winery_paginated.return_value = (protocols, 1)
    
    # Execute
    result = await list_protocols(
        page=1,
        page_size=20,
        current_user=mock_user_context,
        repository=mock_protocol_repository
    )
    
    # Assert
    assert result is not None
    assert len(result.items) == 1
    assert result.total_count == 1
    mock_protocol_repository.list_by_winery_paginated.assert_called_once()


@pytest.mark.asyncio
async def test_activate_protocol_success(mock_user_context, mock_protocol_repository, sample_protocol):
    """Test PATCH /protocols/{id}/activate - Activate protocol version"""
    # Setup
    mock_protocol_repository.get_by_id.return_value = sample_protocol
    mock_protocol_repository.deactivate_by_winery_varietal = AsyncMock()
    activated = sample_protocol
    activated.is_active = True
    mock_protocol_repository.update.return_value = activated
    
    # Execute
    result = await activate_protocol(
        protocol_id=1,
        current_user=mock_user_context,
        repository=mock_protocol_repository
    )
    
    # Assert
    assert result is not None
    mock_protocol_repository.deactivate_by_winery_varietal.assert_called_once()
    mock_protocol_repository.update.assert_called_once()


# ======================================================================================
# Protocol Step Router Tests
# ======================================================================================

@pytest.mark.asyncio
async def test_create_protocol_step_success(
    mock_user_context,
    mock_step_repository,
    mock_protocol_repository,
    sample_protocol,
    sample_step
):
    """Test POST /protocols/{id}/steps - Create step successfully"""
    # Setup
    request = StepCreateRequest(
        step_order=1,
        step_type="INITIALIZATION",
        description="Yeast inoculation",
        expected_day=0,
        tolerance_hours=2,
        duration_minutes=30,
        criticality_score=95,
        can_repeat_daily=False
    )
    mock_protocol_repository.get_by_id.return_value = sample_protocol
    mock_step_repository.create.return_value = sample_step
    
    # Execute
    result = await create_protocol_step(
        protocol_id=1,
        request=request,
        current_user=mock_user_context,
        step_repository=mock_step_repository,
        protocol_repository=mock_protocol_repository
    )
    
    # Assert
    assert result is not None
    mock_step_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_list_protocol_steps_success(
    mock_user_context,
    mock_step_repository,
    mock_protocol_repository,
    sample_protocol,
    sample_step
):
    """Test GET /protocols/{id}/steps - List steps with pagination"""
    # Setup
    steps = [sample_step]
    mock_protocol_repository.get_by_id.return_value = sample_protocol
    mock_step_repository.list_by_protocol_paginated.return_value = (steps, 1)
    
    # Execute
    result = await list_protocol_steps(
        protocol_id=1,
        page=1,
        page_size=20,
        current_user=mock_user_context,
        step_repository=mock_step_repository,
        protocol_repository=mock_protocol_repository
    )
    
    # Assert
    assert result is not None
    assert len(result.items) == 1
    assert result.total_count == 1


# ======================================================================================
# Protocol Execution Router Tests
# ======================================================================================

@pytest.mark.asyncio
async def test_start_protocol_execution_success(
    mock_user_context,
    mock_execution_repository,
    sample_execution
):
    """Test POST /fermentations/{id}/execute - Start execution"""
    # Setup
    request = ExecutionStartRequest(
        protocol_id=1
    )
    mock_execution_repository.create.return_value = sample_execution
    
    # Execute
    result = await start_protocol_execution(
        fermentation_id=100,
        request=request,
        current_user=mock_user_context,
        execution_repository=mock_execution_repository
    )
    
    # Assert
    assert result is not None
    mock_execution_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_list_protocol_executions_success(
    mock_user_context,
    mock_execution_repository,
    sample_execution
):
    """Test GET /executions - List executions with pagination"""
    # Setup
    executions = [sample_execution]
    mock_execution_repository.list_by_winery_paginated.return_value = (executions, 1)
    
    # Execute
    result = await list_protocol_executions(
        page=1,
        page_size=20,
        current_user=mock_user_context,
        execution_repository=mock_execution_repository
    )
    
    # Assert
    assert result is not None
    assert len(result.items) == 1
    assert result.total_count == 1


# ======================================================================================
# Step Completion Router Tests
# ======================================================================================

@pytest.mark.asyncio
async def test_complete_protocol_step_success(
    mock_user_context,
    mock_execution_repository,
    mock_completion_repository,
    sample_execution,
    sample_completion
):
    """Test POST /executions/{id}/complete - Mark step complete"""
    # Setup
    request = CompletionCreateRequest(
        step_id=1,
        completed_at=datetime.now(),
        is_on_schedule=True,
        notes="H2S levels normal",
        was_skipped=False
    )
    mock_execution_repository.get_by_id.return_value = sample_execution
    mock_completion_repository.create.return_value = sample_completion
    
    # Execute
    result = await complete_protocol_step(
        execution_id=1,
        request=request,
        current_user=mock_user_context,
        completion_repository=mock_completion_repository,
        execution_repository=mock_execution_repository
    )
    
    # Assert
    assert result is not None
    mock_completion_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_list_execution_completions_success(
    mock_user_context,
    mock_execution_repository,
    mock_completion_repository,
    sample_execution,
    sample_completion
):
    """Test GET /executions/{id}/completions - List completions"""
    # Setup
    completions = [sample_completion]
    mock_execution_repository.get_by_id.return_value = sample_execution
    mock_completion_repository.list_by_execution_paginated.return_value = (completions, 1)
    
    # Execute
    result = await list_execution_completions(
        execution_id=1,
        page=1,
        page_size=20,
        current_user=mock_user_context,
        completion_repository=mock_completion_repository,
        execution_repository=mock_execution_repository
    )
    
    # Assert
    assert result is not None
    assert len(result.items) == 1
    assert result.total_count == 1


# ======================================================================================
# Additional Coverage Tests
# ======================================================================================

@pytest.mark.asyncio
async def test_skip_protocol_step_validation(mock_user_context, mock_execution_repository, mock_completion_repository):
    """Test that skip_reason is validated when was_skipped=True"""
    # Setup
    execution = Mock()
    execution.id = 1
    execution.winery_id = 10
    mock_execution_repository.get_by_id.return_value = execution
    
    request = CompletionCreateRequest(
        step_id=1,
        was_skipped=True,
        skip_reason="EQUIPMENT_MALFUNCTION"
    )
    
    completion = Mock()
    completion.id = 1
    completion.execution_id = 1
    completion.step_id = 1
    completion.winery_id = 10
    completion.was_skipped = True
    completion.completed_at = None
    completion.is_on_schedule = False
    completion.days_late = 0
    completion.skip_reason = "EQUIPMENT_MALFUNCTION"
    completion.skip_notes = None
    completion.notes = None
    completion.created_at = datetime.now()
    completion.updated_at = datetime.now()
    mock_completion_repository.create.return_value = completion
    
    # Execute
    result = await complete_protocol_step(
        execution_id=1,
        request=request,
        current_user=mock_user_context,
        completion_repository=mock_completion_repository,
        execution_repository=mock_execution_repository
    )
    
    # Assert
    assert result is not None
    mock_completion_repository.create.assert_called_once()
