"""
Sample Repository Implementation.

Concrete implementation of ISampleRepository that extends BaseRepository
and provides database operations for sample management.

Following ADR-003 Separation of Concerns:
- SampleRepository handles ALL sample operations
- Fermentation operations handled by FermentationRepository
- Real SQLAlchemy queries (not mocked/hardcoded)
- Multi-tenant scoping with winery_id via fermentation relationship
- Soft delete support
- Error mapping via BaseRepository
- Returns domain entities (BaseSample)
"""

from datetime import datetime
from typing import List, Optional
from decimal import Decimal

# Import domain definitions
from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.enums.sample_type import SampleType

from src.shared.infra.repository.base_repository import BaseRepository

# NOTE: Sample entity classes (SugarSample, DensitySample, CelsiusTemperatureSample)
# are imported INSIDE methods to avoid SQLAlchemy table registration conflicts
# when running unit tests. This is CRITICAL to prevent mapper errors.


class SampleRepository(BaseRepository, ISampleRepository):
    """
    Repository for sample data operations.

    Implements ISampleRepository using SQLAlchemy ORM with BaseRepository
    infrastructure for session management, error mapping, and multi-tenant security.
    
    TDD Implementation: Building one method at a time following RED-GREEN-REFACTOR cycle.
    """

    async def create(self, sample: BaseSample) -> BaseSample:
        """
        Creates a new sample record.
        
        TDD CYCLE 1: GREEN Phase - Minimal implementation to pass test.

        Args:
            sample: BaseSample entity to create

        Returns:
            BaseSample: Created sample entity with ID populated

        Raises:
            RepositoryError: If creation fails
            IntegrityError: If constraints are violated
        """
        async def _create_operation():
            # Import SQLAlchemy entities inside method
            from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample as SQLSugarSample
            from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample as SQLDensitySample
            from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample as SQLCelsiusTemperatureSample

            session_cm = await self.get_session()
            async with session_cm as session:
                # Map domain entity to SQLAlchemy entity based on type
                if sample.sample_type == SampleType.SUGAR:
                    sql_sample = SQLSugarSample(
                        fermentation_id=sample.fermentation_id,
                        recorded_by_user_id=sample.recorded_by_user_id,
                        sample_type=sample.sample_type.value,
                        value=sample.value,
                        units=sample.units,
                        recorded_at=sample.recorded_at,
                    )
                elif sample.sample_type == SampleType.DENSITY:
                    sql_sample = SQLDensitySample(
                        fermentation_id=sample.fermentation_id,
                        recorded_by_user_id=sample.recorded_by_user_id,
                        sample_type=sample.sample_type.value,
                        value=sample.value,
                        units=sample.units,
                        recorded_at=sample.recorded_at,
                    )
                elif sample.sample_type == SampleType.TEMPERATURE:
                    sql_sample = SQLCelsiusTemperatureSample(
                        fermentation_id=sample.fermentation_id,
                        recorded_by_user_id=sample.recorded_by_user_id,
                        sample_type=sample.sample_type.value,
                        value=sample.value,
                        units=sample.units,
                        recorded_at=sample.recorded_at,
                    )
                else:
                    # Generic BaseSample for other types
                    from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample as SQLBaseSample
                    sql_sample = SQLBaseSample(
                        fermentation_id=sample.fermentation_id,
                        recorded_by_user_id=sample.recorded_by_user_id,
                        sample_type=sample.sample_type.value,
                        value=sample.value,
                        units=sample.units,
                        recorded_at=sample.recorded_at,
                    )

                session.add(sql_sample)
                await session.flush()
                await session.refresh(sql_sample)

                # Map back to domain entity
                return self._map_to_domain(sql_sample)

        return await self.execute_with_error_mapping(_create_operation)

    def _map_to_domain(self, sql_sample) -> BaseSample:
        """
        Maps SQLAlchemy sample entity to domain BaseSample.
        
        Helper method to convert database entity to domain entity.
        """
        # Import sample entity classes inside method to avoid mapper conflicts
        from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
        from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
        from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
        
        sample_type = SampleType(sql_sample.sample_type)
        
        if sample_type == SampleType.SUGAR:
            return SugarSample(
                id=sql_sample.id,
                fermentation_id=sql_sample.fermentation_id,
                sample_type=sample_type,
                value=sql_sample.value,
                units=sql_sample.units,
                recorded_at=sql_sample.recorded_at,
                created_at=sql_sample.created_at,
                updated_at=sql_sample.updated_at,
            )
        elif sample_type == SampleType.DENSITY:
            return DensitySample(
                id=sql_sample.id,
                fermentation_id=sql_sample.fermentation_id,
                sample_type=sample_type,
                value=sql_sample.value,
                units=sql_sample.units,
                recorded_at=sql_sample.recorded_at,
                created_at=sql_sample.created_at,
                updated_at=sql_sample.updated_at,
            )
        elif sample_type == SampleType.TEMPERATURE:
            return CelsiusTemperatureSample(
                id=sql_sample.id,
                fermentation_id=sql_sample.fermentation_id,
                sample_type=sample_type,
                value=sql_sample.value,
                units=sql_sample.units,
                recorded_at=sql_sample.recorded_at,
                created_at=sql_sample.created_at,
                updated_at=sql_sample.updated_at,
            )
        else:
            # Generic BaseSample
            return BaseSample(
                id=sql_sample.id,
                fermentation_id=sql_sample.fermentation_id,
                sample_type=sample_type,
                value=sql_sample.value,
                units=sql_sample.units,
                recorded_at=sql_sample.recorded_at,
                created_at=sql_sample.created_at,
                updated_at=sql_sample.updated_at,
            )

    # =====================================================================
    # Remaining methods from ISampleRepository - NOT YET IMPLEMENTED
    # Will be implemented in subsequent TDD cycles
    # =====================================================================

    async def upsert_sample(self, sample: BaseSample) -> BaseSample:
        """NOT YET IMPLEMENTED - Next TDD cycle."""
        raise NotImplementedError("TDD: Implement in next cycle")

    async def get_sample_by_id(self, sample_id: int, fermentation_id: Optional[int] = None) -> BaseSample:
        """NOT YET IMPLEMENTED - Next TDD cycle."""
        raise NotImplementedError("TDD: Implement in next cycle")

    async def get_samples_by_fermentation_id(self, fermentation_id: int) -> List[BaseSample]:
        """NOT YET IMPLEMENTED - Next TDD cycle."""
        raise NotImplementedError("TDD: Implement in next cycle")

    async def get_samples_in_timerange(
        self,
        fermentation_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[BaseSample]:
        """NOT YET IMPLEMENTED - Next TDD cycle."""
        raise NotImplementedError("TDD: Implement in next cycle")

    async def get_latest_sample(self, fermentation_id: int) -> Optional[BaseSample]:
        """NOT YET IMPLEMENTED - Next TDD cycle."""
        raise NotImplementedError("TDD: Implement in next cycle")

    async def get_fermentation_start_date(self, fermentation_id: int) -> datetime:
        """NOT YET IMPLEMENTED - Next TDD cycle."""
        raise NotImplementedError("TDD: Implement in next cycle")

    async def get_latest_sample_by_type(
        self,
        fermentation_id: int,
        sample_type: SampleType
    ) -> Optional[BaseSample]:
        """NOT YET IMPLEMENTED - Next TDD cycle."""
        raise NotImplementedError("TDD: Implement in next cycle")

    async def check_duplicate_timestamp(
        self,
        fermentation_id: int,
        sample: BaseSample,
        exclude_sample_id: Optional[int] = None
    ) -> bool:
        """NOT YET IMPLEMENTED - Next TDD cycle."""
        raise NotImplementedError("TDD: Implement in next cycle")

    async def soft_delete_sample(self, sample_id: int) -> None:
        """NOT YET IMPLEMENTED - Next TDD cycle."""
        raise NotImplementedError("TDD: Implement in next cycle")

    async def bulk_upsert_samples(self, samples: List[BaseSample]) -> List[BaseSample]:
        """NOT YET IMPLEMENTED - Next TDD cycle."""
        raise NotImplementedError("TDD: Implement in next cycle")
