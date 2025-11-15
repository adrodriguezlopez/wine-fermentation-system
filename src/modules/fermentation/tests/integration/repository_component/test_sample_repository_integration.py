"""
Integration tests for SampleRepository.

These tests validate repository operations against real PostgreSQL database,
ensuring that:
- Data persists correctly
- SQLAlchemy mappings work
- Queries return expected results  
- Transactions and rollbacks work properly

Database: localhost:5433/wine_fermentation_test
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select

from src.modules.fermentation.src.domain.enums.sample_type import SampleType

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestSampleRepositoryIntegration:
    """Integration tests for SampleRepository with real database."""

    @pytest.mark.asyncio
    async def test_create_sugar_sample_persists_to_database(
        self, 
        test_models,
        sample_repository, 
        test_fermentation,
        test_user,
        db_session
    ):
        """
        Test that create() persists SugarSample to PostgreSQL.
        
        GIVEN a valid SugarSample entity
        WHEN create() is called
        THEN the sample should be persisted with ID assigned
        AND should be retrievable from the database
        AND should have correct sample_type polymorphic discrimination
        """
        # Arrange: Create SugarSample domain entity
        SugarSample = test_models['SugarSample']
        
        sample = SugarSample(
            fermentation_id=test_fermentation.id,
            recorded_by_user_id=test_user.id,
            sample_type=SampleType.SUGAR,
            value=Decimal("18.5"),
            units="brix",
            recorded_at=datetime(2024, 10, 4, 10, 0, 0),
        )
        
        # Act: Create sample using repository
        result = await sample_repository.create(sample)
        
        # Assert: Verify returned entity
        assert result is not None, "create() should return BaseSample entity"
        assert result.id is not None, "Persisted sample should have ID assigned"
        assert result.fermentation_id == test_fermentation.id
        assert result.sample_type == SampleType.SUGAR
        assert result.value == Decimal("18.5")
        assert result.units == "brix"
        assert result.recorded_at == datetime(2024, 10, 4, 10, 0, 0)
        
        # Verify: Check database persistence
        query = select(SugarSample).where(SugarSample.id == result.id)
        db_result = await db_session.execute(query)
        persisted_sample = db_result.scalar_one_or_none()
        
        assert persisted_sample is not None, "Sample should be persisted in database"
        assert persisted_sample.id == result.id
        assert persisted_sample.fermentation_id == test_fermentation.id
        assert persisted_sample.sample_type == "sugar", "Polymorphic discriminator should be 'sugar'"
        assert persisted_sample.value == Decimal("18.5")
        assert persisted_sample.units == "brix"
