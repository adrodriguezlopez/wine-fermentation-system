"""
Tests for ETL post-validation layer.

Post-validation occurs after data is loaded and validates:
- Date chronology (harvest_date < start_date < end_date < sample_dates)
- Sample chronology (samples must be in ascending time order)
- Business rules (sugar trend, sample count minimum)
- Data integrity across related records
"""
import pandas as pd
import pytest
from pathlib import Path
from src.modules.fermentation.src.service_component.etl.etl_validator import ETLValidator


class TestPostValidation:
    """Test suite for post-validation business rules and chronology checks."""
    
    @pytest.mark.asyncio
    async def test_validates_fermentation_date_chronology(self, tmp_path):
        """Post-validation should ensure harvest < start < end dates."""
        excel_file = tmp_path / "invalid_date_chronology.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002', 'FERM-003'],
            'fermentation_start_date': ['2023-03-10', '2023-03-20', '2023-03-05'],
            'fermentation_end_date': ['2023-04-10', '2023-03-15', '2023-04-10'],  # Row 1: end before start
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-10'],  # Row 2: harvest after start
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500, 1500],
            'sample_date': ['2023-03-14', '2023-03-14', '2023-03-14'],
            'density': [1.090, 1.090, 1.090],
            'temperature_celsius': [18, 18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.post_validate(excel_file)
        
        assert result.valid_row_count == 1
        assert result.invalid_row_count == 2
        assert 1 in result.row_errors
        assert 2 in result.row_errors
        assert any('date' in err.lower() and 'chronology' in err.lower() for err in result.row_errors[1])
        assert any('harvest' in err.lower() and 'start' in err.lower() for err in result.row_errors[2])
    
    @pytest.mark.asyncio
    async def test_validates_sample_date_after_fermentation_start(self, tmp_path):
        """Post-validation should ensure sample_date >= fermentation_start_date."""
        excel_file = tmp_path / "sample_before_start.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500],
            'sample_date': ['2023-03-08', '2023-03-15'],  # Row 0: sample before start
            'density': [1.090, 1.090],
            'temperature_celsius': [18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.post_validate(excel_file)
        
        assert result.valid_row_count == 1
        assert result.invalid_row_count == 1
        assert 0 in result.row_errors
        assert any('sample' in err.lower() and 'before' in err.lower() for err in result.row_errors[0])
    
    @pytest.mark.asyncio
    async def test_validates_sample_date_before_fermentation_end(self, tmp_path):
        """Post-validation should ensure sample_date <= fermentation_end_date."""
        excel_file = tmp_path / "sample_after_end.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500],
            'sample_date': ['2023-04-15', '2023-03-15'],  # Row 0: sample after end
            'density': [1.090, 1.090],
            'temperature_celsius': [18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.post_validate(excel_file)
        
        assert result.valid_row_count == 1
        assert result.invalid_row_count == 1
        assert 0 in result.row_errors
        assert any('sample' in err.lower() and 'after' in err.lower() for err in result.row_errors[0])
    
    @pytest.mark.asyncio
    async def test_validates_samples_in_chronological_order_per_fermentation(self, tmp_path):
        """Post-validation should ensure samples for same fermentation are in time order."""
        excel_file = tmp_path / "samples_out_of_order.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-001', 'FERM-001', 'FERM-002', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-10', '2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-10', '2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05', '2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte', 'Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet', 'Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500, 1500, 1500, 1500],
            'sample_date': ['2023-03-15', '2023-03-12', '2023-03-18', '2023-03-15', '2023-03-18'],  # FERM-001 row 1 is out of order
            'density': [1.090, 1.085, 1.080, 1.090, 1.085],
            'temperature_celsius': [18, 18, 18, 18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.post_validate(excel_file)
        
        assert result.invalid_row_count >= 1
        assert 1 in result.row_errors
        assert any('chronological' in err.lower() or 'order' in err.lower() for err in result.row_errors[1])
    
    @pytest.mark.asyncio
    async def test_validates_sugar_decreases_over_time_when_present(self, tmp_path):
        """Post-validation should ensure sugar_brix decreases for same fermentation."""
        excel_file = tmp_path / "sugar_increases.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-001', 'FERM-001'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500, 1500],
            'sample_date': ['2023-03-12', '2023-03-15', '2023-03-18'],
            'density': [1.090, 1.085, 1.080],
            'temperature_celsius': [18, 18, 18],
            'sugar_brix': [25, 30, 15]  # Row 1 sugar increases (invalid)
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.post_validate(excel_file)
        
        assert result.invalid_row_count >= 1
        assert 1 in result.row_errors
        assert any('sugar' in err.lower() for err in result.row_errors[1])
    
    @pytest.mark.asyncio
    async def test_accepts_valid_multi_fermentation_data(self, tmp_path):
        """Post-validation should accept valid data with multiple fermentations and samples."""
        excel_file = tmp_path / "valid_multi_fermentation.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-001', 'FERM-002', 'FERM-002', 'FERM-002'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-15', '2023-03-15', '2023-03-15'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-15', '2023-04-15', '2023-04-15'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-10', '2023-03-10', '2023-03-10'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Sur', 'Viña Sur', 'Viña Sur'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Merlot', 'Merlot', 'Merlot'],
            'harvest_mass_kg': [1500, 1500, 2000, 2000, 2000],
            'sample_date': ['2023-03-12', '2023-03-18', '2023-03-17', '2023-03-20', '2023-03-25'],
            'density': [1.090, 1.080, 1.095, 1.085, 1.075],
            'temperature_celsius': [18, 18, 19, 19, 19],
            'sugar_brix': [25, 15, 28, 20, 12]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.post_validate(excel_file)
        
        assert result.valid_row_count == 5
        assert result.invalid_row_count == 0
        assert len(result.row_errors) == 0
    
    @pytest.mark.asyncio
    async def test_handles_missing_optional_sugar_values(self, tmp_path):
        """Post-validation should not fail on missing sugar values (optional field)."""
        excel_file = tmp_path / "missing_sugar.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-001', 'FERM-001'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500, 1500],
            'sample_date': ['2023-03-12', '2023-03-15', '2023-03-18'],
            'density': [1.090, 1.085, 1.080],
            'temperature_celsius': [18, 18, 18]
            # No sugar_brix column
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.post_validate(excel_file)
        
        assert result.valid_row_count == 3
        assert result.invalid_row_count == 0
    
    @pytest.mark.asyncio
    async def test_validates_density_decreases_over_time(self, tmp_path):
        """Post-validation should ensure density decreases for same fermentation."""
        excel_file = tmp_path / "density_increases.xlsx"
        df = pd.DataFrame({
            'fermentation_code': ['FERM-001', 'FERM-001', 'FERM-001'],
            'fermentation_start_date': ['2023-03-10', '2023-03-10', '2023-03-10'],
            'fermentation_end_date': ['2023-04-10', '2023-04-10', '2023-04-10'],
            'harvest_date': ['2023-03-05', '2023-03-05', '2023-03-05'],
            'vineyard_name': ['Viña Norte', 'Viña Norte', 'Viña Norte'],
            'grape_variety': ['Cabernet', 'Cabernet', 'Cabernet'],
            'harvest_mass_kg': [1500, 1500, 1500],
            'sample_date': ['2023-03-12', '2023-03-15', '2023-03-18'],
            'density': [1.090, 1.095, 1.080],  # Row 1 density increases (invalid)
            'temperature_celsius': [18, 18, 18]
        })
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        validator = ETLValidator()
        result = await validator.post_validate(excel_file)
        
        assert result.invalid_row_count >= 1
        assert 1 in result.row_errors
        assert any('density' in err.lower() for err in result.row_errors[1])
