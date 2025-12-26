"""
ADR-025 LIGHT: Multi-Tenancy Security Tests for GET /fermentations/{id}

Tests defense-in-depth validation:
- Repository filters by winery_id (Day 1)
- API validates explicitly (Day 2)
- Security events logged (ADR-027)

Test Coverage:
- Legitimate same-winery access succeeds
- Repository layer filters by winery_id
- API layer catches cross-winery access (defense in depth)
- Security logging format validation (ADR-027)
- Information disclosure prevention (404 for both not-found and wrong-winery)
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from fastapi import HTTPException

from src.modules.fermentation.src.api.routers.fermentation_router import get_fermentation
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.shared.auth.domain.dtos import UserContext
# ADR-026: Import domain errors
from src.modules.fermentation.src.service_component.errors import NotFoundError
from shared.domain.errors import CrossWineryAccessDenied


# ==================================================================================
# FIXTURES
# ==================================================================================

@pytest.fixture
def user_context_winery_100():
    """User from winery 100"""
    return UserContext(
        user_id=1,
        email="test@test.com",
        winery_id=100,
        role="user"
    )


@pytest.fixture
def user_context_winery_200():
    """User from winery 200 (different winery)"""
    return UserContext(
        user_id=2,
        email="other@test.com",
        winery_id=200,
        role="user"
    )


@pytest.fixture
def fermentation_winery_100():
    """Fermentation belonging to winery 100 with all required attributes"""
    fermentation = Mock(spec=Fermentation)
    fermentation.id = 1
    fermentation.winery_id = 100
    fermentation.name = "Test Fermentation"
    fermentation.status = "IN_PROGRESS"
    fermentation.vintage_year = 2024
    fermentation.yeast_strain = "EC-1118"
    fermentation.vessel_code = "T-01"
    fermentation.input_mass_kg = 100.0
    fermentation.initial_sugar_brix = 22.5
    fermentation.initial_density = 1.095
    fermentation.start_date = datetime(2024, 1, 1)
    fermentation.created_at = datetime(2024, 1, 1)
    fermentation.updated_at = datetime(2024, 1, 1)
    fermentation.harvest_lot_source = None
    fermentation.notes = []
    return fermentation


@pytest.fixture
def fermentation_winery_200():
    """Fermentation belonging to winery 200 with all required attributes"""
    fermentation = Mock(spec=Fermentation)
    fermentation.id = 1
    fermentation.winery_id = 200
    fermentation.name = "Other Winery Fermentation"
    fermentation.status = "IN_PROGRESS"
    fermentation.vintage_year = 2024
    fermentation.yeast_strain = "EC-1118"
    fermentation.vessel_code = "T-02"
    fermentation.input_mass_kg = 100.0
    fermentation.initial_sugar_brix = 22.5
    fermentation.initial_density = 1.095
    fermentation.start_date = datetime(2024, 1, 1)
    fermentation.created_at = datetime(2024, 1, 1)
    fermentation.updated_at = datetime(2024, 1, 1)
    fermentation.harvest_lot_source = None
    fermentation.notes = []
    return fermentation


# ==================================================================================
# TESTS: Multi-Tenant Security Validation
# ==================================================================================

class TestGetFermentationSecurity:
    """ADR-025 LIGHT: Defense-in-depth validation tests for fermentation endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_fermentation_same_winery_success(
        self,
        user_context_winery_100,
        fermentation_winery_100
    ):
        """
        GIVEN: User from winery 100 requests fermentation from winery 100
        WHEN: get_fermentation is called
        THEN: Returns fermentation successfully (200)
        
        ADR-025: Legitimate access within same winery succeeds
        """
        # Arrange
        service = AsyncMock()
        service.get_fermentation.return_value = fermentation_winery_100
        
        # Act
        response = await get_fermentation(
            fermentation_id=1,
            current_user=user_context_winery_100,
            service=service
        )
        
        # Assert
        assert response is not None
        service.get_fermentation.assert_awaited_once_with(
            fermentation_id=1,
            winery_id=100
        )
    
    @pytest.mark.asyncio
    async def test_get_fermentation_repository_filters_by_winery(
        self,
        user_context_winery_100
    ):
        """
        GIVEN: User from winery 100 requests fermentation
        WHEN: Repository returns None (filtered by winery_id)
        THEN: Returns 404 (don't reveal existence)
        
        ADR-025 Day 1: Repository layer filters by winery_id
        """
        # Arrange
        service = AsyncMock()
        service.get_fermentation.return_value = None  # Filtered by repository
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await get_fermentation(
                fermentation_id=999,
                current_user=user_context_winery_100,
                service=service
            )
        
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_fermentation_cross_winery_defense_in_depth(
        self,
        user_context_winery_100,
        fermentation_winery_200
    ):
        """
        GIVEN: User from winery 100
        WHEN: Service somehow returns fermentation from winery 200 (should never happen)
        THEN: Explicit validation catches it and returns 403 + logs security event
        
        ADR-025 Day 2: Defense-in-depth validation at API layer
        
        NOTE: This scenario should never happen because repository filters by winery_id.
        This test validates the explicit security layer catches implementation bugs.
        """
        # Arrange
        service = AsyncMock()
        service.get_fermentation.return_value = fermentation_winery_200
        
        # Act & Assert
        with patch("src.shared.wine_fermentator_logging.get_logger") as mock_logger:
            logger_instance = Mock()
            mock_logger.return_value = logger_instance
            
            with pytest.raises(CrossWineryAccessDenied) as exc_info:
                await get_fermentation(
                    fermentation_id=1,
                    current_user=user_context_winery_100,
                    service=service
                )
            
            # Assert 403 Forbidden (not 404)
            assert exc_info.value.http_status == 403
            assert "access denied" in exc_info.value.message.lower()
            
            # Assert security event logged (ADR-027)
            logger_instance.warning.assert_called_once()
            call_args = logger_instance.warning.call_args
            
            assert call_args[0][0] == "cross_winery_access_attempt"
            assert call_args[1]["user_id"] == 1
            assert call_args[1]["user_winery_id"] == 100
            assert call_args[1]["resource_type"] == "fermentation"
            assert call_args[1]["resource_id"] == 1
            assert call_args[1]["resource_winery_id"] == 200
            assert call_args[1]["endpoint"] == "GET /fermentations/{id}"
    
    @pytest.mark.asyncio
    async def test_get_fermentation_not_found_vs_access_denied(
        self,
        user_context_winery_100
    ):
        """
        GIVEN: User from winery 100 requests non-existent fermentation
        WHEN: Repository returns None
        THEN: Returns 404 (don't reveal whether it exists in other winery)
        
        Security Note: We return 404 for both "not found" and "wrong winery"
        to avoid revealing existence of resources in other wineries.
        """
        # Arrange
        service = AsyncMock()
        service.get_fermentation.return_value = None
        
        # Act & Assert
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await get_fermentation(
                fermentation_id=999,
                current_user=user_context_winery_100,
                service=service
            )
        
        assert exc_info.value.http_status == 404
        # Don't distinguish between "not found" vs "wrong winery"
        assert "not found" in exc_info.value.message.lower()
    
    @pytest.mark.asyncio
    async def test_get_fermentation_security_logging_format(
        self,
        user_context_winery_100,
        fermentation_winery_200
    ):
        """
        GIVEN: Cross-winery access attempt detected
        WHEN: Security event is logged
        THEN: Uses ADR-027 structlog format with all required fields
        
        ADR-027: Structured logging integration for security audit trail
        """
        # Arrange
        service = AsyncMock()
        service.get_fermentation.return_value = fermentation_winery_200
        
        # Act
        with patch("src.shared.wine_fermentator_logging.get_logger") as mock_logger:
            logger_instance = Mock()
            mock_logger.return_value = logger_instance
            
            try:
                await get_fermentation(
                    fermentation_id=1,
                    current_user=user_context_winery_100,
                    service=service
                )
            except CrossWineryAccessDenied:
                pass  # Expected
            
            # Assert logging format
            logger_instance.warning.assert_called_once()
            call_kwargs = logger_instance.warning.call_args[1]
            
            # Required fields for security audit
            required_fields = [
                "user_id",
                "user_winery_id",
                "resource_type",
                "resource_id",
                "resource_winery_id",
                "endpoint"
            ]
            
            for field in required_fields:
                assert field in call_kwargs, f"Missing required field: {field}"
            
            # Validate field types
            assert isinstance(call_kwargs["user_id"], int)
            assert isinstance(call_kwargs["user_winery_id"], int)
            assert isinstance(call_kwargs["resource_id"], int)
            assert isinstance(call_kwargs["resource_winery_id"], int)
            assert isinstance(call_kwargs["resource_type"], str)
            assert isinstance(call_kwargs["endpoint"], str)
