"""
DataSource enum for tracking data origin (ADR-029)

This enum identifies the source of data in the system:
- SYSTEM: Created through normal API operations
- IMPORTED: Imported from historical Excel files
- MIGRATED: Migrated from legacy systems (future use)
"""
from enum import Enum


class DataSource(str, Enum):
    """
    Data source tracking enum (ADR-029).
    
    Values:
        SYSTEM: Data created through API operations
        IMPORTED: Data imported from Excel files
        MIGRATED: Data migrated from legacy systems
    """
    SYSTEM = "system"
    IMPORTED = "imported"
    MIGRATED = "migrated"
