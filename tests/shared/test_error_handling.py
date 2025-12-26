"""
Tests for domain exception hierarchy and error handlers.

Tests ADR-026: Error Handling & Exception Hierarchy Strategy.
Validates RFC 7807 compliance, HTTP status mapping, and logging integration.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Import from shared package (since tests are outside src/)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "shared"))

from domain.errors import (
    DomainError,
    FermentationError,
    FermentationNotFound,
    InvalidFermentationState,
    FermentationAlreadyCompleted,
    SampleNotFound,
    InvalidSampleDate,
    InvalidSampleValue,
    FruitOriginError,
    VineyardNotFound,
    InvalidHarvestDate,
    HarvestLotAlreadyUsed,
    GrapeVarietyNotFound,
    InvalidGrapePercentage,
    WineryError,
    WineryNotFound,
    WineryNameAlreadyExists,
    InvalidWineryData,
    AuthError,
    InvalidCredentials,
    UserNotFound,
    InsufficientPermissions,
    TokenExpired,
    InvalidToken,
    CrossWineryAccessDenied,
)
from api.error_handlers import register_error_handlers


# ============================================
# Exception Hierarchy Tests
# ============================================

class TestExceptionHierarchy:
    """Test exception hierarchy structure and inheritance"""
    
    def test_base_domain_error_attributes(self):
        """Base DomainError should have correct default attributes"""
        error = DomainError("Test error", field="test_field", value=123)
        
        assert error.message == "Test error"
        assert error.http_status == 400
        assert error.error_code == "DOMAIN_ERROR"
        assert error.context == {"field": "test_field", "value": 123}
    
    def test_fermentation_error_is_domain_error(self):
        """FermentationError should inherit from DomainError"""
        assert issubclass(FermentationError, DomainError)
        
        error = FermentationError("Fermentation error")
        assert isinstance(error, DomainError)
        assert error.error_code == "FERMENTATION_ERROR"
    
    def test_fruit_origin_error_is_domain_error(self):
        """FruitOriginError should inherit from DomainError"""
        assert issubclass(FruitOriginError, DomainError)
        
        error = FruitOriginError("Fruit origin error")
        assert isinstance(error, DomainError)
        assert error.error_code == "FRUIT_ORIGIN_ERROR"
    
    def test_winery_error_is_domain_error(self):
        """WineryError should inherit from DomainError"""
        assert issubclass(WineryError, DomainError)
        
        error = WineryError("Winery error")
        assert isinstance(error, DomainError)
        assert error.error_code == "WINERY_ERROR"
    
    def test_auth_error_is_domain_error(self):
        """AuthError should inherit from DomainError"""
        assert issubclass(AuthError, DomainError)
        
        error = AuthError("Auth error")
        assert isinstance(error, DomainError)
        assert error.error_code == "AUTH_ERROR"


# ============================================
# HTTP Status Code Tests
# ============================================

class TestHTTPStatusCodes:
    """Test HTTP status code mapping for specific errors"""
    
    def test_not_found_errors_return_404(self):
        """Not found errors should have 404 status"""
        assert FermentationNotFound("msg").http_status == 404
        assert SampleNotFound("msg").http_status == 404
        assert VineyardNotFound("msg").http_status == 404
        assert GrapeVarietyNotFound("msg").http_status == 404
        assert WineryNotFound("msg").http_status == 404
        assert UserNotFound("msg").http_status == 404
    
    def test_validation_errors_return_400(self):
        """Validation errors should have 400 status"""
        assert InvalidFermentationState("msg").http_status == 400
        assert InvalidSampleDate("msg").http_status == 400
        assert InvalidSampleValue("msg").http_status == 400
        assert InvalidHarvestDate("msg").http_status == 400
        assert InvalidGrapePercentage("msg").http_status == 400
        assert InvalidWineryData("msg").http_status == 400
    
    def test_conflict_errors_return_409(self):
        """Conflict errors should have 409 status"""
        assert FermentationAlreadyCompleted("msg").http_status == 409
        assert HarvestLotAlreadyUsed("msg").http_status == 409
        assert WineryNameAlreadyExists("msg").http_status == 409
    
    def test_auth_errors_return_401(self):
        """Authentication errors should have 401 status"""
        assert InvalidCredentials("msg").http_status == 401
        assert TokenExpired("msg").http_status == 401
        assert InvalidToken("msg").http_status == 401
    
    def test_permission_errors_return_403(self):
        """Permission errors should have 403 status"""
        assert InsufficientPermissions("msg").http_status == 403
        assert CrossWineryAccessDenied("msg").http_status == 403


# ============================================
# Error Code Tests
# ============================================

class TestErrorCodes:
    """Test error code constants"""
    
    def test_fermentation_error_codes(self):
        """Fermentation errors should have correct codes"""
        assert FermentationNotFound("msg").error_code == "FERMENTATION_NOT_FOUND"
        assert InvalidFermentationState("msg").error_code == "INVALID_FERMENTATION_STATE"
        assert FermentationAlreadyCompleted("msg").error_code == "FERMENTATION_ALREADY_COMPLETED"
        assert SampleNotFound("msg").error_code == "SAMPLE_NOT_FOUND"
        assert InvalidSampleDate("msg").error_code == "INVALID_SAMPLE_DATE"
        assert InvalidSampleValue("msg").error_code == "INVALID_SAMPLE_VALUE"
    
    def test_fruit_origin_error_codes(self):
        """Fruit origin errors should have correct codes"""
        assert VineyardNotFound("msg").error_code == "VINEYARD_NOT_FOUND"
        assert InvalidHarvestDate("msg").error_code == "INVALID_HARVEST_DATE"
        assert HarvestLotAlreadyUsed("msg").error_code == "HARVEST_LOT_ALREADY_USED"
        assert GrapeVarietyNotFound("msg").error_code == "GRAPE_VARIETY_NOT_FOUND"
        assert InvalidGrapePercentage("msg").error_code == "INVALID_GRAPE_PERCENTAGE"
    
    def test_winery_error_codes(self):
        """Winery errors should have correct codes"""
        assert WineryNotFound("msg").error_code == "WINERY_NOT_FOUND"
        assert WineryNameAlreadyExists("msg").error_code == "WINERY_NAME_ALREADY_EXISTS"
        assert InvalidWineryData("msg").error_code == "INVALID_WINERY_DATA"
    
    def test_auth_error_codes(self):
        """Auth errors should have correct codes"""
        assert InvalidCredentials("msg").error_code == "INVALID_CREDENTIALS"
        assert UserNotFound("msg").error_code == "USER_NOT_FOUND"
        assert InsufficientPermissions("msg").error_code == "INSUFFICIENT_PERMISSIONS"
        assert TokenExpired("msg").error_code == "TOKEN_EXPIRED"
        assert InvalidToken("msg").error_code == "INVALID_TOKEN"


# ============================================
# RFC 7807 Format Tests
# ============================================

class TestRFC7807Format:
    """Test RFC 7807 Problem Details format compliance"""
    
    @pytest.fixture
    def app(self) -> FastAPI:
        """Create test FastAPI app with error handlers"""
        app = FastAPI()
        register_error_handlers(app)
        
        @app.get("/test/fermentation/{fermentation_id}")
        async def test_endpoint(fermentation_id: int):
            if fermentation_id == 999:
                raise FermentationNotFound(
                    f"Fermentation {fermentation_id} not found",
                    fermentation_id=fermentation_id
                )
            return {"id": fermentation_id}
        
        @app.get("/test/vineyard/{vineyard_id}")
        async def test_vineyard_endpoint(vineyard_id: int):
            if vineyard_id == 888:
                raise InvalidHarvestDate(
                    "Harvest date 2026-01-15 cannot be in the future",
                    field="harvest_date",
                    provided_date="2026-01-15"
                )
            return {"id": vineyard_id}
        
        return app
    
    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create test client"""
        return TestClient(app)
    
    def test_rfc7807_format_for_not_found(self, client: TestClient):
        """Error response should follow RFC 7807 format for 404"""
        response = client.get("/test/fermentation/999")
        
        assert response.status_code == 404
        data = response.json()
        
        # RFC 7807 required fields
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "instance" in data
        
        # Custom fields
        assert data["code"] == "FERMENTATION_NOT_FOUND"
        assert data["status"] == 404
        assert "999" in data["detail"]
        assert data["fermentation_id"] == 999
        assert data["instance"] == "/test/fermentation/999"
    
    def test_rfc7807_format_for_validation_error(self, client: TestClient):
        """Error response should follow RFC 7807 format for 400"""
        response = client.get("/test/vineyard/888")
        
        assert response.status_code == 400
        data = response.json()
        
        # RFC 7807 required fields
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "instance" in data
        
        # Custom fields
        assert data["code"] == "INVALID_HARVEST_DATE"
        assert data["status"] == 400
        assert "future" in data["detail"].lower()
        assert data["field"] == "harvest_date"
        assert data["provided_date"] == "2026-01-15"
    
    def test_error_title_formatting(self, client: TestClient):
        """Error title should be human-readable"""
        response = client.get("/test/fermentation/999")
        data = response.json()
        
        # Title should be formatted from PascalCase to Title Case
        assert data["title"] == "Fermentation Not Found"
    
    def test_error_type_uri(self, client: TestClient):
        """Error type should be a URI"""
        response = client.get("/test/fermentation/999")
        data = response.json()
        
        assert data["type"] == "https://api.wine-fermentation.com/errors/fermentation_not_found"


