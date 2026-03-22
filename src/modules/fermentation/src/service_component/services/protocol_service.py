"""
Protocol Service for Fermentation Protocol Management

Provides high-level protocol operations:
- CRUD operations (create, read, update, delete)
- Protocol activation and versioning
- Execution lifecycle management
- Integration with compliance tracking
- Multi-tenant support with winery scoping
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.enums.step_type import ProtocolExecutionStatus
from src.modules.fermentation.src.repository_component.fermentation_protocol_repository import FermentationProtocolRepository
from src.modules.fermentation.src.repository_component.protocol_execution_repository import ProtocolExecutionRepository
from src.modules.fermentation.src.repository_component.protocol_step_repository import ProtocolStepRepository
from src.modules.fermentation.src.service_component.services.protocol_compliance_service import ProtocolComplianceService


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ProtocolSummary:
    """Summary of a protocol for listing."""
    id: int
    winery_id: int
    varietal_name: str
    version: str
    protocol_name: str
    is_active: bool
    step_count: int
    expected_duration_days: int
    created_at: datetime
    updated_at: Optional[datetime]


@dataclass
class ProtocolDetail:
    """Full protocol details with all steps."""
    id: int
    winery_id: int
    varietal_code: str
    varietal_name: str
    color: str
    version: str
    protocol_name: str
    description: str
    expected_duration_days: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    steps: List[Dict]  # Step details


@dataclass
class ExecutionStartResult:
    """Result of starting protocol execution."""
    execution_id: int
    fermentation_id: int
    protocol_id: int
    start_date: datetime
    status: str
    compliance_score: float


# ============================================================================
# Protocol Service
# ============================================================================

class ProtocolService:
    """
    High-level service for protocol management and execution.
    
    Provides:
    - Protocol CRUD operations with multi-tenancy
    - Protocol activation and versioning
    - Execution lifecycle management
    - Integration with compliance tracking
    """

    def __init__(
        self,
        protocol_repository: FermentationProtocolRepository,
        execution_repository: ProtocolExecutionRepository,
        step_repository: ProtocolStepRepository,
        compliance_service: ProtocolComplianceService,
    ):
        """Initialize service with repository and service dependencies."""
        self.protocol_repo = protocol_repository
        self.execution_repo = execution_repository
        self.step_repo = step_repository
        self.compliance_service = compliance_service

    # ========================================================================
    # Protocol CRUD Operations
    # ========================================================================

    async def create_protocol(
        self,
        winery_id: int,
        varietal_code: str,
        varietal_name: str,
        color: str,
        version: str,
        protocol_name: str,
        description: str,
        expected_duration_days: int,
    ) -> FermentationProtocol:
        """
        Create a new fermentation protocol.

        Args:
            winery_id: Owning winery
            varietal_code: Short code (e.g., "PN", "CS")
            varietal_name: Full name (e.g., "Pinot Noir")
            color: Wine color ("RED", "WHITE", "ROSÉ")
            version: Semantic version (e.g., "1.0", "2.1")
            protocol_name: Human-readable name
            description: Long description
            expected_duration_days: Estimated fermentation duration

        Returns:
            Created FermentationProtocol entity

        Raises:
            ValueError: If validation fails or protocol already exists
        """
        # Check for duplicate (winery, varietal, version combo)
        existing = await self.protocol_repo.get_by_winery_varietal_version(
            winery_id, varietal_code, version
        )
        if existing:
            raise ValueError(
                f"Protocol {varietal_code} v{version} already exists for winery {winery_id}"
            )

        # Create protocol
        protocol = FermentationProtocol(
            winery_id=winery_id,
            varietal_code=varietal_code,
            varietal_name=varietal_name,
            color=color,
            version=version,
            protocol_name=protocol_name,
            description=description,
            expected_duration_days=expected_duration_days,
            is_active=False,  # New protocols are inactive by default
        )

        # Persist
        await self.protocol_repo.create(protocol)
        await self.protocol_repo.session.commit()

        return protocol

    async def get_protocol(
        self,
        protocol_id: int,
        winery_id: int,
    ) -> FermentationProtocol:
        """
        Get protocol by ID with multi-tenant check.

        Args:
            protocol_id: ID of protocol
            winery_id: Requesting winery (for access control)

        Returns:
            FermentationProtocol entity

        Raises:
            ValueError: If protocol not found or access denied
        """
        protocol = await self.protocol_repo.get_by_id(protocol_id)
        if not protocol:
            raise ValueError(f"Protocol {protocol_id} not found")

        # Verify winery access
        if protocol.winery_id != winery_id:
            raise ValueError(
                f"Access denied: Protocol {protocol_id} belongs to winery {protocol.winery_id}"
            )

        return protocol

    async def update_protocol(
        self,
        protocol_id: int,
        winery_id: int,
        **updates,
    ) -> FermentationProtocol:
        """
        Update protocol fields.

        Args:
            protocol_id: ID of protocol to update
            winery_id: Requesting winery (for access control)
            **updates: Fields to update (name, description, expected_duration_days, etc.)

        Returns:
            Updated FermentationProtocol entity

        Raises:
            ValueError: If protocol not found, access denied, or update invalid
        """
        protocol = await self.get_protocol(protocol_id, winery_id)

        # Update allowed fields
        allowed_fields = {
            "protocol_name",
            "description",
            "expected_duration_days",
        }

        for field, value in updates.items():
            if field not in allowed_fields:
                raise ValueError(f"Cannot update field: {field}")
            setattr(protocol, field, value)

        protocol.updated_at = datetime.utcnow()

        # Persist
        await self.protocol_repo.update(protocol)
        await self.protocol_repo.session.commit()

        return protocol

    async def delete_protocol(
        self,
        protocol_id: int,
        winery_id: int,
    ) -> bool:
        """
        Delete a protocol (soft or hard delete).

        Args:
            protocol_id: ID of protocol to delete
            winery_id: Requesting winery (for access control)

        Returns:
            True if deleted

        Raises:
            ValueError: If protocol not found, access denied, or has active executions
        """
        protocol = await self.get_protocol(protocol_id, winery_id)

        # Check for active executions
        active_executions = await self.execution_repo.get_by_protocol(protocol_id)
        if any(e.status == "ACTIVE" for e in active_executions):
            raise ValueError(
                f"Cannot delete protocol {protocol_id}: has active executions"
            )

        # Delete
        await self.protocol_repo.delete(protocol_id)
        await self.protocol_repo.session.commit()

        return True

    async def list_protocols(
        self,
        winery_id: int,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ProtocolSummary], int]:
        """
        List protocols for a winery with pagination.

        Args:
            winery_id: Filter by winery
            is_active: Filter by active status (None = both)
            limit: Results per page (1-100)
            offset: Pagination offset

        Returns:
            Tuple of (protocol summaries, total count)
        """
        # Validate pagination
        limit = max(1, min(limit, 100))

        # Get protocols
        protocols, total = await self.protocol_repo.list_by_winery(
            winery_id=winery_id,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

        # Convert to summaries
        summaries = [
            ProtocolSummary(
                id=p.id,
                winery_id=p.winery_id,
                varietal_name=p.varietal_name,
                version=p.version,
                protocol_name=p.protocol_name,
                is_active=p.is_active,
                step_count=len(p.steps) if p.steps else 0,
                expected_duration_days=p.expected_duration_days,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in protocols
        ]

        return summaries, total

    async def get_protocol_detail(
        self,
        protocol_id: int,
        winery_id: int,
    ) -> ProtocolDetail:
        """
        Get full protocol detail including all steps.

        Args:
            protocol_id: ID of protocol
            winery_id: Requesting winery

        Returns:
            ProtocolDetail with all steps

        Raises:
            ValueError: If protocol not found or access denied
        """
        protocol = await self.get_protocol(protocol_id, winery_id)

        # Convert steps to dictionaries
        step_details = [
            {
                "id": s.id,
                "step_order": s.step_order,
                "step_type": s.step_type.value,
                "description": s.description,
                "expected_day": s.expected_day,
                "tolerance_hours": s.tolerance_hours,
                "duration_minutes": s.duration_minutes,
                "is_critical": s.is_critical,
                "criticality_score": s.criticality_score,
            }
            for s in (protocol.steps or [])
        ]

        return ProtocolDetail(
            id=protocol.id,
            winery_id=protocol.winery_id,
            varietal_code=protocol.varietal_code,
            varietal_name=protocol.varietal_name,
            color=protocol.color,
            version=protocol.version,
            protocol_name=protocol.protocol_name,
            description=protocol.description,
            expected_duration_days=protocol.expected_duration_days,
            is_active=protocol.is_active,
            created_at=protocol.created_at,
            updated_at=protocol.updated_at,
            steps=step_details,
        )

    # ========================================================================
    # Protocol Activation
    # ========================================================================

    async def activate_protocol(
        self,
        protocol_id: int,
        winery_id: int,
    ) -> FermentationProtocol:
        """
        Activate a protocol (mark as ready for use).

        Args:
            protocol_id: ID of protocol to activate
            winery_id: Requesting winery

        Returns:
            Activated FermentationProtocol

        Raises:
            ValueError: If protocol not found, access denied, or already active
        """
        protocol = await self.get_protocol(protocol_id, winery_id)

        if protocol.is_active:
            raise ValueError(f"Protocol {protocol_id} is already active")

        # Verify protocol has steps
        if not protocol.steps or len(protocol.steps) == 0:
            raise ValueError(
                f"Cannot activate protocol {protocol_id}: no steps defined"
            )

        protocol.is_active = True
        protocol.updated_at = datetime.utcnow()

        await self.protocol_repo.update(protocol)
        await self.protocol_repo.session.commit()

        return protocol

    async def deactivate_protocol(
        self,
        protocol_id: int,
        winery_id: int,
    ) -> FermentationProtocol:
        """
        Deactivate a protocol (mark as not ready for use).

        Args:
            protocol_id: ID of protocol to deactivate
            winery_id: Requesting winery

        Returns:
            Deactivated FermentationProtocol

        Raises:
            ValueError: If protocol not found or access denied
        """
        protocol = await self.get_protocol(protocol_id, winery_id)

        if not protocol.is_active:
            raise ValueError(f"Protocol {protocol_id} is already inactive")

        protocol.is_active = False
        protocol.updated_at = datetime.utcnow()

        await self.protocol_repo.update(protocol)
        await self.protocol_repo.session.commit()

        return protocol

    # ========================================================================
    # Execution Management
    # ========================================================================

    async def start_execution(
        self,
        protocol_id: int,
        fermentation_id: int,
        winery_id: int,
        start_date: Optional[datetime] = None,
    ) -> ExecutionStartResult:
        """
        Start protocol execution for a fermentation.

        Args:
            protocol_id: ID of protocol to execute
            fermentation_id: ID of fermentation to link
            winery_id: Winery ID (for access control)
            start_date: When fermentation started (default: now)

        Returns:
            ExecutionStartResult with execution details

        Raises:
            ValueError: If protocol not found, not active, or execution already exists
        """
        # Verify protocol
        protocol = await self.get_protocol(protocol_id, winery_id)
        if not protocol.is_active:
            raise ValueError(f"Protocol {protocol_id} is not active")

        # Check for existing execution
        existing = await self.execution_repo.get_by_fermentation(fermentation_id)
        if existing:
            raise ValueError(
                f"Fermentation {fermentation_id} already has active execution"
            )

        # Create execution
        start_date = start_date or datetime.utcnow()
        execution = ProtocolExecution(
            fermentation_id=fermentation_id,
            protocol_id=protocol_id,
            winery_id=winery_id,
            start_date=start_date,
            status="NOT_STARTED",
            compliance_score=0.0,
            completed_steps=0,
            skipped_critical_steps=0,
        )

        # Persist
        await self.execution_repo.create(execution)
        await self.execution_repo.session.commit()

        return ExecutionStartResult(
            execution_id=execution.id,
            fermentation_id=fermentation_id,
            protocol_id=protocol_id,
            start_date=execution.start_date,
            status=execution.status,
            compliance_score=execution.compliance_score,
        )

    async def get_execution(
        self,
        execution_id: int,
        winery_id: int,
    ) -> ProtocolExecution:
        """
        Get execution with multi-tenant check.

        Args:
            execution_id: ID of execution
            winery_id: Requesting winery

        Returns:
            ProtocolExecution entity

        Raises:
            ValueError: If execution not found or access denied
        """
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        # Verify winery access
        if execution.winery_id != winery_id:
            raise ValueError(
                f"Access denied: Execution {execution_id} belongs to winery {execution.winery_id}"
            )

        return execution

    async def list_executions(
        self,
        protocol_id: int,
        winery_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        """
        List executions for a protocol with pagination.

        Args:
            protocol_id: Filter by protocol
            winery_id: Filter by winery (access control)
            status: Filter by status (optional)
            limit: Results per page
            offset: Pagination offset

        Returns:
            Tuple of (executions, total count)
        """
        # Verify protocol access
        protocol = await self.get_protocol(protocol_id, winery_id)

        # Get executions
        executions, total = await self.execution_repo.list_by_protocol(
            protocol_id=protocol_id,
            status=status,
            limit=limit,
            offset=offset,
        )

        # Convert to dictionaries
        execution_dicts = [
            {
                "id": e.id,
                "fermentation_id": e.fermentation_id,
                "status": e.status,
                "start_date": e.start_date,
                "completed_at": e.completed_at,
                "compliance_score": e.compliance_score,
                "completed_steps": e.completed_steps,
                "skipped_critical_steps": e.skipped_critical_steps,
            }
            for e in executions
        ]

        return execution_dicts, total

    async def update_execution_status(
        self,
        execution_id: int,
        winery_id: int,
        new_status: str,
    ) -> ProtocolExecution:
        """
        Update execution status (IN_PROGRESS, COMPLETED, PAUSED, ABANDONED).

        Args:
            execution_id: ID of execution
            winery_id: Requesting winery
            new_status: New status value

        Returns:
            Updated ProtocolExecution

        Raises:
            ValueError: If execution not found, access denied, or status invalid
        """
        execution = await self.get_execution(execution_id, winery_id)

        # Validate status
        valid_statuses = {
            "NOT_STARTED",
            "ACTIVE",
            "PAUSED",
            "COMPLETED",
            "ABANDONED",
        }
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        # Handle transitions
        if new_status == "COMPLETED" and execution.status != "ACTIVE":
            raise ValueError(
                f"Cannot complete execution: status is {execution.status}, must be ACTIVE"
            )

        execution.status = new_status
        if new_status == "COMPLETED":
            execution.completed_at = datetime.utcnow()

        await self.execution_repo.update(execution)
        await self.execution_repo.session.commit()

        return execution

    # ========================================================================
    # ADR-039: Template Management
    # ========================================================================

    async def clone_protocol(
        self,
        source_protocol_id: int,
        winery_id: int,
        new_version: str,
        new_protocol_name: Optional[str] = None,
    ) -> FermentationProtocol:
        """
        Clone an existing protocol into a new version, copying all steps.

        The cloned protocol starts inactive so the winemaker can modify it
        before activating it. All steps are deep-copied with new IDs.

        Args:
            source_protocol_id: ID of the protocol to clone from
            winery_id: Requesting winery (access control)
            new_version: Version for the cloned protocol (e.g. "2.0")
            new_protocol_name: Optional override for the name; defaults to
                               "<original_name> v<new_version>"

        Returns:
            Newly created (inactive) FermentationProtocol with copied steps

        Raises:
            ValueError: Protocol not found, access denied, or version conflict
        """
        import re
        if not re.match(r"^\d+\.\d+$", new_version):
            raise ValueError("new_version must be semantic format (e.g. '2.0')")

        source = await self.get_protocol(source_protocol_id, winery_id)

        # Ensure the new version does not already exist
        existing = await self.protocol_repo.get_by_winery_varietal_version(
            winery_id, source.varietal_code, new_version
        )
        if existing:
            raise ValueError(
                f"Protocol {source.varietal_code} v{new_version} already exists "
                f"for winery {winery_id}"
            )

        name = new_protocol_name or f"{source.protocol_name} v{new_version}"

        cloned = FermentationProtocol(
            winery_id=winery_id,
            created_by_user_id=source.created_by_user_id,
            varietal_code=source.varietal_code,
            varietal_name=source.varietal_name,
            color=source.color,
            protocol_name=name,
            version=new_version,
            description=source.description,
            expected_duration_days=source.expected_duration_days,
            is_active=False,
        )
        await self.protocol_repo.create(cloned)
        await self.protocol_repo.session.flush()

        # Deep-copy all steps (preserve order; drop IDs and dependency links
        # that reference old step IDs to avoid FK violations)
        source_steps = await self.step_repo.get_by_protocol(source_protocol_id)
        for s in sorted(source_steps, key=lambda x: x.step_order):
            new_step = ProtocolStep(
                protocol_id=cloned.id,
                step_order=s.step_order,
                step_type=s.step_type,
                description=s.description,
                expected_day=s.expected_day,
                tolerance_hours=s.tolerance_hours,
                duration_minutes=s.duration_minutes,
                is_critical=s.is_critical,
                criticality_score=s.criticality_score,
                can_repeat_daily=s.can_repeat_daily,
                notes=s.notes,
                depends_on_step_id=None,  # Reset cross-step deps (old IDs invalid)
            )
            await self.step_repo.create(new_step)

        await self.protocol_repo.session.commit()
        return cloned

    async def add_custom_step(
        self,
        protocol_id: int,
        winery_id: int,
        step_order: int,
        step_type: str,
        description: str,
        expected_day: int,
        tolerance_hours: int,
        duration_minutes: int,
        criticality_score: float,
        is_critical: bool = False,
        can_repeat_daily: bool = False,
        notes: Optional[str] = None,
    ) -> ProtocolStep:
        """
        Inject a custom step into an existing (inactive) protocol.

        The step is inserted at *step_order*. All existing steps with
        step_order >= the given value are shifted up by 1 to make room.

        Args:
            protocol_id: ID of the protocol to modify
            winery_id: Requesting winery (access control)
            step_order: Desired position for the new step (1-indexed)
            step_type: Step category enum value
            description: Specific step details
            expected_day: Day when step occurs (0 = crush day)
            tolerance_hours: Allowed time window ± hours
            duration_minutes: Estimated duration
            criticality_score: Importance 0-100
            is_critical: Whether skipping this step is a critical deviation
            can_repeat_daily: Whether step repeats each day
            notes: Optional free-text notes

        Returns:
            Newly created ProtocolStep

        Raises:
            ValueError: Protocol not found, access denied, or protocol is active
        """
        protocol = await self.get_protocol(protocol_id, winery_id)

        if protocol.is_active:
            raise ValueError(
                f"Cannot modify protocol {protocol_id}: it is active. "
                "Clone it first to create an editable version."
            )

        # Shift existing steps to make room
        existing_steps = await self.step_repo.get_by_protocol(protocol_id)
        for s in existing_steps:
            if s.step_order >= step_order:
                s.step_order += 1
                await self.step_repo.update(s)

        new_step = ProtocolStep(
            protocol_id=protocol_id,
            step_order=step_order,
            step_type=step_type,
            description=description,
            expected_day=expected_day,
            tolerance_hours=tolerance_hours,
            duration_minutes=duration_minutes,
            is_critical=is_critical,
            criticality_score=criticality_score,
            can_repeat_daily=can_repeat_daily,
            notes=notes,
        )
        await self.step_repo.create(new_step)
        await self.step_repo.session.commit()
        return new_step

    async def override_step(
        self,
        protocol_id: int,
        step_id: int,
        winery_id: int,
        **changes,
    ) -> ProtocolStep:
        """
        Override parameters of an existing step in an inactive protocol.

        Only the fields listed in *overridable_fields* can be changed.
        The protocol must be inactive — clone it first if it is active.

        Args:
            protocol_id: ID of the owning protocol (for access control)
            step_id: ID of the step to modify
            winery_id: Requesting winery
            **changes: Fields to update and their new values

        Returns:
            Updated ProtocolStep

        Raises:
            ValueError: Protocol/step not found, access denied, protocol active,
                        or attempt to update a non-overridable field
        """
        overridable_fields = {
            "description",
            "expected_day",
            "tolerance_hours",
            "duration_minutes",
            "is_critical",
            "criticality_score",
            "can_repeat_daily",
            "notes",
        }

        protocol = await self.get_protocol(protocol_id, winery_id)

        if protocol.is_active:
            raise ValueError(
                f"Cannot modify protocol {protocol_id}: it is active. "
                "Clone it first to create an editable version."
            )

        step = await self.step_repo.get_by_id(step_id)
        if step is None:
            raise ValueError(f"Step {step_id} not found")
        if step.protocol_id != protocol_id:
            raise ValueError(
                f"Step {step_id} does not belong to protocol {protocol_id}"
            )

        for field, value in changes.items():
            if field not in overridable_fields:
                raise ValueError(f"Field '{field}' cannot be overridden")
            setattr(step, field, value)

        await self.step_repo.update(step)
        await self.step_repo.session.commit()
        return step

    # ========================================================================
    # Compliance Integration
    # ========================================================================

    async def get_execution_compliance(
        self,
        execution_id: int,
        winery_id: int,
    ) -> Dict:
        """
        Get compliance score and breakdown for an execution.

        Args:
            execution_id: ID of execution
            winery_id: Requesting winery

        Returns:
            Dictionary with compliance details

        Raises:
            ValueError: If execution not found or access denied
        """
        execution = await self.get_execution(execution_id, winery_id)

        # Calculate compliance
        score_result = await self.compliance_service.calculate_compliance_score(
            execution_id
        )

        return {
            "execution_id": execution_id,
            "compliance_score": score_result.compliance_score,
            "weighted_completion": score_result.weighted_completion,
            "timing_score": score_result.timing_score,
            "critical_steps_completion_pct": score_result.critical_steps_completion_pct,
            "breakdown": {
                "completion": {
                    "score": score_result.breakdown["completion"].score,
                    "total_earned": score_result.breakdown["completion"].total_earned,
                    "total_possible": score_result.breakdown["completion"].total_possible,
                    "completed_count": score_result.breakdown["completion"].completed_count,
                    "skipped_count": score_result.breakdown["completion"].skipped_count,
                    "pending_count": score_result.breakdown["completion"].pending_count,
                },
                "timing": {
                    "score": score_result.breakdown["timing"].score,
                    "on_time_count": score_result.breakdown["timing"].on_time_count,
                    "late_count": score_result.breakdown["timing"].late_count,
                },
            },
        }

    async def get_protocol_execution_status(
        self,
        execution_id: int,
        winery_id: int,
    ) -> Dict:
        """
        Get complete execution status including compliance and deviations.

        Args:
            execution_id: ID of execution
            winery_id: Requesting winery

        Returns:
            Dictionary with full execution status

        Raises:
            ValueError: If execution not found or access denied
        """
        execution = await self.get_execution(execution_id, winery_id)

        # Get status from compliance service
        status = await self.compliance_service.get_execution_status(execution_id)

        return status

    # ========================================================================
    # ADR-039: Template Lifecycle Management
    # ========================================================================

    async def list_templates(
        self,
        winery_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[FermentationProtocol], int]:
        """
        List master-template protocols (is_template=True) for a winery.

        Args:
            winery_id: Owning winery
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (templates list, total count)
        """
        return await self.protocol_repo.list_templates_paginated(
            winery_id=winery_id, page=page, page_size=page_size
        )

    async def approve_template(
        self,
        protocol_id: int,
        winery_id: int,
        approver_user_id: int,
    ) -> FermentationProtocol:
        """
        Transition a DRAFT template to FINAL (approved for use).

        Args:
            protocol_id: Template to approve
            winery_id: Owning winery (access control)
            approver_user_id: ID of the admin/winemaker approving

        Returns:
            Updated FermentationProtocol in FINAL state

        Raises:
            ValueError: If protocol not found, not a template, or not in DRAFT state
        """
        from src.modules.fermentation.src.domain.enums.step_type import ProtocolState

        protocol = await self.get_protocol(protocol_id, winery_id)

        if not protocol.is_template:
            raise ValueError(
                f"Protocol {protocol_id} is a fermentation instance, not a template"
            )
        if protocol.state != ProtocolState.DRAFT:
            raise ValueError(
                f"Only DRAFT templates can be approved. "
                f"Current state: {protocol.state}"
            )

        protocol.state = ProtocolState.FINAL
        protocol.approved_by_user_id = approver_user_id
        protocol.updated_at = datetime.utcnow()

        await self.protocol_repo.update(protocol)
        await self.protocol_repo.session.commit()
        return protocol

    async def deprecate_template(
        self,
        protocol_id: int,
        winery_id: int,
    ) -> FermentationProtocol:
        """
        Transition a FINAL template to DEPRECATED (retired, no new instances).

        A deprecated template becomes inactive as well so it no longer appears
        in normal protocol lists.

        Args:
            protocol_id: Template to deprecate
            winery_id: Owning winery (access control)

        Returns:
            Updated FermentationProtocol in DEPRECATED state

        Raises:
            ValueError: If protocol not found, not a template, or not in FINAL state
        """
        from src.modules.fermentation.src.domain.enums.step_type import ProtocolState

        protocol = await self.get_protocol(protocol_id, winery_id)

        if not protocol.is_template:
            raise ValueError(
                f"Protocol {protocol_id} is a fermentation instance, not a template"
            )
        if protocol.state != ProtocolState.FINAL:
            raise ValueError(
                f"Only FINAL templates can be deprecated. "
                f"Current state: {protocol.state}"
            )

        protocol.state = ProtocolState.DEPRECATED
        protocol.is_active = False
        protocol.updated_at = datetime.utcnow()

        await self.protocol_repo.update(protocol)
        await self.protocol_repo.session.commit()
        return protocol

    async def instantiate_from_template(
        self,
        template_id: int,
        winery_id: int,
        fermentation_batch_name: str,
        created_by_user_id: int,
    ) -> FermentationProtocol:
        """
        Create a per-fermentation protocol instance from a FINAL master template.

        The instance is a deep copy of the template with:
        - is_template = False
        - state = FINAL (ready to use immediately)
        - template_id pointing back to the master
        - A name scoped to the fermentation batch

        Args:
            template_id: ID of the FINAL master template to copy
            winery_id: Owning winery (access control)
            fermentation_batch_name: Name of the fermentation batch (used in instance name)
            created_by_user_id: User creating the instance

        Returns:
            Newly created FermentationProtocol instance

        Raises:
            ValueError: If template not found, not in FINAL state, or not a template
        """
        from src.modules.fermentation.src.domain.enums.step_type import ProtocolState

        template = await self.get_protocol(template_id, winery_id)

        if not template.is_template:
            raise ValueError(
                f"Protocol {template_id} is already a fermentation instance"
            )
        if template.state != ProtocolState.FINAL:
            raise ValueError(
                f"Only FINAL templates can be instantiated. "
                f"Current state: {template.state}"
            )

        instance_name = (
            f"{template.varietal_name} v{template.version} — {fermentation_batch_name}"
        )

        instance = FermentationProtocol(
            winery_id=winery_id,
            created_by_user_id=created_by_user_id,
            varietal_code=template.varietal_code,
            varietal_name=template.varietal_name,
            color=template.color,
            protocol_name=instance_name,
            version=template.version,
            description=template.description,
            expected_duration_days=template.expected_duration_days,
            is_active=True,
            is_template=False,
            state=ProtocolState.FINAL,
            template_id=template.id,
        )
        await self.protocol_repo.create(instance)
        await self.protocol_repo.session.flush()

        # Deep-copy all steps (reset dependency IDs to avoid FK violations)
        source_steps = await self.step_repo.get_by_protocol(template_id)
        for s in sorted(source_steps, key=lambda x: x.step_order):
            new_step = ProtocolStep(
                protocol_id=instance.id,
                step_order=s.step_order,
                step_type=s.step_type,
                description=s.description,
                expected_day=s.expected_day,
                tolerance_hours=s.tolerance_hours,
                duration_minutes=s.duration_minutes,
                is_critical=s.is_critical,
                criticality_score=s.criticality_score,
                can_repeat_daily=s.can_repeat_daily,
                notes=s.notes,
                depends_on_step_id=None,
            )
            await self.step_repo.create(new_step)

        await self.protocol_repo.session.commit()
        return instance
