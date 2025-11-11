"""
FastAPI dependencies for Fermentation API Layer

Provides dependency injection for services, repositories, and database sessions.
Following Clean Architecture: API layer depends on service abstractions.

TODO: Implement proper DB session management with connection pooling.
For now, this uses a simplified approach suitable for testing/development.
"""

from typing import Annotated
from fastapi import Depends

from src.modules.fermentation.src.service_component.interfaces.fermentation_service_interface import IFermentationService
from src.modules.fermentation.src.service_component.services.fermentation_service import FermentationService
from src.modules.fermentation.src.service_component.interfaces.fermentation_validator_interface import IFermentationValidator
from src.modules.fermentation.src.service_component.validators.fermentation_validator import FermentationValidator


def get_fermentation_validator() -> IFermentationValidator:
    """
    Dependency: Get fermentation validator instance
    
    Returns:
        IFermentationValidator: Stateless validator instance
    """
    return FermentationValidator()


async def get_fermentation_service(
    validator: Annotated[IFermentationValidator, Depends(get_fermentation_validator)]
) -> IFermentationService:
    """
    Dependency: Get fermentation service instance with injected dependencies
    
    Args:
        validator: Fermentation validator (from dependency)
        
    Returns:
        IFermentationService: Service instance ready for use
        
    Note: Repository injection uses a mock repository for API testing.
    This allows testing API structure without full DB setup.
    
    TODO: Inject real repository once DB session dependency is configured.
        
    Example:
        ```python
        @router.post("/fermentations")
        async def create(
            data: FermentationCreateRequest,
            service: Annotated[IFermentationService, Depends(get_fermentation_service)]
        ):
            result = await service.create_fermentation(...)
        ```
    """
    # Create a simple mock repository for testing API layer
    from unittest.mock import MagicMock
    from datetime import datetime
    from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
    
    mock_repo = MagicMock()
    
    # Mock create method to return a simple object (not ORM entity to avoid mapping issues)
    async def mock_create(winery_id: int, data):
        # Create a simple object that mimics Fermentation entity
        # Avoid using actual Fermentation class to prevent SQLAlchemy mapping issues
        class MockFermentation:
            def __init__(self):
                self.id = 1
                self.winery_id = winery_id
                self.fermented_by_user_id = data.fermented_by_user_id
                self.vintage_year = data.vintage_year
                self.yeast_strain = data.yeast_strain
                self.vessel_code = data.vessel_code
                self.input_mass_kg = data.input_mass_kg
                self.initial_sugar_brix = data.initial_sugar_brix
                self.initial_density = data.initial_density
                self.start_date = data.start_date or datetime.now()
                self.status = FermentationStatus.ACTIVE
                self.created_at = datetime.now()
                self.updated_at = datetime.now()
        
        return MockFermentation()
    
    mock_repo.create = mock_create
    
    return FermentationService(
        fermentation_repo=mock_repo,
        validator=validator
    )
