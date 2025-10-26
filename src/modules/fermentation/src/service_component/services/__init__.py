"""
Service implementations for fermentation module.

Following Service Layer Pattern as defined in ADR-005.
Services orchestrate business logic, delegating to repositories and validators.
"""

# Note: Import services directly from their modules to avoid circular imports
# Example: from src.service_component.services.fermentation_service import FermentationService

__all__ = [
    "FermentationService",
]
