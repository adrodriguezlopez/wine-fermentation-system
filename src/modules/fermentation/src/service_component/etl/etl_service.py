"""
ETL Service for Historical Data Import.

Orchestrates the complete import process:
1. Validates using 3-layer strategy (pre, row, post)
2. Creates fermentations and samples with data_source=IMPORTED
3. Manages transactions and rollback
4. Returns comprehensive import results
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import time
import pandas as pd

from src.modules.fermentation.src.service_component.etl.etl_validator import (
    ETLValidator,
    PreValidationResult,
    RowValidationResult,
    PostValidationResult
)
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource
from src.modules.fermentation.src.domain.enums.data_source import DataSource
from src.modules.fermentation.src.domain.enums.sample_type import SampleType
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.domain.interfaces.unit_of_work_interface import IUnitOfWork
from src.modules.fruit_origin.src.domain.dtos.vineyard_dtos import VineyardCreate
from src.modules.fruit_origin.src.domain.dtos.vineyard_block_dtos import VineyardBlockCreate
from src.modules.fruit_origin.src.domain.dtos.harvest_lot_dtos import HarvestLotCreate


@dataclass
class ImportResult:
    """Result from ETL import operation."""
    success: bool
    total_rows: int = 0
    fermentations_created: int = 0
    samples_created: int = 0
    errors: List[str] = field(default_factory=list)
    row_errors: Dict[int, List[str]] = field(default_factory=dict)
    phase_failed: Optional[str] = None  # 'pre_validation', 'row_validation', 'post_validation', 'import'
    duration_seconds: float = 0.0


class ETLService:
    """
    Service for orchestrating ETL import process.
    
    Coordinates validation, entity creation, and transaction management
    for historical fermentation data import (ADR-019).
    """
    
    def __init__(self, unit_of_work: IUnitOfWork):
        """
        Initialize ETL service.
        
        Args:
            unit_of_work: Unit of work for database transactions
        """
        self.uow = unit_of_work
        self.validator = ETLValidator()
    
    async def import_file(self, file_path: Path, winery_id: int, user_id: int) -> ImportResult:
        """
        Import fermentation data from Excel file.
        
        Performs 3-layer validation, creates entities with data_source=IMPORTED,
        and manages transactions.
        
        Args:
            file_path: Path to Excel file to import
            winery_id: ID of the winery performing the import (from authenticated user)
            user_id: ID of the user performing the import (from authenticated user)
            
        Returns:
            ImportResult with success status and statistics
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
            
            # Import data within transaction
            try:
                async with self.uow:
                    fermentations_created, samples_created = await self._import_data(df, winery_id, user_id)
                    await self.uow.commit()
                    
                    result.success = True
                    result.fermentations_created = fermentations_created
                    result.samples_created = samples_created
            except Exception as e:
                await self.uow.rollback()
                result.phase_failed = 'import'
                result.errors = [f"Database error: {str(e)}"]
        
        except Exception as e:
            result.phase_failed = 'import'
            result.errors = [f"Unexpected error: {str(e)}"]
        
        result.duration_seconds = time.time() - start_time
        return result
    
    async def _import_data(self, df: pd.DataFrame, winery_id: int, user_id: int) -> tuple[int, int]:
        """
        Import fermentations and samples from validated dataframe.
        
        Creates complete entity hierarchy:
        1. Find or create Vineyard (from vineyard_name, or "UNKNOWN" if missing)
        2. Create default VineyardBlock (for historical imports)
        3. Create HarvestLot (with harvest data)
        4. Create Fermentation
        5. Create FermentationLotSource (link HarvestLot → Fermentation)
        6. Create Samples (density, temperature, optional sugar)
        
        Args:
            df: Validated pandas DataFrame
            winery_id: ID of the winery performing the import
            user_id: ID of the user performing the import
            
        Returns:
            Tuple of (fermentations_created, samples_created)
        """
        fermentations_created = 0
        samples_created = 0
        
        # Group by fermentation code
        grouped = df.groupby('fermentation_code')
        
        for ferm_code, group_df in grouped:
            # Get data from first row for fermentation-level info
            first_row = group_df.iloc[0]
            
            # Step 1: Find or create Vineyard
            # Handle missing vineyard_name (use "UNKNOWN" as default)
            vineyard_name_raw = first_row.get('vineyard_name')
            if pd.isna(vineyard_name_raw) or not str(vineyard_name_raw).strip():
                vineyard_name = "UNKNOWN"
            else:
                vineyard_name = str(vineyard_name_raw).strip()
            vineyard = await self.uow.vineyard_repo.get_by_code(vineyard_name, winery_id)
            
            if vineyard is None:
                # Create new vineyard
                vineyard_dto = VineyardCreate(
                    code=vineyard_name,
                    name=vineyard_name,
                    notes="Created during historical data import"
                )
                vineyard = await self.uow.vineyard_repo.create(winery_id, vineyard_dto)
            
            # Step 2: Create default VineyardBlock for historical imports
            # Historical data doesn't have block-specific information
            block_code = f"{vineyard_name}-IMPORTED-DEFAULT"
            vineyard_block_dto = VineyardBlockCreate(
                code=block_code,
                notes="Default block created during historical data import"
            )
            vineyard_block = await self.uow.vineyard_block_repo.create(
                vineyard.id, winery_id, vineyard_block_dto
            )
            
            # Step 3: Create HarvestLot with harvest data from Excel
            harvest_date = pd.to_datetime(first_row['harvest_date']).date()
            harvest_mass_kg = float(first_row['harvest_mass_kg'])
            
            # Handle optional grape_variety
            grape_variety_raw = first_row.get('grape_variety')
            if pd.isna(grape_variety_raw) or not str(grape_variety_raw).strip():
                grape_variety = "Unknown"  # Default value for historical imports
            else:
                grape_variety = str(grape_variety_raw).strip()
            
            harvest_lot_code = f"HL-{ferm_code}"
            harvest_lot_dto = HarvestLotCreate(
                block_id=vineyard_block.id,
                code=harvest_lot_code,
                harvest_date=harvest_date,
                weight_kg=harvest_mass_kg,
                grape_variety=grape_variety,
                notes="Created from historical fermentation data import"
            )
            harvest_lot = await self.uow.harvest_lot_repo.create(winery_id, harvest_lot_dto)
            
            # Step 4: Create Fermentation
            fermentation_start_date = pd.to_datetime(first_row['fermentation_start_date'])
            initial_density = float(first_row['density'])
            initial_sugar_brix = float(first_row.get('sugar_brix', 0)) if pd.notna(first_row.get('sugar_brix')) else 0.0
            
            fermentation = Fermentation(
                winery_id=winery_id,
                fermented_by_user_id=user_id,
                vintage_year=harvest_date.year,
                yeast_strain="IMPORTED - Unknown",
                vessel_code=ferm_code,
                input_mass_kg=harvest_mass_kg,
                initial_sugar_brix=initial_sugar_brix,
                initial_density=initial_density,
                start_date=fermentation_start_date,
                status=FermentationStatus.COMPLETED.value,
                data_source=DataSource.IMPORTED
            )
            created_fermentation = await self.uow.fermentation_repo.create(fermentation)
            fermentations_created += 1
            
            # Step 5: Create FermentationLotSource (link HarvestLot → Fermentation)
            lot_source = FermentationLotSource(
                fermentation_id=created_fermentation.id,
                harvest_lot_id=harvest_lot.id,
                mass_used_kg=harvest_mass_kg,  # Single source, all mass used
                notes="Created from historical data import"
            )
            await self.uow.lot_source_repo.create(lot_source)
            
            # Step 6: Create samples for this fermentation
            for idx, row in group_df.iterrows():
                sample_data_list = self._prepare_sample_data(created_fermentation.id, row)
                for sample_data in sample_data_list:
                    sample_class = sample_data.pop('_class')
                    sample = sample_class(**sample_data)
                    await self.uow.sample_repo.create(sample)
                    samples_created += 1
        
        return fermentations_created, samples_created
    
    def _prepare_sample_data(self, fermentation_id: str, row: pd.Series) -> List[dict]:
        """Prepare sample data dictionaries from dataframe row."""
        sample_data_list = []
        sample_date = pd.to_datetime(row['sample_date'])
        
        # Always create density and temperature samples (required)
        sample_data_list.append({
            '_class': DensitySample,
            'fermentation_id': fermentation_id,
            'recorded_at': sample_date,
            'value': float(row['density']),
            'data_source': DataSource.IMPORTED
        })
        
        sample_data_list.append({
            '_class': CelsiusTemperatureSample,
            'fermentation_id': fermentation_id,
            'recorded_at': sample_date,
            'value': float(row['temperature_celsius']),
            'data_source': DataSource.IMPORTED
        })
        
        # Create sugar sample if present (optional)
        if 'sugar_brix' in row and pd.notna(row['sugar_brix']):
            sample_data_list.append({
                '_class': SugarSample,
                'fermentation_id': fermentation_id,
                'recorded_at': sample_date,
                'value': float(row['sugar_brix']),
                'data_source': DataSource.IMPORTED
            })
        
        return sample_data_list
