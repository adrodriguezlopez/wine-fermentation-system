"""
Domain exception hierarchy for Wine Fermentation System.

Implements ADR-026: Error Handling & Exception Hierarchy Strategy.
Provides type-safe, self-documenting error handling with automatic HTTP status mapping.
"""

from typing import Any, Dict


class DomainError(Exception):
    """
    Base exception for all business logic errors.
    
    Attributes:
        http_status: HTTP status code to return (default 400 Bad Request)
        error_code: Machine-readable error code for frontend/API consumers
        message: Human-readable error message
        context: Additional context data (field names, IDs, etc.)
    """
    http_status: int = 400
    error_code: str = "DOMAIN_ERROR"
    
    def __init__(self, message: str, **kwargs: Any) -> None:
        """
        Initialize domain error.
        
        Args:
            message: Human-readable error description
            **kwargs: Additional context (vineyard_id, field, etc.)
        """
        super().__init__(message)
        self.message = message
        self.context: Dict[str, Any] = kwargs


# ============================================
# Module-specific base errors
# ============================================

class FermentationError(DomainError):
    """Base error for Fermentation module"""
    error_code = "FERMENTATION_ERROR"


class FruitOriginError(DomainError):
    """Base error for Fruit Origin module"""
    error_code = "FRUIT_ORIGIN_ERROR"


class WineryError(DomainError):
    """Base error for Winery module"""
    error_code = "WINERY_ERROR"


class AuthError(DomainError):
    """Base error for Authentication/Authorization"""
    error_code = "AUTH_ERROR"


# ============================================
# Fermentation-specific errors
# ============================================

class FermentationNotFound(FermentationError):
    """Raised when a fermentation is not found"""
    http_status = 404
    error_code = "FERMENTATION_NOT_FOUND"


class InvalidFermentationState(FermentationError):
    """Raised when attempting an operation incompatible with current state"""
    http_status = 400
    error_code = "INVALID_FERMENTATION_STATE"


class FermentationAlreadyCompleted(FermentationError):
    """Raised when attempting to modify a completed fermentation"""
    http_status = 409  # Conflict
    error_code = "FERMENTATION_ALREADY_COMPLETED"


class SampleNotFound(FermentationError):
    """Raised when a sample is not found"""
    http_status = 404
    error_code = "SAMPLE_NOT_FOUND"


class InvalidSampleDate(FermentationError):
    """Raised when sample date is invalid (future date, before start, etc.)"""
    http_status = 400
    error_code = "INVALID_SAMPLE_DATE"


class InvalidSampleValue(FermentationError):
    """Raised when sample value is outside valid range"""
    http_status = 400
    error_code = "INVALID_SAMPLE_VALUE"


# ============================================
# Fruit Origin-specific errors
# ============================================

class VineyardNotFound(FruitOriginError):
    """Raised when a vineyard is not found"""
    http_status = 404
    error_code = "VINEYARD_NOT_FOUND"


class InvalidHarvestDate(FruitOriginError):
    """Raised when harvest date is invalid (future, too old, etc.)"""
    http_status = 400
    error_code = "INVALID_HARVEST_DATE"


class HarvestLotAlreadyUsed(FruitOriginError):
    """Raised when harvest lot already exists for vineyard/date combination"""
    http_status = 409  # Conflict
    error_code = "HARVEST_LOT_ALREADY_USED"


class GrapeVarietyNotFound(FruitOriginError):
    """Raised when a grape variety is not found"""
    http_status = 404
    error_code = "GRAPE_VARIETY_NOT_FOUND"


class InvalidGrapePercentage(FruitOriginError):
    """Raised when grape variety percentages don't sum to 100%"""
    http_status = 400
    error_code = "INVALID_GRAPE_PERCENTAGE"


class VineyardHasActiveLotsError(FruitOriginError):
    """Raised when attempting to delete vineyard with active harvest lots"""
    http_status = 409  # Conflict
    error_code = "VINEYARD_HAS_ACTIVE_LOTS"


class VineyardBlockNotFound(FruitOriginError):
    """Raised when a vineyard block is not found"""
    http_status = 404
    error_code = "VINEYARD_BLOCK_NOT_FOUND"


class HarvestLotNotFound(FruitOriginError):
    """Raised when a harvest lot is not found"""
    http_status = 404
    error_code = "HARVEST_LOT_NOT_FOUND"


class DuplicateCodeError(FruitOriginError):
    """Raised when code already exists for the winery"""
    http_status = 409  # Conflict
    error_code = "DUPLICATE_CODE"


# ============================================
# Winery-specific errors
# ============================================

class WineryNotFound(WineryError):
    """Raised when a winery is not found"""
    http_status = 404
    error_code = "WINERY_NOT_FOUND"


class WineryNameAlreadyExists(WineryError):
    """Raised when attempting to create a winery with duplicate name"""
    http_status = 409  # Conflict
    error_code = "WINERY_NAME_ALREADY_EXISTS"


class InvalidWineryData(WineryError):
    """Raised when winery data fails validation"""
    http_status = 400
    error_code = "INVALID_WINERY_DATA"


# ============================================
# Auth-specific errors
# ============================================

class InvalidCredentials(AuthError):
    """Raised when login credentials are incorrect"""
    http_status = 401  # Unauthorized
    error_code = "INVALID_CREDENTIALS"


class UserNotFound(AuthError):
    """Raised when a user is not found"""
    http_status = 404
    error_code = "USER_NOT_FOUND"


class InsufficientPermissions(AuthError):
    """Raised when user lacks required permissions"""
    http_status = 403  # Forbidden
    error_code = "INSUFFICIENT_PERMISSIONS"


class TokenExpired(AuthError):
    """Raised when authentication token has expired"""
    http_status = 401  # Unauthorized
    error_code = "TOKEN_EXPIRED"


class InvalidToken(AuthError):
    """Raised when authentication token is malformed or invalid"""
    http_status = 401  # Unauthorized
    error_code = "INVALID_TOKEN"


# ============================================
# Cross-cutting errors (ADR-025: Multi-Tenancy)
# ============================================

class CrossWineryAccessDenied(DomainError):
    """Raised when attempting to access resources from a different winery"""
    http_status = 403  # Forbidden
    error_code = "CROSS_WINERY_ACCESS_DENIED"
