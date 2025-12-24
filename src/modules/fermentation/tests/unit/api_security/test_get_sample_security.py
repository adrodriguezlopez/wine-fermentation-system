"""
ADR-025 LIGHT: Multi-Tenancy Security Tests for GET /fermentations/{id}/samples/{sample_id}

Tests defense-in-depth validation for samples:
- Repository filters by winery_id via JOIN with fermentation (Day 1)
- API validates fermentation_id match (Day 2)
- Security events logged (ADR-027)

Note: Samples don't have winery_id directly - validated via fermentation relationship.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException
from src.modules.fermentation.src.api.routers.sample_router import get_sample
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.shared.auth.domain.dtos import UserContext


class TestGetSampleSecurity:
    """ADR-025 LIGHT: Defense-in-depth validation tests for samples"""
    
    @pytest.fixture
    def user_context_winery_100(self):
        """User from winery 100"""
        return UserContext(
            user_id=1,
            email="test@test.com",
            winery_id=100,
            role="user"
        )
    
    @pytest.fixture
    def sample_fermentation_1(self):
        """Sample belonging to fermentation 1"""
        from datetime import datetime
        sample = Mock(spec=BaseSample)
        sample.id = 10
        sample.fermentation_id = 1
        sample.sample_type = "DENSITY"
        sample.sampled_at = datetime(2024, 1, 2)
        sample.created_at = datetime(2024, 1, 2)
        sample.updated_at = datetime(2024, 1, 2)
        sample.value = 1.050
        sample.notes = None
        sample.units = "g/mL"
        sample.recorded_at = datetime(2024, 1, 2)
        return sample
    
    @pytest.fixture
    def sample_fermentation_2(self):
        """Sample belonging to fermentation 2 (different fermentation)"""
        from datetime import datetime
        sample = Mock(spec=BaseSample)
        sample.id = 10
        sample.fermentation_id = 2
        sample.sample_type = "DENSITY"
        sample.sampled_at = datetime(2024, 1, 2)
        sample.created_at = datetime(2024, 1, 2)
        sample.updated_at = datetime(2024, 1, 2)
        sample.value = 1.050
        sample.notes = None
        sample.units = "g/mL"
        sample.recorded_at = datetime(2024, 1, 2)
        return sample
    
    @pytest.mark.asyncio
    async def test_get_sample_same_winery_success(
        self,
        user_context_winery_100,
        sample_fermentation_1
    ):
        """
        GIVEN: User from winery 100 requests sample from fermentation 1 (same winery)
        WHEN: get_sample is called
        THEN: Returns sample successfully (200)
        
        ADR-025: Legitimate access within same winery succeeds
        """
        # Arrange
        service = AsyncMock()
        service.get_sample.return_value = sample_fermentation_1
        
        # Act
        response = await get_sample(
            fermentation_id=1,
            sample_id=10,
            current_user=user_context_winery_100,
            sample_service=service
        )
        
        # Assert
        assert response is not None
        service.get_sample.assert_awaited_once_with(
            sample_id=10,
            fermentation_id=1,
            winery_id=100
        )
    
    @pytest.mark.asyncio
    async def test_get_sample_repository_filters_by_winery(
        self,
        user_context_winery_100
    ):
        """
        GIVEN: User from winery 100 requests sample
        WHEN: Repository returns None (filtered by winery_id via JOIN)
        THEN: Returns 404 (don't reveal existence)
        
        ADR-025 Day 1: Repository filters samples via JOIN with fermentation.winery_id
        """
        # Arrange
        service = AsyncMock()
        service.get_sample.return_value = None  # Filtered by repository
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_sample(
                fermentation_id=999,
                sample_id=888,
                current_user=user_context_winery_100,
                sample_service=service
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_sample_fermentation_id_mismatch(
        self,
        user_context_winery_100,
        sample_fermentation_2
    ):
        """
        GIVEN: User requests sample 10 from fermentation 1
        WHEN: Sample actually belongs to fermentation 2 (path mismatch)
        THEN: Returns 404 + logs security event
        
        ADR-025 Day 2: Validate path parameter consistency
        
        NOTE: Repository should prevent this, but explicit validation catches bugs.
        """
        # Arrange
        service = AsyncMock()
        service.get_sample.return_value = sample_fermentation_2  # Wrong fermentation
        
        # Act & Assert
        with patch("src.shared.wine_fermentator_logging.get_logger") as mock_logger:
            logger_instance = Mock()
            mock_logger.return_value = logger_instance
            
            with pytest.raises(HTTPException) as exc_info:
                await get_sample(
                    fermentation_id=1,  # Request from fermentation 1
                    sample_id=10,
                    current_user=user_context_winery_100,
                    sample_service=service
                )
            
            # Assert 404 (don't reveal sample exists in other fermentation)
            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()
            assert "fermentation 1" in exc_info.value.detail.lower()
            
            # Assert security event logged (ADR-027)
            logger_instance.warning.assert_called_once()
            call_args = logger_instance.warning.call_args
            
            assert call_args[0][0] == "sample_fermentation_mismatch"
            assert call_args[1]["user_id"] == 1
            assert call_args[1]["user_winery_id"] == 100
            assert call_args[1]["sample_id"] == 10
            assert call_args[1]["expected_fermentation_id"] == 1
            assert call_args[1]["actual_fermentation_id"] == 2
    
    @pytest.mark.asyncio
    async def test_get_sample_security_logging_format(
        self,
        user_context_winery_100,
        sample_fermentation_2
    ):
        """
        GIVEN: Fermentation ID mismatch detected
        WHEN: Security event is logged
        THEN: Uses ADR-027 structlog format with all required fields
        
        ADR-027: Structured logging integration
        """
        # Arrange
        service = AsyncMock()
        service.get_sample.return_value = sample_fermentation_2
        
        # Act
        with patch("src.shared.wine_fermentator_logging.get_logger") as mock_logger:
            logger_instance = Mock()
            mock_logger.return_value = logger_instance
            
            try:
                await get_sample(
                    fermentation_id=1,
                    sample_id=10,
                    current_user=user_context_winery_100,
                    sample_service=service
                )
            except HTTPException:
                pass  # Expected
            
            # Assert logging format
            logger_instance.warning.assert_called_once()
            call_kwargs = logger_instance.warning.call_args[1]
            
            # Required fields for security audit
            required_fields = [
                "user_id",
                "user_winery_id",
                "sample_id",
                "expected_fermentation_id",
                "actual_fermentation_id",
                "endpoint"
            ]
            
            for field in required_fields:
                assert field in call_kwargs, f"Missing required field: {field}"
            
            # Validate field types
            assert isinstance(call_kwargs["user_id"], int)
            assert isinstance(call_kwargs["user_winery_id"], int)
            assert isinstance(call_kwargs["sample_id"], int)
            assert isinstance(call_kwargs["expected_fermentation_id"], int)
            assert isinstance(call_kwargs["actual_fermentation_id"], int)
            assert isinstance(call_kwargs["endpoint"], str)
    
    @pytest.mark.asyncio
    async def test_get_sample_path_parameter_validation(
        self,
        user_context_winery_100,
        sample_fermentation_1
    ):
        """
        GIVEN: Valid sample belonging to requested fermentation
        WHEN: Path parameters match sample.fermentation_id
        THEN: Returns sample successfully (no security warning)
        
        ADR-025: Path consistency validation passes for valid requests
        """
        # Arrange
        service = AsyncMock()
        service.get_sample.return_value = sample_fermentation_1
        
        # Act
        with patch("src.shared.wine_fermentator_logging.get_logger") as mock_logger:
            logger_instance = Mock()
            mock_logger.return_value = logger_instance
            
            response = await get_sample(
                fermentation_id=1,  # Matches sample.fermentation_id
                sample_id=10,
                current_user=user_context_winery_100,
                sample_service=service
            )
            
            # Assert no security warning logged (legitimate access)
            logger_instance.warning.assert_not_called()
            assert response is not None
    
    @pytest.mark.asyncio
    async def test_get_sample_winery_isolation_via_repository(
        self,
        user_context_winery_100
    ):
        """
        GIVEN: User from winery 100 tries to access sample from winery 200
        WHEN: Repository filters via JOIN (fermentation.winery_id)
        THEN: Returns None → 404 (don't reveal existence)
        
        ADR-025 Day 1: Repository layer provides first security boundary
        
        Note: Samples don't have winery_id column. Security enforced via:
        - Repository: JOIN with fermentation WHERE fermentation.winery_id = ?
        - API: Validate fermentation_id consistency
        """
        # Arrange
        service = AsyncMock()
        service.get_sample.return_value = None  # Repository filtered out
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_sample(
                fermentation_id=999,  # Different winery
                sample_id=10,
                current_user=user_context_winery_100,
                sample_service=service
            )
        
        # Repository filtered it out → 404
        assert exc_info.value.status_code == 404
        
        # Service was called with correct winery_id filter
        service.get_sample.assert_awaited_once_with(
            sample_id=10,
            fermentation_id=999,
            winery_id=100  # Repository uses this to JOIN filter
        )
