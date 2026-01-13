"""
ETL Service for Historical Data Import.

Orchestrates the complete import process:
1. Validates using 3-layer strategy (pre, row, post)
2. Creates fermentations and samples with data_source=IMPORTED
3. Manages transactions and rollback
4. Returns comprehensive import results
5. Supports progress tracking and cancellation (ADR-030 Phase 3)
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable, Awaitable
import time
import pandas as pd

from src.modules.fermentation.src.service_component.etl.etl_validator import (
    ETLValidator,
    PreValidationResult,
    RowValidationResult,
    PostValidationResult
)
from src.modules.fermentation.src.service_component.etl.cancellation_token import (
    CancellationToken,
    ImportCancelledException
)
from src.modules.fermentation.src.domain.dtos import FermentationCreate, LotSourceData
from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
from src.modules.fermentation.src.domain.enums.data_source import DataSource
from src.modules.fermentation.src.domain.enums.sample_type import SampleType
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository
from src.modules.fermentation.src.repository_component.repositories.lot_source_repository import LotSourceRepository
from src.modules.fruit_origin.src.service_component.interfaces.fruit_origin_service_interface import IFruitOriginService
from src.shared.infra.interfaces.session_manager import ISessionManager
from src.shared.infra.session.transaction_scope import TransactionScope
from decimal import Decimal


@dataclass
class ImportResult:
    """Result from ETL import operation."""
    success: bool
    total_rows: int = 0
    fermentations_created: int = 0
    samples_created: int = 0
    failed_fermentations: List[Dict[str, str]] = field(default_factory=list)  # [{'code': 'FERM-001', 'error': 'message'}]
    errors: List[str] = field(default_factory=list)
    row_errors: Dict[int, List[str]] = field(default_factory=dict)
    phase_failed: Optional[str] = None  # 'pre_validation', 'row_validation', 'post_validation', 'import'
    duration_seconds: float = 0.0


class ETLService:
    """
    Service for orchestrating ETL import process.
    
    Coordinates validation, entity creation, and transaction management
    for historical fermentation data import (ADR-019, ADR-030, ADR-031).
    
    Architecture Evolution (ADR-031):
    - Uses TransactionScope for cross-module transaction coordination
    - Creates repositories directly with shared session manager
    - Enables atomic operations across fermentation + fruit_origin modules
    """
    
    def __init__(self, session_manager: ISessionManager, fruit_origin_service: IFruitOriginService):
        """
        Initialize ETL service.
        
        Args:
            session_manager: Session manager for transaction coordination (ADR-031)
            fruit_origin_service: Service for fruit origin orchestration (ADR-030)
        """
        self._session_manager = session_manager
        self.fruit_origin_service = fruit_origin_service
        self.validator = ETLValidator()
    
    async def import_file(
        self, 
        file_path: Path, 
        winery_id: int, 
        user_id: int,
        progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> ImportResult:
        """
        Import fermentation data from Excel file.
        
        Performs 3-layer validation, creates entities with data_source=IMPORTED,
        and manages transactions. Supports progress tracking and cancellation (ADR-030 Phase 3).
        
        Args:
            file_path: Path to Excel file to import
            winery_id: ID of the winery performing the import (from authenticated user)
            user_id: ID of the user performing the import (from authenticated user)
            progress_callback: Optional async callback invoked after each fermentation.
                             Receives (current: int, total: int) for progress tracking.
            cancellation_token: Optional token to cancel import gracefully.
                              Check is_cancelled property to stop import.
            
        Returns:
            ImportResult with success status and statistics
            
        Raises:
            ImportCancelledException: If cancellation_token.is_cancelled becomes True
        """
        start_time = time.time()
        result = ImportResult(success=False)
        
        try:
            # Phase 1: Pre-validation (schema check)
            pre_result = await self.validator.pre_validate(file_path)
            if not pre_result.is_valid:
                result.phase_failed = 'pre_validation'
                result.errors = pre_result.errors
                result.duration_seconds = time.time() - start_time
                return result
            
            # Phase 2: Row-validation (data quality)
            row_result = await self.validator.validate_rows(file_path)
            if row_result.invalid_row_count > 0:
                result.phase_failed = 'row_validation'
                result.row_errors = row_result.row_errors
                result.duration_seconds = time.time() - start_time
                return result
            
            # Phase 3: Post-validation (business rules)
            post_result = await self.validator.post_validate(file_path)
            if post_result.invalid_row_count > 0:
                result.phase_failed = 'post_validation'
                result.row_errors = post_result.row_errors
                result.duration_seconds = time.time() - start_time
                return result
            
            # All validations passed - proceed with import
            df = pd.read_excel(file_path, engine='openpyxl')
            df.columns = df.columns.str.strip().str.lower()
            result.total_rows = len(df)
            
            # Import data with per-fermentation transactions (partial success)
            fermentations_created, samples_created, failed_fermentations = await self._import_data(
                df, 
                winery_id, 
                user_id,
                progress_callback,
                cancellation_token
            )
            
            result.fermentations_created = fermentations_created
            result.samples_created = samples_created
            result.failed_fermentations = failed_fermentations
            
            # Success if at least one fermentation imported, or all failed but gracefully
            result.success = fermentations_created > 0 or len(failed_fermentations) == 0
        
        except ImportCancelledException:
            # Re-raise cancellation exceptions (don't catch them as generic errors)
            raise
        
        except Exception as e:
            result.phase_failed = 'import'
            result.errors = [f"Unexpected error: {str(e)}"]
        
        result.duration_seconds = time.time() - start_time
        return result
    
    async def _import_data(
        self, 
        df: pd.DataFrame, 
        winery_id: int, 
        user_id: int,
        progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> tuple[int, int, List[Dict[str, str]]]:
        """
        Import fermentations and samples from validated dataframe.
        
        Uses per-fermentation transactions for partial success (ADR-030).
        If one fermentation fails, successful ones are still saved.
        
        Creates complete entity hierarchy using orchestration services (ADR-030):
        1-3. Orchestrate vineyard → block → harvest lot (via FruitOriginService)
        4. Create Fermentation
        5. Create FermentationLotSource (link HarvestLot → Fermentation)
        6. Create Samples (density, temperature, optional sugar)
        
        Performance optimizations:
        - Uses ensure_harvest_lot_for_import() to eliminate N+1 queries
        - Reuses shared default blocks (prevents UNIQUE constraint violations)
        - Handles optional vineyard_name and grape_variety gracefully
        
        Progress tracking (ADR-030 Phase 3):
        - Invokes progress_callback after each fermentation if provided
        - Checks cancellation_token before each fermentation
        - Raises ImportCancelledException if cancelled
        
        Args:
            df: Validated pandas DataFrame
            winery_id: ID of the winery performing the import
            user_id: ID of the user performing the import
            progress_callback: Optional async callback for progress updates (current, total)
            cancellation_token: Optional token to check for cancellation
            
        Returns:
            Tuple of (fermentations_created, samples_created, failed_fermentations)
            
        Raises:
            ImportCancelledException: If cancellation requested via token
        """
        fermentations_created = 0
        samples_created = 0
        failed_fermentations = []
        
        # Group by fermentation code
        grouped = df.groupby('fermentation_code')
        total_fermentations = len(grouped)
        
        for i, (ferm_code, group_df) in enumerate(grouped):
            # Check for cancellation before processing each fermentation
            if cancellation_token and cancellation_token.is_cancelled:
                raise ImportCancelledException(
                    imported=fermentations_created,
                    total=total_fermentations
                )
            
            try:
                # Each fermentation gets its own transaction for partial success
                # TransactionScope coordinates fruit_origin + fermentation operations (ADR-031)
                async with TransactionScope(self._session_manager):
                    # Create repositories with shared session manager
                    fermentation_repo = FermentationRepository(self._session_manager)
                    lot_source_repo = LotSourceRepository(self._session_manager)
                    sample_repo = SampleRepository(self._session_manager)
                    
                    # Get data from first row for fermentation-level info
                    first_row = group_df.iloc[0]
            
                    # Steps 1-3: Orchestrate vineyard → block → harvest lot creation
                    # Uses FruitOriginService.ensure_harvest_lot_for_import() (ADR-030)
                    # - Eliminates N+1 vineyard queries
                    # - Fixes duplicate block bug (reuses shared default blocks)
                    # - Handles optional vineyard_name and grape_variety
                    vineyard_name_raw = first_row.get('vineyard_name')
                    vineyard_name = str(vineyard_name_raw).strip() if pd.notna(vineyard_name_raw) and str(vineyard_name_raw).strip() else None
                    
                    grape_variety_raw = first_row.get('grape_variety')
                    grape_variety = str(grape_variety_raw).strip() if pd.notna(grape_variety_raw) and str(grape_variety_raw).strip() else None
                    
                    harvest_date = pd.to_datetime(first_row['harvest_date']).date()
                    harvest_mass_kg = Decimal(str(first_row['harvest_mass_kg']))
                    
                    harvest_lot = await self.fruit_origin_service.ensure_harvest_lot_for_import(
                        winery_id=winery_id,
                        vineyard_name=vineyard_name,
                        grape_variety=grape_variety,
                        harvest_date=harvest_date,
                        harvest_mass_kg=harvest_mass_kg
                    )
                    
                    # Step 4: Create Fermentation
                    fermentation_start_date = pd.to_datetime(first_row['fermentation_start_date'])
                    initial_density = float(first_row['density'])
                    initial_sugar_brix = float(first_row.get('sugar_brix', 0)) if pd.notna(first_row.get('sugar_brix')) else 0.0
                    
                    fermentation_data = FermentationCreate(
                        fermented_by_user_id=user_id,
                        vintage_year=harvest_date.year,
                        yeast_strain="IMPORTED - Unknown",
                        vessel_code=ferm_code,
                        input_mass_kg=float(harvest_mass_kg),
                        initial_sugar_brix=initial_sugar_brix,
                        initial_density=initial_density,
                        start_date=fermentation_start_date
                    )
                    created_fermentation = await fermentation_repo.create(winery_id, fermentation_data)
                    
                    # Step 5: Create FermentationLotSource (link HarvestLot → Fermentation)
                    lot_source_data = LotSourceData(
                        harvest_lot_id=harvest_lot.id,
                        mass_used_kg=float(harvest_mass_kg),  # Single source, all mass used
                        notes="Created from historical data import"
                    )
                    await lot_source_repo.create(
                        fermentation_id=created_fermentation.id,
                        winery_id=winery_id,
                        data=lot_source_data
                    )
                    
                    # Step 6: Create samples for this fermentation
                    ferm_samples_created = 0
                    for idx, row in group_df.iterrows():
                        sample_data_list = self._prepare_sample_data(created_fermentation.id, row, user_id)
                        for sample_data in sample_data_list:
                            sample_class = sample_data.pop('_class')
                            sample = sample_class(**sample_data)
                            await sample_repo.create(sample)
                            ferm_samples_created += 1
                    
                    # TransactionScope automatically commits on successful exit
                    
                    # Success - increment counters
                    fermentations_created += 1
                    samples_created += ferm_samples_created
                    
                    # Invoke progress callback if provided
                    if progress_callback:
                        await progress_callback(current=i + 1, total=total_fermentations)
                    
            except Exception as e:
                # Note: Rollback is automatic via context manager (__aexit__)
                # No need for explicit rollback here
                
                # Track failure but continue with remaining fermentations
                failed_fermentations.append({
                    'code': str(ferm_code),
                    'error': str(e)
                })
        
        return fermentations_created, samples_created, failed_fermentations
    def _prepare_sample_data(self, fermentation_id: str, row: pd.Series, user_id: int) -> List[dict]:
        """Prepare sample data dictionaries from dataframe row."""
        sample_data_list = []
        sample_date = pd.to_datetime(row['sample_date'])
        
        # Always create density and temperature samples (required)
        sample_data_list.append({
            '_class': DensitySample,
            'fermentation_id': fermentation_id,
            'recorded_by_user_id': user_id,
            'recorded_at': sample_date,
            'value': float(row['density']),
            'data_source': DataSource.IMPORTED
        })
        
        sample_data_list.append({
            '_class': CelsiusTemperatureSample,
            'fermentation_id': fermentation_id,
            'recorded_by_user_id': user_id,
            'recorded_at': sample_date,
            'value': float(row['temperature_celsius']),
            'data_source': DataSource.IMPORTED
        })
        
        # Create sugar sample if present (optional)
        if 'sugar_brix' in row and pd.notna(row['sugar_brix']):
            sample_data_list.append({
                '_class': SugarSample,
                'fermentation_id': fermentation_id,
                'recorded_by_user_id': user_id,
                'recorded_at': sample_date,
                'value': float(row['sugar_brix']),
                'data_source': DataSource.IMPORTED
            })
        
        return sample_data_list
