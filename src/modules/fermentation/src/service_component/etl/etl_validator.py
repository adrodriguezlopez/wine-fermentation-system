"""
ETL Validator for Historical Data Import.

Implements 3-layer validation strategy (ADR-019):
1. Pre-validation: Schema and file checks (fail fast)
2. Row-validation: Data validation per row (granular errors)
3. Post-validation: Business rules and integrity (after loading)
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict
import pandas as pd

from src.modules.fermentation.src.service_component.services.validation_service import ValidationService
from src.modules.fermentation.src.domain.enums.sample_type import SampleType


@dataclass
class PreValidationResult:
    """Result from pre-validation (schema check)."""
    is_valid: bool
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class RowValidationResult:
    """Result from row-by-row data validation."""
    valid_row_count: int = 0
    invalid_row_count: int = 0
    row_errors: Dict[int, List[str]] = field(default_factory=dict)


@dataclass
class PostValidationResult:
    """Result from post-validation (business rules and chronology)."""
    valid_row_count: int = 0
    invalid_row_count: int = 0
    row_errors: Dict[int, List[str]] = field(default_factory=dict)


class ETLValidator:
    """
    Validator for ETL pipeline with 3-layer validation.
    
    Following ADR-019 validation strategy.
    Reuses existing ValueValidationService for business logic consistency.
    """
    
    # File size limit: 50MB
    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
    
    # Required columns from ADR-019 specification
    REQUIRED_COLUMNS: Set[str] = {
        'fermentation_code',
        'fermentation_start_date',
        'fermentation_end_date',
        'harvest_date',
        'harvest_mass_kg',
        'sample_date',
        'density',
        'temperature_celsius'
        # vineyard_name and grape_variety are OPTIONAL
        # If missing, defaults will be used: "UNKNOWN" and "Unknown" respectively
    }
    
    # Validation ranges for numeric fields (aligned with domain rules)
    DENSITY_MIN = 0.990
    DENSITY_MAX = 1.200
    TEMPERATURE_MIN = 0
    TEMPERATURE_MAX = 40
    SUGAR_BRIX_MIN = 0
    SUGAR_BRIX_MAX = 40
    
    # Field groups for validation
    FERMENTATION_REQUIRED_FIELDS = [
        'fermentation_code',
        'fermentation_start_date',
        'fermentation_end_date',
        'harvest_date',
        'harvest_mass_kg'
        # vineyard_name and grape_variety are OPTIONAL
    ]
    
    SAMPLE_REQUIRED_FIELDS = [
        'sample_date',
        'density',
        'temperature_celsius'
    ]
    
    DATE_FIELDS = [
        'fermentation_start_date',
        'fermentation_end_date',
        'harvest_date',
        'sample_date'
    ]
    
    NUMERIC_FIELDS = [
        'harvest_mass_kg',
        'density',
        'temperature_celsius'
    ]
    
    def __init__(self):
        """Initialize with reusable validation services."""
        self.validation_service = ValidationService(sample_repository=None)
    
    async def pre_validate(self, file_path: Path) -> PreValidationResult:
        """
        Pre-validation: Check file size and basic schema.
        
        Fails fast before loading data into memory.
        
        Args:
            file_path: Path to Excel file to validate
            
        Returns:
            PreValidationResult with validation status and errors
        """
        errors = []
        
        # Check file size (fail fast - don't read large files)
        if not self._validate_file_size(file_path, errors):
            return PreValidationResult(is_valid=False, errors=errors)
        
        # Check Excel structure (columns and data)
        self._validate_excel_structure(file_path, errors)
        
        return PreValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def _validate_file_size(self, file_path: Path, errors: List[str]) -> bool:
        """
        Validate file size is within limits.
        
        Args:
            file_path: Path to file
            errors: List to append errors to
            
        Returns:
            True if validation should continue, False to stop early
        """
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            errors.append(
                f"File too large ({size_mb:.1f}MB). Maximum 50MB allowed."
            )
            return False
        return True
    
    def _validate_excel_structure(self, file_path: Path, errors: List[str]) -> None:
        """
        Validate Excel file has required columns and data rows.
        
        Args:
            file_path: Path to Excel file
            errors: List to append errors to
        """
        try:
            # Read first row to check both headers and data presence
            df = pd.read_excel(file_path, nrows=1, engine='openpyxl')
            
            # Validate columns
            self._validate_required_columns(df.columns, errors)
            
            # Validate data presence
            if len(df) == 0:
                errors.append("File is empty. No data rows found.")
                
        except Exception as e:
            errors.append(f"Error reading file: {str(e)}")
    
    def _validate_required_columns(
        self, file_columns: pd.Index, errors: List[str]
    ) -> None:
        """
        Validate all required columns are present.
        
        Args:
            file_columns: Column names from Excel file
            errors: List to append errors to
        """
        normalized_columns = set(file_columns.str.lower().str.strip())
        required_lower = {col.lower() for col in self.REQUIRED_COLUMNS}
        missing = required_lower - normalized_columns
        
        if missing:
            missing_list = sorted(missing)
            errors.append(
                f"Missing required columns: {', '.join(missing_list)}"
            )
    
    async def validate_rows(self, file_path: Path) -> RowValidationResult:
        """
        Row-validation: Validate data quality for each row.
        
        Args:
            file_path: Path to Excel file to validate
            
        Returns:
            RowValidationResult with counts and per-row errors
        """
        result = RowValidationResult()
        
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Validate each row
            for index, row in df.iterrows():
                row_errors = []
                
                # Validate fermentation fields
                self._validate_fermentation_fields(row, row_errors)
                
                # Validate sample fields
                self._validate_sample_fields(row, row_errors)
                
                # Validate date formats
                self._validate_date_fields(row, row_errors)
                
                # Validate numeric ranges
                self._validate_numeric_ranges(row, row_errors)
                
                # Validate numeric types
                self._validate_numeric_types(row, row_errors)
                
                # Store results
                if row_errors:
                    result.invalid_row_count += 1
                    result.row_errors[int(index)] = row_errors
                else:
                    result.valid_row_count += 1
                    
        except Exception as e:
            # If we can't read the file, mark all as invalid
            result.invalid_row_count = 1
            result.row_errors[0] = [f"Error reading file: {str(e)}"]
        
        return result
    
    def _validate_fermentation_fields(
        self, row: pd.Series, errors: List[str]
    ) -> None:
        """Validate required fermentation fields."""
        self._validate_required_fields(row, self.FERMENTATION_REQUIRED_FIELDS, errors)
    
    def _validate_sample_fields(
        self, row: pd.Series, errors: List[str]
    ) -> None:
        """Validate required sample fields."""
        self._validate_required_fields(row, self.SAMPLE_REQUIRED_FIELDS, errors)
    
    def _validate_required_fields(
        self, row: pd.Series, fields: List[str], errors: List[str]
    ) -> None:
        """Generic validation for required fields."""
        for field in fields:
            if not self._is_field_present(row, field):
                errors.append(f"{field} is required")
    
    def _is_field_present(self, row: pd.Series, field: str) -> bool:
        """Check if field has a non-empty value."""
        value = row.get(field)
        return pd.notna(value) and str(value).strip() != ''
    
    def _validate_date_fields(
        self, row: pd.Series, errors: List[str]
    ) -> None:
        """Validate date formats."""
        for field in self.DATE_FIELDS:
            if self._is_field_present(row, field):
                if not self._is_valid_date(row.get(field)):
                    errors.append(f"{field} has invalid date format")
    
    def _is_valid_date(self, value) -> bool:
        """Check if value can be parsed as a date."""
        try:
            pd.to_datetime(value)
            return True
        except:
            return False
    
    def _validate_numeric_ranges(
        self, row: pd.Series, errors: List[str]
    ) -> None:
        """Validate numeric values are within valid ranges."""
        # Density validation
        self._validate_range(
            row, 'density', self.DENSITY_MIN, self.DENSITY_MAX, errors
        )
        
        # Temperature validation
        self._validate_range(
            row, 'temperature_celsius', self.TEMPERATURE_MIN, self.TEMPERATURE_MAX, errors
        )
        
        # Sugar Brix validation (optional field)
        if self._is_field_present(row, 'sugar_brix'):
            self._validate_range(
                row, 'sugar_brix', self.SUGAR_BRIX_MIN, self.SUGAR_BRIX_MAX, errors
            )
        
        # Harvest mass must be positive
        self._validate_positive_number(row, 'harvest_mass_kg', errors)
    
    def _validate_range(
        self, row: pd.Series, field: str, min_val: float, max_val: float, errors: List[str]
    ) -> None:
        """Validate numeric field is within specified range using ValidationService."""
        value = row.get(field)
        if pd.notna(value):
            # Map field names to sample types for proper validation
            sample_type_map = {
                'density': SampleType.DENSITY,
                'temperature_celsius': SampleType.TEMPERATURE,
                'sugar_brix': SampleType.SUGAR
            }
            
            # First validate it's a valid sample value (type and numeric check)
            sample_type = sample_type_map.get(field)
            if sample_type:
                result = self.validation_service.validate_sample_value(sample_type, value)
                if not result.is_valid:
                    # Add our own error message for consistency with tests
                    errors.append(f"{field} out of range ({min_val} - {max_val})")
                    return
            
            # Then validate the range
            try:
                num_val = float(value)
                if num_val < min_val or num_val > max_val:
                    errors.append(f"{field} out of range ({min_val} - {max_val})")
            except (ValueError, TypeError):
                pass  # Already caught by validate_sample_value
    
    def _validate_positive_number(
        self, row: pd.Series, field: str, errors: List[str]
    ) -> None:
        """Validate numeric field is positive (> 0) using ValidationService."""
        value = row.get(field)
        if pd.notna(value):
            # Use sample value validation which checks for numeric type and negative values
            result = self.validation_service.validate_sample_value(
                sample_type=SampleType.DENSITY,  # Any type works for basic validation
                value=value
            )
            if not result.is_valid:
                # ValidationService found an error (None, empty string, non-numeric, or negative)
                errors.append(f"{field} must be positive")
                return
            
            # ValidationService accepts 0, but we need to reject it for fields like harvest_mass
            try:
                num_val = float(value)
                if num_val <= 0:
                    errors.append(f"{field} must be positive")
            except (ValueError, TypeError):
                pass  # Already caught by ValidationService
    
    def _validate_numeric_types(
        self, row: pd.Series, errors: List[str]
    ) -> None:
        """Validate numeric fields contain valid numbers using ValidationService."""
        # Map fields to their corresponding sample types
        field_to_sample_type = {
            'density': SampleType.DENSITY,
            'temperature_celsius': SampleType.TEMPERATURE,
            'harvest_mass_kg': SampleType.DENSITY  # Use any type for generic numeric check
        }
        
        for field in self.NUMERIC_FIELDS:
            if self._is_field_present(row, field):
                sample_type = field_to_sample_type.get(field, SampleType.DENSITY)
                result = self.validation_service.validate_sample_value(sample_type, row.get(field))
                if not result.is_valid:
                    # Check if it's a numeric type error
                    if any('valid number' in err.message.lower() for err in result.errors):
                        errors.append(f"{field} must be numeric")
    
    async def post_validate(self, file_path: Path) -> PostValidationResult:
        """
        Perform post-validation: business rules and chronology checks.
        
        Validates:
        - Date chronology: harvest < start < end, samples within fermentation period
        - Sample chronology: samples in ascending order per fermentation
        - Business rules: sugar and density trends
        
        Args:
            file_path: Path to the Excel file to validate
            
        Returns:
            PostValidationResult with validation results and errors
        """
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()
        
        row_errors: Dict[int, List[str]] = {}
        
        # Parse dates once for efficiency
        df['harvest_date_parsed'] = pd.to_datetime(df['harvest_date'], errors='coerce')
        df['start_date_parsed'] = pd.to_datetime(df['fermentation_start_date'], errors='coerce')
        df['end_date_parsed'] = pd.to_datetime(df['fermentation_end_date'], errors='coerce')
        df['sample_date_parsed'] = pd.to_datetime(df['sample_date'], errors='coerce')
        
        # Group by fermentation_code for chronological validation
        grouped = df.groupby('fermentation_code')
        
        for idx, row in df.iterrows():
            errors: List[str] = []
            
            # Validate fermentation date chronology
            self._validate_fermentation_chronology(row, errors)
            
            # Validate sample date within fermentation period
            self._validate_sample_within_period(row, errors)
            
            if errors:
                row_errors[idx] = errors
        
        # Validate sample chronology and trends per fermentation
        for ferm_code, group_df in grouped:
            self._validate_sample_chronology(group_df, row_errors)
            self._validate_sugar_trend(group_df, row_errors)
            self._validate_density_trend(group_df, row_errors)
        
        valid_row_count = len(df) - len(row_errors)
        invalid_row_count = len(row_errors)
        
        return PostValidationResult(
            valid_row_count=valid_row_count,
            invalid_row_count=invalid_row_count,
            row_errors=row_errors
        )
    
    def _validate_fermentation_chronology(
        self, row: pd.Series, errors: List[str]
    ) -> None:
        """Validate fermentation dates are in correct chronological order."""
        harvest = row.get('harvest_date_parsed')
        start = row.get('start_date_parsed')
        end = row.get('end_date_parsed')
        
        if pd.notna(harvest) and pd.notna(start) and harvest >= start:
            errors.append("harvest_date must be before fermentation_start_date")
        
        if pd.notna(start) and pd.notna(end) and start >= end:
            errors.append("fermentation_start_date must be before fermentation_end_date (invalid date chronology)")
    
    def _validate_sample_within_period(
        self, row: pd.Series, errors: List[str]
    ) -> None:
        """Validate sample date is within fermentation period."""
        sample_date = row.get('sample_date_parsed')
        start = row.get('start_date_parsed')
        end = row.get('end_date_parsed')
        
        if pd.notna(sample_date) and pd.notna(start) and sample_date < start:
            errors.append("sample_date cannot be before fermentation_start_date")
        
        if pd.notna(sample_date) and pd.notna(end) and sample_date > end:
            errors.append("sample_date cannot be after fermentation_end_date")
    
    def _validate_sample_chronology(
        self, group_df: pd.DataFrame, row_errors: Dict[int, List[str]]
    ) -> None:
        """Validate samples are in chronological order for a fermentation."""
        # Don't sort - validate the order as they appear in the file
        prev_date = None
        for idx, row in group_df.iterrows():
            sample_date = row.get('sample_date_parsed')
            
            if pd.notna(sample_date):
                if prev_date is not None and sample_date < prev_date:
                    # Sample is out of chronological order
                    if idx not in row_errors:
                        row_errors[idx] = []
                    row_errors[idx].append("sample not in chronological order for fermentation")
                prev_date = sample_date
    
    def _validate_sugar_trend(
        self, group_df: pd.DataFrame, row_errors: Dict[int, List[str]]
    ) -> None:
        """Validate sugar decreases over time for a fermentation."""
        if 'sugar_brix' not in group_df.columns:
            return  # Optional field
        
        # Sort by sample date and filter out NaN sugar values
        sorted_df = group_df.sort_values('sample_date_parsed')
        sorted_df = sorted_df[pd.notna(sorted_df['sugar_brix'])]
        
        prev_sugar = None
        for idx, row in sorted_df.iterrows():
            sugar = row.get('sugar_brix')
            
            if pd.notna(sugar):
                if prev_sugar is not None and sugar > prev_sugar:
                    # Sugar increased (invalid)
                    if idx not in row_errors:
                        row_errors[idx] = []
                    row_errors[idx].append("sugar_brix must decrease over time")
                prev_sugar = sugar
    
    def _validate_density_trend(
        self, group_df: pd.DataFrame, row_errors: Dict[int, List[str]]
    ) -> None:
        """Validate density decreases over time for a fermentation."""
        # Sort by sample date
        sorted_df = group_df.sort_values('sample_date_parsed')
        
        prev_density = None
        for idx, row in sorted_df.iterrows():
            density = row.get('density')
            
            if pd.notna(density):
                if prev_density is not None and density > prev_density:
                    # Density increased (invalid)
                    if idx not in row_errors:
                        row_errors[idx] = []
                    row_errors[idx].append("density must decrease over time")
                prev_density = density
