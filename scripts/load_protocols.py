"""
Protocol Seed Loader

Loads protocol JSON files into the database using repositories.
Handles 3 sample protocols: Pinot Noir, Chardonnay, Cabernet Sauvignon

Usage:
    python -m scripts.load_protocols [--db-url postgresql://user:pass@host/db]
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
from src.modules.fermentation.src.domain.enums.step_type import StepType
from src.modules.fermentation.src.repository_component.fermentation_protocol_repository import (
    FermentationProtocolRepository
)
from src.modules.fermentation.src.repository_component.protocol_step_repository import (
    ProtocolStepRepository
)


# Mapping of old specific step types to new category-based StepType enum
# (Feb 10, 2026: Refactored to use categories instead of specific step names)
STEP_TYPE_MAPPING: Dict[str, StepType] = {
    # INITIALIZATION steps
    "YEAST_INOCULATION": StepType.INITIALIZATION,
    "COLD_SOAK": StepType.INITIALIZATION,
    
    # MONITORING steps
    "TEMPERATURE_CHECK": StepType.MONITORING,
    "TEMPERATURE_ADJUSTMENT": StepType.MONITORING,
    "H2S_CHECK": StepType.MONITORING,
    "BRIX_READING": StepType.MONITORING,
    "PH_CHECK": StepType.MONITORING,
    
    # ADDITIONS steps
    "DAP_ADDITION": StepType.ADDITIONS,
    "NUTRIENT_ADDITION": StepType.ADDITIONS,
    "SO2_ADDITION": StepType.ADDITIONS,
    "SULFITE_ADDITION": StepType.ADDITIONS,
    "MLF_INOCULATION": StepType.ADDITIONS,
    
    # CAP_MANAGEMENT steps
    "PUNCH_DOWN": StepType.CAP_MANAGEMENT,
    "PUMP_OVER": StepType.CAP_MANAGEMENT,
    
    # POST_FERMENTATION steps
    "PRESSING": StepType.POST_FERMENTATION,
    "RACKING": StepType.POST_FERMENTATION,
    "RACK_TRANSFER": StepType.POST_FERMENTATION,
    "SETTLING": StepType.POST_FERMENTATION,
    "FILTRATION": StepType.POST_FERMENTATION,
    "CLARIFICATION": StepType.POST_FERMENTATION,
    "EXTENDED_MACERATION": StepType.POST_FERMENTATION,
    
    # QUALITY_CHECK steps
    "CATA_TASTING": StepType.QUALITY_CHECK,
    "FLAVOR_PROFILE_ASSESSMENT": StepType.QUALITY_CHECK,
    "VISUAL_INSPECTION": StepType.QUALITY_CHECK,
    "FINAL_ADJUSTMENT": StepType.QUALITY_CHECK,
}


class ProtocolLoader:
    """Loads protocol JSON files into database"""
    
    def __init__(
        self,
        db_url: str = "sqlite+aiosqlite:///:memory:",
        winery_id: int = 1,
        created_by: int = 1
    ):
        """
        Initialize protocol loader.
        
        Args:
            db_url: SQLAlchemy async database URL
            winery_id: ID of winery owning these protocols
            created_by: ID of user creating protocols
        """
        self.db_url = db_url
        self.winery_id = winery_id
        self.created_by = created_by
        self.engine = None
        self.async_session_factory = None
    
    async def connect(self):
        """Create async engine and session factory"""
        self.engine = create_async_engine(
            self.db_url,
            echo=False,
            future=True
        )
        self.async_session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def disconnect(self):
        """Close async engine"""
        if self.engine:
            await self.engine.dispose()
    
    async def load_protocol_from_file(self, file_path: Path) -> None:
        """
        Load a single protocol JSON file into database.
        
        Args:
            file_path: Path to JSON protocol file
        """
        with open(file_path, 'r') as f:
            protocol_data = json.load(f)
        
        async with self.async_session_factory() as session:
            await self._load_protocol(session, protocol_data, file_path.name)
    
    async def _load_protocol(
        self,
        session: AsyncSession,
        data: Dict[str, Any],
        source_file: str
    ) -> None:
        """
        Load protocol from parsed JSON data.
        
        Args:
            session: AsyncSession for database operations
            data: Parsed JSON protocol data
            source_file: Name of source file (for logging)
        """
        # Create protocol entity
        protocol = FermentationProtocol(
            winery_id=self.winery_id,
            varietal=data['varietal_name'],
            vintage_year=data['year'],
            version=1,
            created_by=self.created_by,
            created_at=datetime.utcnow(),
            is_active=True,
            description=data.get('description', '')
        )
        
        # Save protocol
        protocol_repo = FermentationProtocolRepository(session)
        saved_protocol = await protocol_repo.create(protocol)
        
        # Load steps
        step_repo = ProtocolStepRepository(session)
        for step_data in data['steps']:
            step = ProtocolStep(
                protocol_id=saved_protocol.id,
                step_order=step_data['step_order'],
                step_type=STEP_TYPE_MAPPING[step_data['step_type']],
                description=step_data['description'],
                target_min=None,
                target_max=None,
                target_value=None,
                unit=None,
                duration_hours=int(step_data['duration_minutes'] / 60) 
                    if step_data.get('duration_minutes') else None,
                is_critical=step_data.get('is_critical', False),
                can_skip=not step_data.get('is_critical', False),
                created_at=datetime.utcnow()
            )
            await step_repo.create(step)
        
        print(f"✅ Loaded {source_file}")
        print(f"   - Protocol: {data['varietal_name']} {data['year']}")
        print(f"   - Steps: {len(data['steps'])}")
        
        await session.commit()
    
    async def load_all_protocols(self) -> None:
        """Load all JSON protocol files from extracted_protocols directory"""
        protocol_dir = Path(__file__).parent.parent / "src" / "modules" / "fermentation" / "extracted_protocols"
        
        if not protocol_dir.exists():
            print(f"⚠️  Protocol directory not found: {protocol_dir}")
            return
        
        json_files = sorted(protocol_dir.glob("*.json"))
        
        if not json_files:
            print(f"⚠️  No JSON files found in {protocol_dir}")
            return
        
        print(f"📦 Loading {len(json_files)} protocols from {protocol_dir}")
        print()
        
        for file_path in json_files:
            try:
                await self.load_protocol_from_file(file_path)
            except Exception as e:
                print(f"❌ Failed to load {file_path.name}: {str(e)}")
        
        print()
        print("✅ Protocol loading complete!")


async def main():
    """Main entry point for protocol loading"""
    import sys
    
    # Parse command line arguments
    db_url = "sqlite+aiosqlite:///:memory:"
    
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--db-url" and i + 1 < len(sys.argv) - 1:
            db_url = sys.argv[i + 2]
    
    # Load protocols
    loader = ProtocolLoader(
        db_url=db_url,
        winery_id=1,
        created_by=1
    )
    
    try:
        await loader.connect()
        await loader.load_all_protocols()
    finally:
        await loader.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
