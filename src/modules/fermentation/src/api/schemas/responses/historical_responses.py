"""
Response DTOs for Historical Data API endpoints.

Following Pydantic v2 patterns for response serialization.
Related ADR: ADR-032 (Historical Data API Layer)
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample


class HistoricalSampleResponse(BaseModel):
    """Response DTO for a historical sample."""
    
    id: int = Field(..., description="Sample ID")
    fermentation_id: int = Field(..., description="Fermentation ID")
    sample_type: str = Field(..., description="Type of sample (density, sugar, temperature, etc.)")
    recorded_at: datetime = Field(..., description="When sample was recorded")
    data_source: str = Field(..., description="Data source (should be 'HISTORICAL')")
    
    # Conditional fields based on sample type
    density: Optional[float] = Field(None, description="Density value (for density samples)")
    sugar_brix: Optional[float] = Field(None, description="Sugar in °Brix (for sugar samples)")
    temperature_celsius: Optional[float] = Field(None, description="Temperature in Celsius (for temperature samples)")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_entity(cls, entity: BaseSample) -> "HistoricalSampleResponse":
        """Create response DTO from domain entity."""
        # Base fields
        data = {
            "id": entity.id,
            "fermentation_id": entity.fermentation_id,
            "sample_type": entity.sample_type.value if hasattr(entity.sample_type, 'value') else str(entity.sample_type),
            "recorded_at": entity.recorded_at,
            "data_source": getattr(entity, 'data_source', 'HISTORICAL')
        }
        
        # Add type-specific fields
        if hasattr(entity, 'density') and entity.density is not None:
            data["density"] = entity.density
        if hasattr(entity, 'sugar_brix') and entity.sugar_brix is not None:
            data["sugar_brix"] = entity.sugar_brix
        if hasattr(entity, 'temperature_celsius') and entity.temperature_celsius is not None:
            data["temperature_celsius"] = entity.temperature_celsius
        
        return cls(**data)


class HistoricalFermentationResponse(BaseModel):
    """Response DTO for a historical fermentation."""
    
    id: int = Field(..., description="Fermentation ID")
    winery_id: int = Field(..., description="Winery ID")
    vintage_year: int = Field(..., description="Vintage year")
    yeast_strain: Optional[str] = Field(None, description="Yeast strain used")
    input_mass_kg: Optional[float] = Field(None, description="Input mass in kg")
    initial_sugar_brix: Optional[float] = Field(None, description="Initial sugar in °Brix")
    initial_density: Optional[float] = Field(None, description="Initial density")
    vessel_code: Optional[str] = Field(None, description="Vessel code")
    start_date: datetime = Field(..., description="Fermentation start date")
    status: str = Field(..., description="Fermentation status")
    data_source: str = Field(..., description="Data source (should be 'HISTORICAL')")
    fruit_origin_id: Optional[int] = Field(None, description="Fruit origin ID")
    created_at: datetime = Field(..., description="Record creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_entity(cls, entity: Fermentation) -> "HistoricalFermentationResponse":
        """Create response DTO from domain entity."""
        return cls(
            id=entity.id,
            winery_id=entity.winery_id,
            vintage_year=entity.vintage_year,
            yeast_strain=entity.yeast_strain,
            input_mass_kg=entity.input_mass_kg,
            initial_sugar_brix=entity.initial_sugar_brix,
            initial_density=entity.initial_density,
            vessel_code=entity.vessel_code,
            start_date=entity.start_date,
            status=entity.status.value if hasattr(entity.status, 'value') else str(entity.status),
            data_source=getattr(entity, 'data_source', 'HISTORICAL'),
            fruit_origin_id=getattr(entity, 'fruit_origin_id', None),
            created_at=entity.created_at
        )


class PaginatedHistoricalFermentationsResponse(BaseModel):
    """Response DTO for paginated list of historical fermentations."""
    
    items: List[HistoricalFermentationResponse] = Field(..., description="List of historical fermentations")
    total: int = Field(..., description="Total count of fermentations")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset for pagination")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "id": 1,
                            "winery_id": 1,
                            "vintage_year": 2024,
                            "yeast_strain": "EC-1118",
                            "input_mass_kg": 1000.0,
                            "initial_sugar_brix": 24.5,
                            "initial_density": 1.105,
                            "vessel_code": "T-001",
                            "start_date": "2024-01-01T08:00:00",
                            "end_date": "2024-01-15T10:00:00",
                            "status": "completed",
                            "data_source": "HISTORICAL",
                            "fruit_origin_id": 5,
                            "created_at": "2024-12-01T00:00:00"
                        }
                    ],
                    "total": 1,
                    "limit": 100,
                    "offset": 0
                }
            ]
        }
    }


class PatternResponse(BaseModel):
    """Response DTO for aggregated patterns from historical data.
    
    Designed for consumption by Analysis Engine (ADR-020).
    """
    
    total_fermentations: int = Field(..., description="Total fermentations analyzed")
    avg_initial_density: Optional[float] = Field(None, description="Average initial density")
    avg_final_density: Optional[float] = Field(None, description="Average final density")
    avg_initial_sugar_brix: Optional[float] = Field(None, description="Average initial sugar (°Brix)")
    avg_final_sugar_brix: Optional[float] = Field(None, description="Average final sugar (°Brix)")
    avg_duration_days: Optional[float] = Field(None, description="Average fermentation duration in days")
    success_rate: float = Field(..., description="Success rate (0.0-1.0)")
    completed_count: int = Field(..., description="Number of completed fermentations")
    stuck_count: int = Field(..., description="Number of stuck fermentations")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_fermentations": 100,
                    "avg_initial_density": 1.102,
                    "avg_final_density": 0.993,
                    "avg_initial_sugar_brix": 24.3,
                    "avg_final_sugar_brix": 0.4,
                    "avg_duration_days": 14.5,
                    "success_rate": 0.95,
                    "completed_count": 95,
                    "stuck_count": 5
                }
            ]
        }
    }


class StatisticsResponse(BaseModel):
    """Response DTO for dashboard statistics from historical data."""
    
    total_fermentations: int = Field(..., description="Total historical fermentations")
    avg_duration_days: Optional[float] = Field(None, description="Average duration in days")
    success_rate: float = Field(..., description="Success rate (0.0-1.0)")
    total_volume_liters: Optional[float] = Field(None, description="Total volume processed (liters)")
    most_common_yeast: Optional[str] = Field(None, description="Most commonly used yeast strain")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_fermentations": 500,
                    "avg_duration_days": 15.2,
                    "success_rate": 0.92,
                    "total_volume_liters": 50000.0,
                    "most_common_yeast": "EC-1118"
                }
            ]
        }
    }


class ImportJobResponse(BaseModel):
    """Response DTO for an ETL import job."""
    
    id: int = Field(..., description="Import job ID")
    status: str = Field(..., description="Job status (pending, running, completed, failed)")
    progress: float = Field(..., description="Job progress (0.0-1.0)")
    total_fermentations: int = Field(..., description="Total fermentations to import")
    imported_count: int = Field(..., description="Number of fermentations imported")
    failed_count: int = Field(..., description="Number of fermentations that failed")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "status": "completed",
                    "progress": 1.0,
                    "total_fermentations": 100,
                    "imported_count": 98,
                    "failed_count": 2,
                    "errors": ["Row 50: Invalid date format", "Row 75: Missing required field"],
                    "started_at": "2024-01-01T10:00:00",
                    "completed_at": "2024-01-01T10:05:00"
                }
            ]
        }
    }


class ImportTriggerResponse(BaseModel):
    """Response DTO when triggering a new import job."""
    
    job_id: int = Field(..., description="ID of the triggered import job")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Human-readable message")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": 42,
                    "status": "pending",
                    "message": "Import job queued successfully"
                }
            ]
        }
    }
