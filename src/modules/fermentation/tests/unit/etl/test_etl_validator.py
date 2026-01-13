"""
Unit tests for ETL Validator.

Tests the 3-layer validation strategy for historical data import (ADR-019).
"""
import pytest
import pandas as pd
from pathlib import Path
from src.modules.fermentation.src.service_component.etl.etl_validator import (
    ETLValidator,
    PreValidationResult
)


class TestPreValidation:
    """Tests for pre-validation layer (schema and file checks)."""
    
    @pytest.mark.asyncio
    async def test_rejects_file_larger_than_50mb(self, tmp_path):
        """
        TDD RED: Pre-validation should reject files > 50MB.
        
        Given: Excel file with size > 50MB
        When: Running pre_validate()
        Then: Returns is_valid=False with size error message
        """
        # Create a mock large file (51MB)
        large_file = tmp_path / "large_import.xlsx"
        with open(large_file, 'wb') as f:
            f.write(b'0' * (51 * 1024 * 1024))  # 51MB
        
        validator = ETLValidator()
        result = await validator.pre_validate(large_file)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "50MB" in result.errors[0]
        assert "too large" in result.errors[0].lower()
    
    @pytest.mark.asyncio
    async def test_rejects_file_with_missing_required_columns(self, tmp_path):
        """
        TDD RED: Pre-validation should detect missing required columns.
        
        Given: Excel file missing required columns (e.g., fermentation_code)
        When: Running pre_validate()
        Then: Returns is_valid=False with missing column names
        """
        # Create Excel with only some columns (missing fermentation_code, sample_date)
        excel_file = tmp_path / "missing_columns.xlsx"
        df = pd.DataFrame({
            'harvest_date': ['2023-03-14'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.pre_validate(excel_file)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        # Should mention the missing columns
        error_msg = ' '.join(result.errors).lower()
        assert 'fermentation_code' in error_msg
        assert 'sample_date' in error_msg
        assert 'missing' in error_msg or 'required' in error_msg
    
    @pytest.mark.asyncio
    async def test_accepts_valid_file_with_all_required_columns(self, tmp_path):
        """Pre-validation should accept file with all required columns."""
        excel_file = tmp_path / "valid_file.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            'grape_variety': ['Cabernet Sauvignon'],
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-14'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.pre_validate(excel_file)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_accepts_file_with_extra_columns(self, tmp_path):
        """Pre-validation should accept file with extra optional columns."""
        excel_file = tmp_path / "extra_columns.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001'],
            'fermentation_start_date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            'grape_variety': ['Cabernet Sauvignon'],
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-14'],
            'density': [1.090],
            'temperature_celsius': [18],
            'sugar_brix': [22.5],  # Optional column
            'notes': ['Sample looks good'],  # Extra column
            'operator': ['Juan Pérez']  # Extra column
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.pre_validate(excel_file)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_rejects_non_excel_file(self, tmp_path):
        """Pre-validation should reject non-Excel files."""
        text_file = tmp_path / "not_excel.txt"
        text_file.write_text("This is not an Excel file")
        
        validator = ETLValidator()
        result = await validator.pre_validate(text_file)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any('error reading file' in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_rejects_corrupted_excel_file(self, tmp_path):
        """Pre-validation should reject corrupted Excel files."""
        corrupted_file = tmp_path / "corrupted.xlsx"
        # Write invalid Excel content
        corrupted_file.write_bytes(b"PK\x03\x04CORRUPTED_EXCEL_DATA")
        
        validator = ETLValidator()
        result = await validator.pre_validate(corrupted_file)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any('error reading file' in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_rejects_empty_excel_file(self, tmp_path):
        """Pre-validation should reject Excel file with no data rows."""
        empty_file = tmp_path / "empty.xlsx"
        # Create Excel with headers but no data
        df = pd.DataFrame(columns=[
            'fermentation_code', 'fermentation_start_date', 'fermentation_end_date',
            'harvest_date', 'vineyard_name', 'grape_variety', 'harvest_mass_kg',
            'sample_date', 'density', 'temperature_celsius'
        ])
        df.to_excel(empty_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.pre_validate(empty_file)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any('empty' in error.lower() or 'no data' in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_handles_case_insensitive_column_names(self, tmp_path):
        """Pre-validation should handle column names case-insensitively."""
        excel_file = tmp_path / "mixed_case.xlsx"
        df = pd.DataFrame({
            'FERMENTATION_CODE': ['FERM-001'],
            'Fermentation_Start_Date': ['2023-03-10'],
            'fermentation_end_date': ['2023-04-10'],
            'HARVEST_DATE': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            'Grape_Variety': ['Cabernet Sauvignon'],
            'HARVEST_MASS_KG': [1500],
            'Sample_Date': ['2023-03-14'],
            'DENSITY': [1.090],
            'Temperature_Celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.pre_validate(excel_file)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_handles_column_names_with_whitespace(self, tmp_path):
        """Pre-validation should handle column names with leading/trailing whitespace."""
        excel_file = tmp_path / "whitespace.xlsx"
        df = pd.DataFrame({
            ' fermentation_code ': ['FERM-001'],
            'fermentation_start_date  ': ['2023-03-10'],
            '  fermentation_end_date': ['2023-04-10'],
            'harvest_date': ['2023-03-05'],
            'vineyard_name': ['Viña Norte'],
            'grape_variety': ['Cabernet Sauvignon'],
            'harvest_mass_kg': [1500],
            'sample_date': ['2023-03-14'],
            'density': [1.090],
            'temperature_celsius': [18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.pre_validate(excel_file)
        
        assert result.is_valid is True
        assert len(result.errors) == 0