# ============================================
# Context Data Tests
# ============================================

class TestErrorContext:
    """Test error context data handling"""
    
    def test_error_with_context_data(self):
        """Error should store arbitrary context data"""
        error = VineyardNotFound(
            "Vineyard 123 not found",
            vineyard_id=123,
            winery_id=456,
            requested_by="user@example.com"
        )
        
        assert error.context == {
            "vineyard_id": 123,
            "winery_id": 456,
            "requested_by": "user@example.com"
        }
    
    def test_error_without_context_data(self):
        """Error should work without context data"""
        error = WineryNotFound("Winery not found")
        
        assert error.context == {}
        assert error.message == "Winery not found"


# ============================================
# Exception Catching Tests
# ============================================

class TestExceptionCatching:
    """Test catching exceptions by category"""
    
    def test_catch_specific_error(self):
        """Should be able to catch specific error"""
        with pytest.raises(FermentationNotFound):
            raise FermentationNotFound("Not found")
    
    def test_catch_module_error_category(self):
        """Should be able to catch all errors from a module"""
        with pytest.raises(FermentationError):
            raise FermentationNotFound("Not found")
        
        with pytest.raises(FermentationError):
            raise InvalidFermentationState("Invalid state")
    
    def test_catch_all_domain_errors(self):
        """Should be able to catch all domain errors"""
        with pytest.raises(DomainError):
            raise FermentationNotFound("Not found")
        
        with pytest.raises(DomainError):
            raise VineyardNotFound("Not found")
        
        with pytest.raises(DomainError):
            raise WineryNotFound("Not found")
