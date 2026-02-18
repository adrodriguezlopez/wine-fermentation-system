"""
Integration tests for RecommendationTemplateRepository.

Tests cover all methods of IRecommendationTemplateRepository interface with real database operations.
"""
import pytest
from uuid import uuid4

from src.modules.analysis_engine.src.domain.entities.recommendation_template import RecommendationTemplate
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.recommendation_category import RecommendationCategory


@pytest.mark.integration
class TestRecommendationTemplateRepositoryAdd:
    """Test adding new templates."""

    @pytest.mark.asyncio
    async def test_add_template_success(self, recommendation_template_repository, db_session):
        """Test adding a new template successfully."""
        template = RecommendationTemplate(
            code="TEMP_CRITICAL",
            category=RecommendationCategory.TEMPERATURE_ADJUSTMENT.value,
            title="Critical Temperature Adjustment",
            description="Adjust temperature for critical situations",
            applicable_anomaly_types=[AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.value],
            priority_default=1
        )
        db_session.add(template)
        await db_session.flush()
        
        added = await recommendation_template_repository.add(template)
        
        assert added is not None
        assert added.id == template.id
        assert added.code == "TEMP_CRITICAL"


@pytest.mark.integration
class TestRecommendationTemplateRepositoryGetById:
    """Test template retrieval by ID."""

    @pytest.mark.asyncio
    async def test_get_existing_template(self, recommendation_template_repository, db_session):
        """Test getting an existing template."""
        template = RecommendationTemplate(
            code="PH_BALANCE",
            category=RecommendationCategory.NUTRIENT_ADDITION.value,
            title="pH Balancing",
            description="Balance pH levels",
            applicable_anomaly_types=[AnomalyType.VOLATILE_ACIDITY_HIGH.value],
            priority_default=2
        )
        db_session.add(template)
        await db_session.flush()
        
        retrieved = await recommendation_template_repository.get_by_id(template.id)
        
        assert retrieved is not None
        assert retrieved.id == template.id
        assert retrieved.code == "PH_BALANCE"

    @pytest.mark.asyncio
    async def test_get_nonexistent_template_returns_none(self, recommendation_template_repository):
        """Test getting a nonexistent template returns None."""
        result = await recommendation_template_repository.get_by_id(uuid4())
        assert result is None


@pytest.mark.integration
class TestRecommendationTemplateRepositoryGetByCode:
    """Test template retrieval by code."""

    @pytest.mark.asyncio
    async def test_get_by_code(self, recommendation_template_repository, db_session):
        """Test getting template by unique code."""
        template = RecommendationTemplate(
            code="DENSITY_CHECK",
            category=RecommendationCategory.MONITORING.value,
            title="Density Monitoring",
            description="Monitor specific gravity",
            applicable_anomaly_types=[AnomalyType.DENSITY_DROP_TOO_FAST.value],
            priority_default=2
        )
        db_session.add(template)
        await db_session.flush()
        
        retrieved = await recommendation_template_repository.get_by_code("DENSITY_CHECK")
        
        assert retrieved is not None
        assert retrieved.code == "DENSITY_CHECK"
        assert retrieved.title == "Density Monitoring"

    @pytest.mark.asyncio
    async def test_get_by_code_nonexistent_returns_none(self, recommendation_template_repository):
        """Test getting template by nonexistent code returns None."""
        result = await recommendation_template_repository.get_by_code("NONEXISTENT_CODE")
        assert result is None


@pytest.mark.integration
class TestRecommendationTemplateRepositoryListByCategory:
    """Test listing templates by category."""

    @pytest.mark.asyncio
    async def test_list_by_category(self, recommendation_template_repository, db_session):
        """Test listing templates by category."""
        template1 = RecommendationTemplate(
            code="TEMP_UP",
            category=RecommendationCategory.TEMPERATURE_ADJUSTMENT.value,
            title="Increase Temperature",
            description="Increase fermentation temperature",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1,
            is_active=True
        )
        template2 = RecommendationTemplate(
            code="TEMP_DOWN",
            category=RecommendationCategory.TEMPERATURE_ADJUSTMENT.value,
            title="Decrease Temperature",
            description="Decrease fermentation temperature",
            applicable_anomaly_types=[AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.value],
            priority_default=1,
            is_active=True
        )
        template3 = RecommendationTemplate(
            code="NUTRIENT_ADD",
            category=RecommendationCategory.NUTRIENT_ADDITION.value,
            title="Add Nutrients",
            description="Add specific nutrients",
            applicable_anomaly_types=[AnomalyType.HYDROGEN_SULFIDE_RISK.value],
            priority_default=2,
            is_active=True
        )
        db_session.add_all([template1, template2, template3])
        await db_session.flush()
        
        temp_templates = await recommendation_template_repository.list_by_category(
            RecommendationCategory.TEMPERATURE_ADJUSTMENT
        )
        
        assert len(temp_templates) == 2
        assert all(t.category == RecommendationCategory.TEMPERATURE_ADJUSTMENT.value for t in temp_templates)


