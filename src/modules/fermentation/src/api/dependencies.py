"""
FastAPI dependencies for Fermentation API Layer

Provides dependency injection for services, repositories, and real PostgreSQL database.
Following Clean Architecture: API layer depends on service abstractions.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infra.database.fastapi_session import get_db_session
from src.shared.infra.repository.fastapi_session_manager import FastAPISessionManager

from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
from src.modules.fermentation.src.service_component.interfaces.fermentation_service_interface import IFermentationService
from src.modules.fermentation.src.service_component.services.fermentation_service import FermentationService
from src.modules.fermentation.src.service_component.interfaces.fermentation_validator_interface import IFermentationValidator
from src.modules.fermentation.src.service_component.validators.fermentation_validator import FermentationValidator

from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository
from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository
from src.modules.fermentation.src.service_component.interfaces.sample_service_interface import ISampleService
from src.modules.fermentation.src.service_component.services.sample_service import SampleService
from src.modules.fermentation.src.service_component.interfaces.validation_orchestrator_interface import IValidationOrchestrator
from src.modules.fermentation.src.service_component.services.validation_orchestrator import ValidationOrchestrator
from src.modules.fermentation.src.service_component.interfaces.chronology_validation_service_interface import IChronologyValidationService
from src.modules.fermentation.src.service_component.services.chronology_validation_service import ChronologyValidationService
from src.modules.fermentation.src.service_component.interfaces.value_validation_service_interface import IValueValidationService
from src.modules.fermentation.src.service_component.services.value_validation_service import ValueValidationService
from src.modules.fermentation.src.service_component.interfaces.business_rule_validation_service_interface import IBusinessRuleValidationService
from src.modules.fermentation.src.service_component.services.business_rule_validation_service import BusinessRuleValidationService


def get_fermentation_validator() -> IFermentationValidator:
    """
    Dependency: Get fermentation validator instance
    
    Returns:
        IFermentationValidator: Stateless validator instance
    """
    return FermentationValidator()


async def get_fermentation_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> IFermentationRepository:
    """
    Dependency: Get fermentation repository with real PostgreSQL database session.
    
    Args:
        session: AsyncSession from FastAPI dependency (auto-injected)
    
    Returns:
        IFermentationRepository: Repository instance connected to PostgreSQL
    
    Lifecycle:
        - Session managed by get_db_session (commit/rollback/close automatic)
        - Repository wraps session with SessionManager for BaseRepository compatibility
    """
    session_manager = FastAPISessionManager(session)
    return FermentationRepository(session_manager)


async def get_fermentation_service(
    repository: Annotated[IFermentationRepository, Depends(get_fermentation_repository)],
    validator: Annotated[IFermentationValidator, Depends(get_fermentation_validator)]
) -> IFermentationService:
    """
    Dependency: Get fermentation service instance with injected dependencies.
    
    Args:
        repository: Fermentation repository (auto-injected with PostgreSQL session)
        validator: Fermentation validator (auto-injected)
        
    Returns:
        IFermentationService: Service instance with REAL database persistence
    """
    return FermentationService(
        fermentation_repo=repository,
        validator=validator
    )


# ======================================================================================
# Sample Dependencies (Sample Service Layer)
# ======================================================================================

async def get_sample_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> ISampleRepository:
    """
    Dependency: Get sample repository with real PostgreSQL database session.
    
    Args:
        session: AsyncSession from FastAPI dependency (auto-injected)
    
    Returns:
        ISampleRepository: Repository instance connected to PostgreSQL
    """
    session_manager = FastAPISessionManager(session)
    return SampleRepository(session_manager)


async def get_chronology_validator(
    sample_repo: Annotated[ISampleRepository, Depends(get_sample_repository)]
) -> IChronologyValidationService:
    """
    Dependency: Get chronology validation service.
    
    Args:
        sample_repo: Sample repository for historical data queries
        
    Returns:
        IChronologyValidationService: Validator instance
    """
    return ChronologyValidationService(sample_repository=sample_repo)


def get_value_validator() -> IValueValidationService:
    """
    Dependency: Get value validation service (stateless).
    
    Returns:
        IValueValidationService: Validator instance
    """
    return ValueValidationService()


async def get_business_rules_validator(
    sample_repo: Annotated[ISampleRepository, Depends(get_sample_repository)],
    fermentation_repo: Annotated[IFermentationRepository, Depends(get_fermentation_repository)]
) -> IBusinessRuleValidationService:
    """
    Dependency: Get business rule validation service.
    
    Args:
        sample_repo: Sample repository for historical data
        fermentation_repo: Fermentation repository for validation
        
    Returns:
        IBusinessRuleValidationService: Validator instance
    """
    return BusinessRuleValidationService(
        sample_repository=sample_repo,
        fermentation_repository=fermentation_repo
    )


async def get_validation_orchestrator(
    chronology_validator: Annotated[IChronologyValidationService, Depends(get_chronology_validator)],
    value_validator: Annotated[IValueValidationService, Depends(get_value_validator)],
    business_rules_validator: Annotated[IBusinessRuleValidationService, Depends(get_business_rules_validator)]
) -> IValidationOrchestrator:
    """
    Dependency: Get validation orchestrator instance with all validators.
    
    Args:
        chronology_validator: Chronology validation service
        value_validator: Value validation service
        business_rules_validator: Business rule validation service
        
    Returns:
        IValidationOrchestrator: Orchestrator instance
    """
    return ValidationOrchestrator(
        chronology_validator=chronology_validator,
        value_validator=value_validator,
        business_rules_validator=business_rules_validator
    )


async def get_sample_service(
    sample_repo: Annotated[ISampleRepository, Depends(get_sample_repository)],
    validation_orchestrator: Annotated[IValidationOrchestrator, Depends(get_validation_orchestrator)],
    fermentation_repo: Annotated[IFermentationRepository, Depends(get_fermentation_repository)]
) -> ISampleService:
    """
    Dependency: Get sample service instance with injected dependencies.
    
    Args:
        sample_repo: Sample repository (auto-injected with PostgreSQL session)
        validation_orchestrator: Validation orchestrator for sample validation
        fermentation_repo: Fermentation repository for ownership validation
        
    Returns:
        ISampleService: Service instance with REAL database persistence
    """
    return SampleService(
        sample_repo=sample_repo,
        validation_orchestrator=validation_orchestrator,
        fermentation_repo=fermentation_repo
    )

