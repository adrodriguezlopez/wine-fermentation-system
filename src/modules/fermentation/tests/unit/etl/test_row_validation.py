"""
Unit tests for ETL Row Validation.

Tests the row-level data validation for historical data import (ADR-019 Layer 2).
"""
import pytest
import pandas as pd
from pathlib import Path
from src.modules.fermentation.src.service_component.etl.etl_validator import (
    ETLValidator
)


class TestRowValidation:
    """Tests for row-validation layer (data quality checks)."""
    
    @pytest.mark.asyncio
    async def test_validates_required_fermentation_fields(self, tmp_path):
        """Row-validation should detect missing required fermentation fields."""
        excel_file = tmp_path / "missing_fermentation_fields.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['', 'FERM-002'],  # Row 0 missing code
            'fermentation_start_date': ['2023-03-10', ''],  # Row 1 missing start
            'fermentation_end_date': ['2023-04-10', '2023-04-20'],
            'harvest_date': ['2023-03-05', '2023-03-06'],
            'vineyard_name': ['Viña Norte', 'Viña Sur'],  # OPTIONAL - no longer required
            'grape_variety': ['Cabernet', 'Merlot'],  # OPTIONAL - no longer required
            'harvest_mass_kg': [1500, 1600],
            'sample_date': ['2023-03-14', '2023-03-15'],
            'density': [1.090, 1.085],
            'temperature_celsius': [18, 19]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.validate_rows(excel_file)
        
        assert result.valid_row_count == 0
        assert result.invalid_row_count == 2
        assert len(result.row_errors) == 2
        # Row 0 should have error for missing code
        assert any('fermentation_code' in err.lower() for err in result.row_errors[0])
        # Row 1 should have error for missing start date
        assert any('fermentation_start_date' in err.lower() for err in result.row_errors[1])
    
    @pytest.mark.asyncio
    async def test_validates_required_sample_fields(self, tmp_path):
        """Row-validation should detect missing required sample fields."""
        excel_file = tmp_path / "missing_sample_fields.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet Sauvignon', 'Cabernet Sauvignon'],
            'harvest_mass_kg': [1500, 1600],
            'sample_date': ['', '2023-03-15'],  # Row 0 missing date
            'density': [1.090, ''],  # Row 1 missing density
            'temperature_celsius': ['', 19]  # Row 0 missing temp
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.validate_rows(excel_file)
        
        assert result.invalid_row_count == 2
        assert any('sample_date' in err.lower() for err in result.row_errors[0])
        assert any('temperature' in err.lower() for err in result.row_errors[0])
        assert any('density' in err.lower() for err in result.row_errors[1])
    
    @pytest.mark.asyncio
    async def test_validates_date_formats(self, tmp_path):
        """Row-validation should detect invalid date formats."""
        excel_file = tmp_path / "invalid_dates.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003'],
            'fermentation_start_date': ['invalid-date', '2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '32/13/2023', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500, 1500],
            'sample_date': ['2023-03-14', '2023-03-14', 'not-a-date'],
            'density': [1.090, 1.090, 1.090],
            'temperature_celsius': [18, 18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.validate_rows(excel_file)
        
        assert result.invalid_row_count == 3
        assert any('fermentation_start_date' in err.lower() for err in result.row_errors[0])
        assert any('fermentation_end_date' in err.lower() for err in result.row_errors[1])
        assert any('sample_date' in err.lower() for err in result.row_errors[2])
    
    @pytest.mark.asyncio
    async def test_validates_density_range(self, tmp_path):
        """Row-validation should detect density values outside valid range."""
        excel_file = tmp_path / "invalid_density.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500, 1500],
            'sample_date': ['2023-03-14', '2023-03-14', '2023-03-14'],
            'density': [0.800, 1.090, 1.300],  # Row 0 too low, Row 2 too high
            'temperature_celsius': [18, 18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.validate_rows(excel_file)
        
        assert result.valid_row_count == 1
        assert result.invalid_row_count == 2
        assert any('density' in err.lower() and 'range' in err.lower() for err in result.row_errors[0])
        assert any('density' in err.lower() and 'range' in err.lower() for err in result.row_errors[2])
    
    @pytest.mark.asyncio
    async def test_validates_temperature_range(self, tmp_path):
        """Row-validation should detect temperature values outside valid range."""
        excel_file = tmp_path / "invalid_temperature.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500, 1500],
            'sample_date': ['2023-03-14', '2023-03-14', '2023-03-14'],
            'density': [1.090, 1.090, 1.090],
            'temperature_celsius': [-5, 18, 45]  # Row 0 too low, Row 2 too high
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.validate_rows(excel_file)
        
        assert result.valid_row_count == 1
        assert result.invalid_row_count == 2
        assert any('temperature' in err.lower() and 'range' in err.lower() for err in result.row_errors[0])
        assert any('temperature' in err.lower() and 'range' in err.lower() for err in result.row_errors[2])
    
    @pytest.mark.asyncio
    async def test_validates_sugar_brix_range_when_present(self, tmp_path):
        """Row-validation should validate sugar_brix range when column exists."""
        excel_file = tmp_path / "invalid_sugar.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500, 1500],
            'sample_date': ['2023-03-14', '2023-03-14', '2023-03-14'],
            'density': [1.090, 1.090, 1.090],
            'temperature_celsius': [18, 18, 18],
            'sugar_brix': [-2, 22.5, 50]  # Row 0 negative, Row 2 too high
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.validate_rows(excel_file)
        
        assert result.valid_row_count == 1
        assert result.invalid_row_count == 2
        assert any('sugar' in err.lower() or 'brix' in err.lower() for err in result.row_errors[0])
        assert any('sugar' in err.lower() or 'brix' in err.lower() for err in result.row_errors[2])
    
    @pytest.mark.asyncio
    async def test_validates_harvest_mass_positive(self, tmp_path):
        """Row-validation should detect negative or zero harvest mass."""
        excel_file = tmp_path / "invalid_harvest_mass.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet'],
            'harvest_mass_kg': [-100, 0, 1500],  # Row 0 negative, Row 1 zero
            'sample_date': ['2023-03-14', '2023-03-14', '2023-03-14'],
            'density': [1.090, 1.090, 1.090],
            'temperature_celsius': [18, 18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.validate_rows(excel_file)
        
        assert result.valid_row_count == 1
        assert result.invalid_row_count == 2
        assert any('harvest_mass' in err.lower() and 'positive' in err.lower() for err in result.row_errors[0])
        assert any('harvest_mass' in err.lower() and 'positive' in err.lower() for err in result.row_errors[1])
    
    @pytest.mark.asyncio
    async def test_validates_numeric_types(self, tmp_path):
        """Row-validation should detect non-numeric values in numeric fields."""
        excel_file = tmp_path / "invalid_numeric.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet'],
            'harvest_mass_kg': ['not-a-number', 1500],
            'sample_date': ['2023-03-14', '2023-03-14'],
            'density': [1.090, 'invalid'],
            'temperature_celsius': [18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.validate_rows(excel_file)
        
        assert result.invalid_row_count == 2
        assert any('harvest_mass' in err.lower() and 'numeric' in err.lower() for err in result.row_errors[0])
        assert any('density' in err.lower() and 'numeric' in err.lower() for err in result.row_errors[1])
    
    @pytest.mark.asyncio
    async def test_accepts_valid_rows(self, tmp_path):
        """Row-validation should accept rows with all valid data."""
        excel_file = tmp_path / "valid_rows.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-11'],
            'fermentation_end_date': ['2023-04-10', '2023-04-11'],
            'harvest_date': ['2023-03-05', '2023-03-06'],
            'vineyard_name': ['Viña Norte', 'Viña Sur'],
            'grape_variety': ['Cabernet Sauvignon', 'Merlot'],
            'harvest_mass_kg': [1500, 1600],
            'sample_date': ['2023-03-14', '2023-03-15'],
            'density': [1.090, 1.085],
            'temperature_celsius': [18, 19],
            'sugar_brix': [22.5, 21.0]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.validate_rows(excel_file)
        
        assert result.valid_row_count == 2
        assert result.invalid_row_count == 0
        assert len(result.row_errors) == 0
    
    @pytest.mark.asyncio
    async def test_handles_mixed_valid_and_invalid_rows(self, tmp_path):
        """Row-validation should correctly identify mix of valid and invalid rows."""
        excel_file = tmp_path / "mixed_rows.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003', ''],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', 'invalid', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, -100, 1500, 1500],
            'sample_date': ['2023-03-14', '2023-03-14', '2023-03-14', '2023-03-14'],
            'density': [1.090, 1.090, 1.090, 1.090],
            'temperature_celsius': [18, 18, 18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.validate_rows(excel_file)
        
        assert result.valid_row_count == 1  # Only first row is valid
        assert result.invalid_row_count == 3
        assert len(result.row_errors) == 3
