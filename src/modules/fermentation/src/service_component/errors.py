"""
Service layer exceptions for fermentation module.

These exceptions represent business logic violations and are thrown
by service methods when operations cannot be completed.
"""


class ServiceError(Exception):
    """Base exception for all service layer errors."""
    pass


class ValidationError(ServiceError):
    """
    Raised when validation fails for an operation.
    
    This wraps validation errors from the validator layer and
    provides a service-specific exception type.
    """
    def __init__(self, message: str, errors: list = None):
        super().__init__(message)
        self.errors = errors or []


class NotFoundError(ServiceError):
    """
    Raised when a requested resource cannot be found.
    
    This can occur due to:
    - Resource doesn't exist
    - Multi-tenant access violation (wrong winery)
    - Resource is soft-deleted
    """
    pass


class DuplicateError(ServiceError):
    """
    Raised when attempting to create a resource that already exists.
    
    Example: Creating a fermentation in a vessel that's already in use.
    """
    pass


class BusinessRuleViolation(ServiceError):
    """
    Raised when a business rule is violated.
    
    This is distinct from validation errors - validation checks data format,
    while business rules check domain logic constraints.
    """
    pass
