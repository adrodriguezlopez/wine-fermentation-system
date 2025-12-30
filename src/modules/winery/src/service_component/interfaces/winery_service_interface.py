"""
Interface definition for Winery Service.

Service layer for winery management business logic orchestration.
Coordinates validation, repository access, and business rules.

Follows Clean Architecture principles:
- Uses DTOs from domain layer (WineryCreate, WineryUpdate)
- Returns ORM entities (Winery)
- Delegates data access to repositories
- Does NOT handle authentication (API layer responsibility)

Related ADRs:
- ADR-009: Missing Repositories (WineryRepository complete)
- ADR-016: Winery Service Layer (this service)
- ADR-025: Multi-Tenancy Security (Winery is root entity)
- ADR-026: Error Handling Strategy (domain errors)
- ADR-027: Structured Logging (observability)
"""
from abc import ABC, abstractmethod
from typing import List

from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.winery.src.domain.dtos.winery_dtos import WineryCreate, WineryUpdate


class IWineryService(ABC):
    """
    Interface for winery management service.
    
    Orchestrates:
    - Winery lifecycle (CRUD with business rules)
    - Global code uniqueness validation
    - Deletion protection (check active data in other modules)
    
    Does NOT handle:
    - Authentication (API layer responsibility)
    - Direct database access (uses repositories)
    - Multi-tenant filtering (Winery is root entity, no winery_id scoping)
    
    Design Philosophy:
    - Simple service for root entity (Winery)
    - Follows Fruit Origin Service pattern (ADR-014)
    - Security-first (ADR-025 integrated from day 1)
    - Observable (ADR-027 structured logging)
    """
    
    # ==================================================================================
    # CREATE OPERATIONS
    # ==================================================================================
    
    @abstractmethod
    async def create_winery(
        self,
        data: WineryCreate
    ) -> Winery:
        """
        Create a new winery with validation.
        
        Validates:
        - Code uniqueness (global across all wineries)
        - Required fields (code, name)
        - Code format (uppercase alphanumeric + hyphens)
        
        Args:
            data: Winery creation data (code, name, location, notes)
            
        Returns:
            Winery: Created winery entity
            
        Raises:
            DuplicateCodeError: If code already exists
            InvalidWineryData: If validation fails (missing required fields, invalid format)
        """
        pass
    
    # ==================================================================================
    # READ OPERATIONS
    # ==================================================================================
    
    @abstractmethod
    async def get_winery(
        self,
        winery_id: int
    ) -> Winery:
        """
        Get winery by ID.
        
        Args:
            winery_id: Winery ID
            
        Returns:
            Winery: Winery entity
            
        Raises:
            WineryNotFound: If winery doesn't exist
        """
        pass
    
    @abstractmethod
    async def get_winery_by_code(
        self,
        code: str
    ) -> Winery:
        """
        Get winery by code.
        
        Args:
            code: Winery code (unique identifier)
            
        Returns:
            Winery: Winery entity
            
        Raises:
            WineryNotFound: If winery doesn't exist
        """
        pass
    
    @abstractmethod
    async def list_wineries(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Winery]:
        """
        List all wineries with pagination.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List[Winery]: List of winery entities
        """
        pass
    
    # ==================================================================================
    # UPDATE OPERATIONS
    # ==================================================================================
    
    @abstractmethod
    async def update_winery(
        self,
        winery_id: int,
        data: WineryUpdate
    ) -> Winery:
        """
        Update winery details.
        
        Note: Code is immutable - cannot be updated after creation.
        
        Args:
            winery_id: Winery ID
            data: Winery update data (name, location, notes)
            
        Returns:
            Winery: Updated winery entity
            
        Raises:
            WineryNotFound: If winery doesn't exist
            InvalidWineryData: If validation fails
        """
        pass
    
    # ==================================================================================
    # DELETE OPERATIONS
    # ==================================================================================
    
    @abstractmethod
    async def delete_winery(
        self,
        winery_id: int
    ) -> None:
        """
        Soft delete winery with active data protection.
        
        Validates deletion is safe:
        - No active vineyards (fruit_origin module)
        - No active fermentations (fermentation module)
        - No active users (auth module, future)
        
        Args:
            winery_id: Winery ID
            
        Raises:
            WineryNotFound: If winery doesn't exist
            WineryHasActiveDataError: If winery has active data in other modules
        """
        pass
    
    # ==================================================================================
    # UTILITY OPERATIONS
    # ==================================================================================
    
    @abstractmethod
    async def winery_exists(
        self,
        winery_id: int
    ) -> bool:
        """
        Check if winery exists.
        
        Args:
            winery_id: Winery ID
            
        Returns:
            bool: True if winery exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def count_wineries(self) -> int:
        """
        Count total wineries.
        
        Returns:
            int: Total number of wineries
        """
        pass
