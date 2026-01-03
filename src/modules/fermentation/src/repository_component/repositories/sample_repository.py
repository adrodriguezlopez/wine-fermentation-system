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

Implements ADR-027 Structured Logging:
- LogTimer for database operation timing
- Automatic context binding (fermentation_id, sample_type)
- Query performance metrics
- Security audit trail (WHO recorded WHAT WHEN)
"""

from datetime import datetime
from typing import List, Optional
from decimal import Decimal

# ADR-027: Structured logging
from src.shared.wine_fermentator_logging import get_logger, LogTimer

# Import domain definitions
from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.enums.sample_type import SampleType

from src.shared.infra.repository.base_repository import BaseRepository

logger = get_logger(__name__)

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
            with LogTimer(logger, "create_sample"):
                # Import SQLAlchemy entities inside method
                from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample as SQLSugarSample
                from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample as SQLDensitySample
                from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample as SQLCelsiusTemperatureSample

                # Map domain entity to SQLAlchemy entity based on type
                sample_type_value = sample.sample_type if isinstance(sample.sample_type, str) else sample.sample_type.value
                
                logger.info(
                    "creating_sample",
                    fermentation_id=sample.fermentation_id,
                    sample_type=sample_type_value,
                    recorded_by_user_id=sample.recorded_by_user_id,
                    value=float(sample.value) if sample.value else None
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    if sample_type_value == SampleType.SUGAR.value or sample.sample_type == SampleType.SUGAR:
                        sql_sample = SQLSugarSample(
                            fermentation_id=sample.fermentation_id,
                            recorded_by_user_id=sample.recorded_by_user_id,
                            sample_type=sample_type_value,
                            value=sample.value,
                            units=sample.units,
                            recorded_at=sample.recorded_at,
                        )
                    elif sample_type_value == SampleType.DENSITY.value or sample.sample_type == SampleType.DENSITY:
                        sql_sample = SQLDensitySample(
                            fermentation_id=sample.fermentation_id,
                            recorded_by_user_id=sample.recorded_by_user_id,
                            sample_type=sample_type_value,
                            value=sample.value,
                            units=sample.units,
                            recorded_at=sample.recorded_at,
                        )
                    elif sample_type_value == SampleType.TEMPERATURE.value or sample.sample_type == SampleType.TEMPERATURE:
                        sql_sample = SQLCelsiusTemperatureSample(
                            fermentation_id=sample.fermentation_id,
                            recorded_by_user_id=sample.recorded_by_user_id,
                            sample_type=sample_type_value,
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
                            sample_type=sample_type_value,
                            value=sample.value,
                            units=sample.units,
                            recorded_at=sample.recorded_at,
                        )

                    session.add(sql_sample)
                    await session.flush()
                    await session.refresh(sql_sample)
                    
                    logger.info(
                        "sample_created",
                        sample_id=sql_sample.id,
                        fermentation_id=sample.fermentation_id,
                        sample_type=sample_type_value
                    )

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
    # ISampleRepository Interface Implementation
    # =====================================================================

    async def upsert_sample(self, sample: BaseSample) -> BaseSample:
        """
        Upsert a sample (create or update).
        
        Args:
            sample: BaseSample entity
            
        Returns:
            Updated/created BaseSample
        """
        if sample.id is None:
            return await self.create(sample)
        else:
            return await self.update(sample)

    async def get_sample_by_id(
        self, 
        sample_id: int,
        fermentation_id: int,
        winery_id: int
    ) -> Optional[BaseSample]:
        """
        Retrieves a sample by its ID with winery access control.
        
        Args:
            sample_id: ID of the sample to retrieve
            fermentation_id: Fermentation ID for access control
            winery_id: Winery ID for multi-tenant security (REQUIRED per ADR-025)
            
        Returns:
            Optional[BaseSample]: Sample entity or None if not found or access denied
            
        Security:
            Validates that sample belongs to fermentation AND fermentation belongs to winery.
            Returns None if access denied (cross-winery attempt).
        """
        # ADR-025 LIGHT: Validate winery_id parameter
        if not winery_id or winery_id <= 0:
            raise ValueError(f"winery_id is REQUIRED for multi-tenancy security, got: {winery_id}")
        
        async def _get_operation():
            with LogTimer(logger, "get_sample_by_id"):
                logger.debug(
                    "fetching_sample",
                    sample_id=sample_id,
                    fermentation_id=fermentation_id,
                    winery_id=winery_id
                )
                
                from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
                from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
                from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
                from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
                from sqlalchemy import select
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    # Query all sample types with JOIN to fermentation for winery_id validation
                    for sample_class in [SugarSample, DensitySample, CelsiusTemperatureSample]:
                        stmt = (
                            select(sample_class)
                            .join(Fermentation, sample_class.fermentation_id == Fermentation.id)
                            .where(
                                sample_class.id == sample_id,
                                sample_class.fermentation_id == fermentation_id,
                                Fermentation.winery_id == winery_id  # ADR-025: winery_id validation
                            )
                        )
                        
                        result = await session.execute(stmt)
                        sample = result.scalar_one_or_none()
                        
                        if sample is not None:
                            logger.debug(
                                "sample_found",
                                sample_id=sample_id,
                                fermentation_id=fermentation_id,
                                winery_id=winery_id,
                                sample_type=sample.sample_type
                            )
                            return sample
                
                    # Not found or access denied (cross-winery attempt)
                    logger.warning(
                        "sample_not_found_or_access_denied",
                        sample_id=sample_id,
                        fermentation_id=fermentation_id,
                        winery_id=winery_id
                    )
                    return None
        
        return await self.execute_with_error_mapping(_get_operation)

    async def get_samples_by_fermentation_id(self, fermentation_id: int) -> List[BaseSample]:
        """
        Retrieves all samples for a fermentation.
        
        Args:
            fermentation_id: ID of the fermentation
            
        Returns:
            List of samples in chronological order
        """
        with LogTimer(logger, "get_samples_by_fermentation"):
            logger.debug(
                "querying_samples_by_fermentation",
                fermentation_id=fermentation_id
            )
            from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
            from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
            from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
            from sqlalchemy import select
            
            session_cm = await self.get_session()
            async with session_cm as session:
                samples = []
                
                # Collect samples from all types
                for sample_class in [SugarSample, DensitySample, CelsiusTemperatureSample]:
                    stmt = select(sample_class).where(
                        sample_class.fermentation_id == fermentation_id
                    ).order_by(sample_class.recorded_at.asc())
                    
                    result = await session.execute(stmt)
                    samples.extend(result.scalars().all())
                
                # Sort all samples chronologically
                samples.sort(key=lambda s: s.recorded_at)
                
                logger.info(
                    "samples_retrieved_by_fermentation",
                    fermentation_id=fermentation_id,
                    count=len(samples)
                )
                
                return samples
            
            return samples


    async def get_samples_in_timerange(
        self,
        fermentation_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[BaseSample]:
        """
        Get samples in a time range.
        
        Args:
            fermentation_id: ID of the fermentation
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of samples in the range
        """
        from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
        from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
        from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
        from sqlalchemy import select
        
        session_cm = await self.get_session()
        async with session_cm as session:
            samples = []
            
            for sample_class in [SugarSample, DensitySample, CelsiusTemperatureSample]:
                stmt = select(sample_class).where(
                    sample_class.fermentation_id == fermentation_id,
                    sample_class.recorded_at >= start_time,
                    sample_class.recorded_at <= end_time
                ).order_by(sample_class.recorded_at.asc())
                
                result = await session.execute(stmt)
                samples.extend(result.scalars().all())
            
            samples.sort(key=lambda s: s.recorded_at)
            return samples

    async def get_latest_sample(self, fermentation_id: int) -> Optional[BaseSample]:
        """
        Get the most recent sample for a fermentation.
        
        Args:
            fermentation_id: ID of the fermentation
            
        Returns:
            Most recent BaseSample or None
        """
        samples = await self.get_samples_by_fermentation_id(fermentation_id)
        
        if not samples:
            return None
        
        # Samples are already sorted chronologically, get last one
        return samples[-1]

    async def get_fermentation_start_date(self, fermentation_id: int) -> datetime:
        """Get fermentation start date."""
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
        from sqlalchemy import select
        
        session_cm = await self.get_session()
        async with session_cm as session:
            stmt = select(Fermentation.start_date).where(Fermentation.id == fermentation_id)
            result = await session.execute(stmt)
            start_date = result.scalar_one_or_none()
            
            return start_date  # Return None if not found

    async def get_latest_sample_by_type(
        self,
        fermentation_id: int,
        sample_type: SampleType
    ) -> Optional[BaseSample]:
        """
        Get the most recent sample of a specific type.
        
        Args:
            fermentation_id: ID of the fermentation
            sample_type: Type of sample to filter
            
        Returns:
            Most recent sample of that type or None
        """
        from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
        from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
        from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
        from sqlalchemy import select
        
        session_cm = await self.get_session()
        async with session_cm as session:
            # Map sample type to entity class
            sample_class_map = {
                SampleType.SUGAR: SugarSample,
                SampleType.DENSITY: DensitySample,
                SampleType.TEMPERATURE: CelsiusTemperatureSample
            }
            
            sample_class = sample_class_map.get(sample_type)
            if not sample_class:
                return None
            
            stmt = select(sample_class).where(
                sample_class.fermentation_id == fermentation_id
            ).order_by(sample_class.recorded_at.desc()).limit(1)
            
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def check_duplicate_timestamp(
        self,
        fermentation_id: int,
        sample: BaseSample,
        exclude_sample_id: Optional[int] = None
    ) -> bool:
        """
        Check if a sample with the same timestamp already exists.
        
        Args:
            fermentation_id: ID of the fermentation
            sample: Sample to check
            exclude_sample_id: Optional ID to exclude from check
            
        Returns:
            True if duplicate exists, False otherwise
        """
        from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
        from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
        from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
        from sqlalchemy import select
        
        session_cm = await self.get_session()
        async with session_cm as session:
            # Map sample type to entity class
            sample_class_map = {
                SampleType.SUGAR: SugarSample,
                SampleType.DENSITY: DensitySample,
                SampleType.TEMPERATURE: CelsiusTemperatureSample
            }
            
            sample_class = sample_class_map.get(sample.sample_type)
            if not sample_class:
                return False
            
            stmt = select(sample_class).where(
                sample_class.fermentation_id == fermentation_id,
                sample_class.recorded_at == sample.recorded_at
            )
            
            if exclude_sample_id is not None:
                stmt = stmt.where(sample_class.id != exclude_sample_id)
            
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            return existing is not None

    async def soft_delete_sample(self, sample_id: int) -> None:
        """
        Soft delete a sample.
        
        Args:
            sample_id: ID of sample to delete
        """
        from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
        from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
        from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
        from sqlalchemy import update
        
        session_cm = await self.get_session()
        async with session_cm as session:
            # Try to update in each table
            for sample_class in [SugarSample, DensitySample, CelsiusTemperatureSample]:
                stmt = update(sample_class).where(
                    sample_class.id == sample_id
                ).values(is_deleted=True)
                
                result = await session.execute(stmt)
                
                if result.rowcount > 0:
                    await session.commit()
                    return
            
            # Not found - just return without error

    async def bulk_upsert_samples(self, samples: List[BaseSample]) -> List[BaseSample]:
        """
        Bulk upsert samples.
        
        Args:
            samples: List of samples to upsert
            
        Returns:
            List of upserted samples
        """
        result = []
        for sample in samples:
            upserted = await self.upsert_sample(sample)
            result.append(upserted)
        return result

    async def list_by_data_source(
        self, fermentation_id: int, data_source: str, winery_id: int
    ) -> List[BaseSample]:
        """
        Retrieves samples filtered by data source (ADR-029).
        
        Multi-tenant secured by winery_id via fermentation relationship.
        
        Args:
            fermentation_id: Fermentation ID to filter samples
            data_source: Data source value to filter by
            winery_id: Winery ID for multi-tenant scoping
            
        Returns:
            List of samples matching criteria
        """
        from sqlalchemy import select
        from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
        from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
        from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
        
        async def _list_by_data_source_operation():
            with LogTimer(logger, "list_samples_by_data_source"):
                logger.debug(
                    "querying_samples_by_data_source",
                    fermentation_id=fermentation_id,
                    data_source=data_source,
                    winery_id=winery_id
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    all_samples = []
                    
                    # Query each sample type table
                    for sample_class in [SugarSample, DensitySample, CelsiusTemperatureSample]:
                        query = (
                            select(sample_class)
                            .join(Fermentation, sample_class.fermentation_id == Fermentation.id)
                            .where(
                                sample_class.fermentation_id == fermentation_id,
                                sample_class.data_source == data_source,
                                Fermentation.winery_id == winery_id
                            )
                        )
                        result = await session.execute(query)
                        samples = result.scalars().all()
                        all_samples.extend(samples)
                    
                    logger.info(
                        "samples_retrieved_by_data_source",
                        fermentation_id=fermentation_id,
                        data_source=data_source,
                        winery_id=winery_id,
                        count=len(all_samples)
                    )
                    
                    return list(all_samples)
        
        return await self.execute_with_error_mapping(_list_by_data_source_operation)