@pytest.mark.integration
class TestRecommendationTemplateRepositoryListByAnomalyType:
    """Test listing templates by anomaly type."""

    @pytest.mark.asyncio
    async def test_list_by_anomaly_type(self, recommendation_template_repository, db_session):
        """Test listing templates applicable to anomaly type."""
        template1 = RecommendationTemplate(
            code="STUCK_FIX_1",
            category=RecommendationCategory.TEMPERATURE_ADJUSTMENT.value,
            title="Fix Stuck 1",
            description="First way to fix stuck fermentation",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1,
            is_active=True
        )
        template2 = RecommendationTemplate(
            code="STUCK_FIX_2",
            category=RecommendationCategory.RE_INOCULATION.value,
            title="Fix Stuck 2",
            description="Second way to fix stuck fermentation",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=2,
            is_active=True
        )
        db_session.add_all([template1, template2])
        await db_session.flush()
        
        templates = await recommendation_template_repository.list_by_anomaly_type(
            AnomalyType.STUCK_FERMENTATION
        )
        
        assert len(templates) == 2
        assert all(AnomalyType.STUCK_FERMENTATION.value in t.applicable_anomaly_types for t in templates)


@pytest.mark.integration
class TestRecommendationTemplateRepositoryListActive:
    """Test listing active templates."""

    @pytest.mark.asyncio
    async def test_list_active(self, recommendation_template_repository, db_session):
        """Test listing active templates only."""
        active_template = RecommendationTemplate(
            code="ACTIVE_TEMPLATE",
            category=RecommendationCategory.MONITORING.value,
            title="Active Template",
            description="This is active",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1,
            is_active=True
        )
        inactive_template = RecommendationTemplate(
            code="INACTIVE_TEMPLATE",
            category=RecommendationCategory.MONITORING.value,
            title="Inactive Template",
            description="This is inactive",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1,
            is_active=False
        )
        db_session.add_all([active_template, inactive_template])
        await db_session.flush()
        
        active_templates = await recommendation_template_repository.list_active()
        
        assert len(active_templates) >= 1
        assert all(t.is_active for t in active_templates)


@pytest.mark.integration
class TestRecommendationTemplateRepositoryListAll:
    """Test listing all templates."""

    @pytest.mark.asyncio
    async def test_list_all(self, recommendation_template_repository, db_session):
        """Test listing all templates including inactive."""
        template = RecommendationTemplate(
            code="TEST_TEMPLATE_ALL",
            category=RecommendationCategory.AERATION.value,
            title="Test Template",
            description="For testing list_all",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1,
            is_active=True
        )
        db_session.add(template)
        await db_session.flush()
        
        all_templates = await recommendation_template_repository.list_all()
        
        assert len(all_templates) >= 1
        assert any(t.code == "TEST_TEMPLATE_ALL" for t in all_templates)


@pytest.mark.integration
class TestRecommendationTemplateRepositoryUpdate:
    """Test updating templates."""

    @pytest.mark.asyncio
    async def test_update_template(self, recommendation_template_repository, db_session):
        """Test updating an existing template."""
        template = RecommendationTemplate(
            code="UPDATE_TEST",
            category=RecommendationCategory.PREVENTIVE.value,
            title="Original Title",
            description="Original description",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1,
            is_active=True
        )
        db_session.add(template)
        await db_session.flush()
        
        template.title = "Updated Title"
        template.priority_default = 2
        
        updated = await recommendation_template_repository.update(template)
        
        assert updated.title == "Updated Title"
        assert updated.priority_default == 2


@pytest.mark.integration
class TestRecommendationTemplateRepositoryDelete:
    """Test deleting templates."""

    @pytest.mark.asyncio
    async def test_delete_template(self, recommendation_template_repository, db_session):
        """Test deleting an existing template."""
        template = RecommendationTemplate(
            code="DELETE_TEST",
            category=RecommendationCategory.MONITORING.value,
            title="To Be Deleted",
            description="This will be deleted",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1,
            is_active=True
        )
        db_session.add(template)
        await db_session.flush()
        template_id = template.id
        
        result = await recommendation_template_repository.delete(template_id)
        
        assert result is True
        
        # Verify it's deleted
        retrieved = await recommendation_template_repository.get_by_id(template_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, recommendation_template_repository):
        """Test deleting nonexistent template returns False."""
        result = await recommendation_template_repository.delete(uuid4())
        assert result is False


@pytest.mark.integration
class TestRecommendationTemplateRepositoryCountActive:
    """Test counting active templates."""

    @pytest.mark.asyncio
    async def test_count_active(self, recommendation_template_repository, db_session):
        """Test counting active templates."""
        # Add active template
        active = RecommendationTemplate(
            code="COUNT_ACTIVE_TEST",
            category=RecommendationCategory.MONITORING.value,
            title="Active for Count",
            description="For counting active",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1,
            is_active=True
        )
        db_session.add(active)
        await db_session.flush()
        
        count = await recommendation_template_repository.count_active()
        
        assert count >= 1


@pytest.mark.integration
class TestRecommendationTemplateRepositoryGetMostUsed:
    """Test getting most used templates."""

    @pytest.mark.asyncio
    async def test_get_most_used(self, recommendation_template_repository, db_session):
        """Test getting most used templates ordered by times_applied."""
        template1 = RecommendationTemplate(
            code="MOST_USED_1",
            category=RecommendationCategory.MONITORING.value,
            title="Template 1",
            description="Most used",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1,
            is_active=True,
            times_applied=10
        )
        template2 = RecommendationTemplate(
            code="MOST_USED_2",
            category=RecommendationCategory.MONITORING.value,
            title="Template 2",
            description="Less used",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1,
            is_active=True,
            times_applied=5
        )
        db_session.add_all([template1, template2])
        await db_session.flush()
        
        most_used = await recommendation_template_repository.get_most_used(limit=2)
        
        assert len(most_used) >= 1
        # Check ordering - most used first
        if len(most_used) >= 2:
            assert most_used[0].times_applied >= most_used[1].times_applied
