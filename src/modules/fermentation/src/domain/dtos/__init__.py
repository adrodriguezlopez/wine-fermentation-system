"""
Domain Data Transfer Objects.

DTOs are simple data structures used to transfer data between layers.
These are framework-agnostic (no Pydantic, no ORM) - pure Python dataclasses.
"""

from .fermentation_dtos import (
    FermentationCreate,
    FermentationUpdate,
    FermentationWithBlendCreate,
    LotSourceData
)
from .sample_dtos import SampleCreate
from .fermentation_note_dtos import FermentationNoteCreate, FermentationNoteUpdate
from .protocol_dtos import (
    ProtocolCreate,
    ProtocolUpdate,
    ProtocolResponse,
    StepCreate,
    StepUpdate,
    StepResponse,
    ExecutionStart,
    ExecutionResponse,
    CompletionCreate,
    CompletionResponse,
    ProtocolListResponse,
    ExecutionListResponse,
    ExecutionDetailResponse,
    StepTypeDTO,
    ProtocolExecutionStatusDTO,
    SkipReasonDTO,
)

__all__ = [
    "FermentationCreate",
    "FermentationUpdate",
    "FermentationWithBlendCreate",
    "LotSourceData",
    "SampleCreate",
    "FermentationNoteCreate",
    "FermentationNoteUpdate",
    "ProtocolCreate",
    "ProtocolUpdate",
    "ProtocolResponse",
    "StepCreate",
    "StepUpdate",
    "StepResponse",
    "ExecutionStart",
    "ExecutionResponse",
    "CompletionCreate",
    "CompletionResponse",
    "ProtocolListResponse",
    "ExecutionListResponse",
    "ExecutionDetailResponse",
    "StepTypeDTO",
    "ProtocolExecutionStatusDTO",
    "SkipReasonDTO",
]
