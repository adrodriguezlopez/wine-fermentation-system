"""
Unit tests for ProtocolService

Test coverage:
- Protocol CRUD operations
- Multi-tenancy enforcement
- Activation/deactivation
- Execution lifecycle
- Compliance integration
- Error handling and validation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch
from datetime import datetime, timedelta
from typing import List

from src.modules.fermentation.src.service_component.services.protocol_service import (
    ProtocolService,
    ProtocolSummary,
    ProtocolDetail,
    ExecutionStartResult,
)
from src.modules.fermentation.src.repository_component.fermentation_protocol_repository import FermentationProtocolRepository
from src.modules.fermentation.src.repository_component.protocol_execution_repository import ProtocolExecutionRepository
from src.modules.fermentation.src.repository_component.protocol_step_repository import ProtocolStepRepository
from src.modules.fermentation.src.service_component.services.protocol_compliance_service import ProtocolComplianceService
from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
from src.modules.fermentation.src.domain.enums.step_type import StepType


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_protocol_repo() -> AsyncMock:
    """Mock protocol repository."""
    mock = create_autospec(FermentationProtocolRepository, instance=True)
    mock.session = MagicMock()
    mock.session.commit = AsyncMock()
    return mock


@pytest.fixture
def mock_execution_repo() -> AsyncMock:
    """Mock execution repository."""
    mock = create_autospec(ProtocolExecutionRepository, instance=True)
    mock.session = MagicMock()
    mock.session.commit = AsyncMock()
    return mock


@pytest.fixture
def mock_step_repo() -> AsyncMock:
    """Mock step repository."""
    return create_autospec(ProtocolStepRepository, instance=True)


@pytest.fixture
def mock_compliance_service() -> AsyncMock:
    """Mock compliance service."""
    return create_autospec(ProtocolComplianceService, instance=True)


@pytest.fixture
def protocol_service(
    mock_protocol_repo,
    mock_execution_repo,
    mock_step_repo,
    mock_compliance_service,
) -> ProtocolService:
    """Create service with mock dependencies."""
    return ProtocolService(
        protocol_repository=mock_protocol_repo,
        execution_repository=mock_execution_repo,
        step_repository=mock_step_repo,
        compliance_service=mock_compliance_service,
    )


@pytest.fixture
def sample_protocol() -> MagicMock:
    """Create a mock protocol with 3 steps."""
    protocol = MagicMock(spec=FermentationProtocol)
    protocol.id = 1
    protocol.winery_id = 1
    protocol.varietal_code = "PN"
    protocol.varietal_name = "Pinot Noir"
    protocol.color = "RED"
    protocol.version = "1.0"
    protocol.protocol_name = "Pinot Noir Standard"
    protocol.description = "Standard protocol for Pinot Noir"
    protocol.expected_duration_days = 28
    protocol.is_active = False
    
    # Add mock steps
    step1 = MagicMock(spec=ProtocolStep)
    step1.id = 1
    step1.protocol_id = 1
    step1.step_order = 1
    step1.step_type = StepType.INITIALIZATION
    step1.description = "Yeast Inoculation"
    step1.expected_day = 0
    step1.tolerance_hours = 12
    step1.duration_minutes = 30
    step1.is_critical = True
    step1.criticality_score = 1.5
    
    protocol.steps = [step1]
    return protocol


@pytest.fixture
def sample_execution() -> MagicMock:
    """Create a mock execution."""
    execution = MagicMock(spec=ProtocolExecution)
    execution.id = 1
    execution.fermentation_id = 1
    execution.protocol_id = 1
    execution.winery_id = 1
    execution.start_date = datetime.utcnow()
    execution.status = "NOT_STARTED"
    execution.compliance_score = 0.0
    execution.completed_steps = 0
    execution.skipped_critical_steps = 0
    return execution


# ============================================================================
# Test Classes
# ============================================================================

class TestCreateProtocol:
    """Test protocol creation."""

    @pytest.mark.asyncio
    @patch("src.modules.fermentation.src.service_component.services.protocol_service.FermentationProtocol")
    async def test_create_protocol_success(
        self,
        mock_protocol_class,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test successful protocol creation."""
        mock_protocol_repo.get_by_winery_varietal_version = AsyncMock(
            return_value=None
        )
        # Create instance that will be returned by constructor
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.winery_id = 1
        mock_protocol_class.return_value = mock_instance
        mock_protocol_repo.create = AsyncMock()

        result = await protocol_service.create_protocol(
            winery_id=1,
            varietal_code="PN",
            varietal_name="Pinot Noir",
            color="RED",
            version="1.0",
            protocol_name="Standard PN",
            description="Pinot Noir protocol",
            expected_duration_days=28,
        )

        # Verify creation was called
        mock_protocol_repo.create.assert_called_once()
        mock_protocol_repo.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_protocol_duplicate_fails(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test that duplicate protocol creation fails."""
        mock_protocol_repo.get_by_winery_varietal_version = AsyncMock(
            return_value=sample_protocol
        )

        with pytest.raises(ValueError, match="already exists"):
            await protocol_service.create_protocol(
                winery_id=1,
                varietal_code="PN",
                varietal_name="Pinot Noir",
                color="RED",
                version="1.0",
                protocol_name="Standard PN",
                description="Pinot Noir protocol",
                expected_duration_days=28,
            )


class TestGetProtocol:
    """Test protocol retrieval."""

    @pytest.mark.asyncio
    async def test_get_protocol_success(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test successful protocol retrieval."""
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)

        result = await protocol_service.get_protocol(1, 1)

        assert result.id == 1
        assert result.varietal_name == "Pinot Noir"

    @pytest.mark.asyncio
    async def test_get_protocol_not_found(
        self,
        protocol_service,
        mock_protocol_repo,
    ):
        """Test get_protocol when protocol not found."""
        mock_protocol_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await protocol_service.get_protocol(999, 1)

    @pytest.mark.asyncio
    async def test_get_protocol_access_denied(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test get_protocol with wrong winery."""
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)

        with pytest.raises(ValueError, match="Access denied"):
            await protocol_service.get_protocol(1, 999)  # Different winery


class TestUpdateProtocol:
    """Test protocol updates."""

    @pytest.mark.asyncio
    async def test_update_protocol_success(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test successful protocol update."""
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)
        mock_protocol_repo.update = AsyncMock(return_value=sample_protocol)

        result = await protocol_service.update_protocol(
            1,
            1,
            protocol_name="Updated PN",
            description="Updated description",
        )

        mock_protocol_repo.update.assert_called_once()
        mock_protocol_repo.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_protocol_invalid_field(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test update with invalid field."""
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)

        with pytest.raises(ValueError, match="Cannot update field"):
            await protocol_service.update_protocol(
                protocol_id=1,
                winery_id=1,
                invalid_field=999,  # Not allowed to update
            )


class TestDeleteProtocol:
    """Test protocol deletion."""

    @pytest.mark.asyncio
    async def test_delete_protocol_success(
        self,
        protocol_service,
        mock_protocol_repo,
        mock_execution_repo,
        sample_protocol,
    ):
        """Test successful protocol deletion."""
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)
        mock_execution_repo.get_by_protocol = AsyncMock(return_value=[])
        mock_protocol_repo.delete = AsyncMock(return_value=True)

        result = await protocol_service.delete_protocol(1, 1)

        assert result is True
        mock_protocol_repo.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_protocol_with_active_execution_fails(
        self,
        protocol_service,
        mock_protocol_repo,
        mock_execution_repo,
        sample_protocol,
        sample_execution,
    ):
        """Test delete fails if protocol has active executions."""
        sample_execution.status = "ACTIVE"
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)
        mock_execution_repo.get_by_protocol = AsyncMock(
            return_value=[sample_execution]
        )

        with pytest.raises(ValueError, match="has active executions"):
            await protocol_service.delete_protocol(1, 1)


class TestListProtocols:
    """Test protocol listing."""

    @pytest.mark.asyncio
    async def test_list_protocols_success(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test successful protocol listing."""
        mock_protocol_repo.list_by_winery = AsyncMock(
            return_value=([sample_protocol], 1)
        )

        results, total = await protocol_service.list_protocols(
            winery_id=1,
            limit=50,
            offset=0,
        )

        assert len(results) == 1
        assert total == 1
        assert results[0].varietal_name == "Pinot Noir"

    @pytest.mark.asyncio
    async def test_list_protocols_respects_limit(
        self,
        protocol_service,
        mock_protocol_repo,
    ):
        """Test that pagination limit is enforced (1-100)."""
        mock_protocol_repo.list_by_winery = AsyncMock(return_value=([], 0))

        # Limit over 100 should be capped
        await protocol_service.list_protocols(winery_id=1, limit=200)
        call_limit = mock_protocol_repo.list_by_winery.call_args[1]["limit"]
        assert call_limit == 100

        # Limit 0 should be set to 1
        await protocol_service.list_protocols(winery_id=1, limit=0)
        call_limit = mock_protocol_repo.list_by_winery.call_args[1]["limit"]
        assert call_limit == 1


class TestGetProtocolDetail:
    """Test detailed protocol retrieval."""

    @pytest.mark.asyncio
    async def test_get_protocol_detail_success(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test getting full protocol detail with steps."""
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)

        result = await protocol_service.get_protocol_detail(1, 1)

        assert result.id == 1
        assert len(result.steps) == 1
        assert result.steps[0]["step_type"] == "INITIALIZATION"


class TestActivateProtocol:
    """Test protocol activation."""

    @pytest.mark.asyncio
    async def test_activate_protocol_success(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test successful protocol activation."""
        sample_protocol.is_active = False
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)
        mock_protocol_repo.update = AsyncMock(return_value=sample_protocol)

        result = await protocol_service.activate_protocol(1, 1)

        mock_protocol_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_protocol_already_active_fails(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test activate fails if already active."""
        sample_protocol.is_active = True
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)

        with pytest.raises(ValueError, match="already active"):
            await protocol_service.activate_protocol(1, 1)

    @pytest.mark.asyncio
    async def test_activate_protocol_no_steps_fails(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test activate fails if protocol has no steps."""
        sample_protocol.is_active = False
        sample_protocol.steps = []
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)

        with pytest.raises(ValueError, match="no steps"):
            await protocol_service.activate_protocol(1, 1)


class TestDeactivateProtocol:
    """Test protocol deactivation."""

    @pytest.mark.asyncio
    async def test_deactivate_protocol_success(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test successful protocol deactivation."""
        sample_protocol.is_active = True
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)
        mock_protocol_repo.update = AsyncMock(return_value=sample_protocol)

        result = await protocol_service.deactivate_protocol(1, 1)

        mock_protocol_repo.update.assert_called_once()


class TestStartExecution:
    """Test execution start."""

    @pytest.mark.asyncio
    @patch("src.modules.fermentation.src.service_component.services.protocol_service.ProtocolExecution")
    async def test_start_execution_success(
        self,
        mock_execution_class,
        protocol_service,
        mock_protocol_repo,
        mock_execution_repo,
        sample_protocol,
    ):
        """Test successful execution start."""
        sample_protocol.is_active = True
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)
        mock_execution_repo.get_by_fermentation = AsyncMock(return_value=None)
        
        # Create instance that will be returned by constructor
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.fermentation_id = 100
        mock_instance.protocol_id = 1
        mock_instance.start_date = datetime.utcnow()
        mock_instance.status = "NOT_STARTED"
        mock_instance.compliance_score = 0.0
        mock_execution_class.return_value = mock_instance
        mock_execution_repo.create = AsyncMock()

        result = await protocol_service.start_execution(
            protocol_id=1,
            fermentation_id=100,
            winery_id=1,
        )

        assert isinstance(result, ExecutionStartResult)
        assert result.protocol_id == 1
        assert result.fermentation_id == 100
        mock_execution_repo.create.assert_called_once()
        mock_execution_repo.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_execution_protocol_not_active_fails(
        self,
        protocol_service,
        mock_protocol_repo,
        sample_protocol,
    ):
        """Test start execution fails if protocol not active."""
        sample_protocol.is_active = False
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)

        with pytest.raises(ValueError, match="not active"):
            await protocol_service.start_execution(1, 100, 1)

    @pytest.mark.asyncio
    async def test_start_execution_already_exists_fails(
        self,
        protocol_service,
        mock_protocol_repo,
        mock_execution_repo,
        sample_protocol,
        sample_execution,
    ):
        """Test start execution fails if execution already exists."""
        sample_protocol.is_active = True
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)
        mock_execution_repo.get_by_fermentation = AsyncMock(
            return_value=sample_execution
        )

        with pytest.raises(ValueError, match="already has active execution"):
            await protocol_service.start_execution(1, 1, 1)


class TestGetExecution:
    """Test execution retrieval."""

    @pytest.mark.asyncio
    async def test_get_execution_success(
        self,
        protocol_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test successful execution retrieval."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)

        result = await protocol_service.get_execution(1, 1)

        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_execution_access_denied(
        self,
        protocol_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test get_execution with wrong winery."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)

        with pytest.raises(ValueError, match="Access denied"):
            await protocol_service.get_execution(1, 999)  # Different winery


class TestListExecutions:
    """Test execution listing."""

    @pytest.mark.asyncio
    async def test_list_executions_success(
        self,
        protocol_service,
        mock_protocol_repo,
        mock_execution_repo,
        sample_protocol,
        sample_execution,
    ):
        """Test successful execution listing."""
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)
        mock_execution_repo.list_by_protocol = AsyncMock(
            return_value=([sample_execution], 1)
        )

        results, total = await protocol_service.list_executions(
            protocol_id=1,
            winery_id=1,
        )

        assert len(results) == 1
        assert total == 1


class TestUpdateExecutionStatus:
    """Test execution status updates."""

    @pytest.mark.asyncio
    async def test_update_execution_status_success(
        self,
        protocol_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test successful status update."""
        sample_execution.status = "ACTIVE"
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_execution_repo.update = AsyncMock(return_value=sample_execution)

        result = await protocol_service.update_execution_status(1, 1, "COMPLETED")

        mock_execution_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_execution_status_invalid_fails(
        self,
        protocol_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test update with invalid status."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)

        with pytest.raises(ValueError, match="Invalid status"):
            await protocol_service.update_execution_status(1, 1, "INVALID_STATUS")


class TestComplianceIntegration:
    """Test compliance integration."""

    @pytest.mark.asyncio
    async def test_get_execution_compliance_success(
        self,
        protocol_service,
        mock_execution_repo,
        mock_compliance_service,
        sample_execution,
    ):
        """Test getting compliance score."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_compliance_service.calculate_compliance_score = AsyncMock(
            return_value=MagicMock(
                compliance_score=85.0,
                weighted_completion=80.0,
                timing_score=95.0,
                critical_steps_completion_pct=100.0,
                breakdown={
                    "completion": MagicMock(score=80.0, total_earned=80, total_possible=100, completed_count=2, skipped_count=0, pending_count=1),
                    "timing": MagicMock(score=95.0, on_time_count=2, late_count=0),
                },
            )
        )

        result = await protocol_service.get_execution_compliance(1, 1)

        assert result["compliance_score"] == 85.0
        assert "breakdown" in result
