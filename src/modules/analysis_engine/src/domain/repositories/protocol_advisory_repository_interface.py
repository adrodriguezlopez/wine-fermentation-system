"""
Repository interface for ProtocolAdvisory entity (ADR-037).
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.protocol_advisory import ProtocolAdvisory
from ..enums.advisory_type import AdvisoryType
from ..enums.risk_level import RiskLevel


class IProtocolAdvisoryRepository(ABC):
    """
    Repository interface for ProtocolAdvisory entity.

    Advisories are created by the Analysis Engine and consumed by winemakers
    via the UI. They are scoped by fermentation_id (not winery_id directly,
    since the fermentation already carries the winery context).
    """

    @abstractmethod
    async def add(self, advisory: ProtocolAdvisory) -> ProtocolAdvisory:
        """
        Persist a new ProtocolAdvisory.

        Args:
            advisory: Unsaved ProtocolAdvisory returned by ProtocolAnalysisIntegrationService

        Returns:
            The persisted advisory (id + created_at populated)
        """
        pass

    @abstractmethod
    async def add_many(self, advisories: List[ProtocolAdvisory]) -> List[ProtocolAdvisory]:
        """
        Persist multiple advisories in one flush (batch insert).

        Args:
            advisories: List of unsaved ProtocolAdvisory objects

        Returns:
            List of persisted advisories
        """
        pass

    @abstractmethod
    async def get_by_id(self, advisory_id: UUID) -> Optional[ProtocolAdvisory]:
        """
        Retrieve an advisory by primary key.

        Args:
            advisory_id: UUID of the advisory

        Returns:
            Advisory if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_fermentation_id(
        self,
        fermentation_id: UUID,
        include_acknowledged: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ProtocolAdvisory]:
        """
        List all advisories for a fermentation, most recent first.

        Args:
            fermentation_id: Target fermentation
            include_acknowledged: If False, only returns unacknowledged advisories
            skip: Pagination offset
            limit: Max results

        Returns:
            List of ProtocolAdvisory objects
        """
        pass

    @abstractmethod
    async def get_by_analysis_id(self, analysis_id: UUID) -> List[ProtocolAdvisory]:
        """
        List advisories generated for a specific analysis run.

        Args:
            analysis_id: The analysis that triggered these advisories

        Returns:
            List of ProtocolAdvisory objects
        """
        pass

    @abstractmethod
    async def get_unacknowledged_by_fermentation_id(
        self,
        fermentation_id: UUID,
    ) -> List[ProtocolAdvisory]:
        """
        List pending (unacknowledged) advisories for a fermentation.

        Used by the UI to show the winemaker what requires attention.

        Args:
            fermentation_id: Target fermentation

        Returns:
            Unacknowledged advisories, sorted critical-first
        """
        pass

    @abstractmethod
    async def acknowledge(self, advisory_id: UUID) -> Optional[ProtocolAdvisory]:
        """
        Mark an advisory as acknowledged by the winemaker.

        Sets is_acknowledged=True and acknowledged_at=now().

        Args:
            advisory_id: Advisory to acknowledge

        Returns:
            Updated advisory, or None if not found
        """
        pass

    @abstractmethod
    async def list_by_risk_level(
        self,
        fermentation_id: UUID,
        risk_level: RiskLevel,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ProtocolAdvisory]:
        """
        List advisories filtered by risk level for a fermentation.

        Args:
            fermentation_id: Target fermentation
            risk_level: Risk level filter (CRITICAL, HIGH, MEDIUM, LOW)
            skip: Pagination offset
            limit: Max results

        Returns:
            Matching advisories
        """
        pass

    @abstractmethod
    async def list_by_advisory_type(
        self,
        fermentation_id: UUID,
        advisory_type: AdvisoryType,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ProtocolAdvisory]:
        """
        List advisories filtered by advisory type for a fermentation.

        Args:
            fermentation_id: Target fermentation
            advisory_type: ACCELERATE_STEP, SKIP_STEP or ADD_STEP
            skip: Pagination offset
            limit: Max results

        Returns:
            Matching advisories
        """
        pass

    @abstractmethod
    async def count_unacknowledged(self, fermentation_id: UUID) -> int:
        """
        Count pending (unacknowledged) advisories for a fermentation.

        Useful for dashboard badge counts.

        Args:
            fermentation_id: Target fermentation

        Returns:
            Number of unacknowledged advisories
        """
        pass
