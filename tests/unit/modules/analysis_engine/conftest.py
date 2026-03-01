"""Pytest configuration for analysis engine tests."""
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

# Add paths for imports
# This test is at: tests/unit/modules/analysis_engine/conftest.py
# Path hierarchy: conftest.py -> analysis_engine/ -> modules/ -> unit/ -> tests/ -> project_root/
# We add:
#   - project_root/src so 'shared.*' imports work
#   - project_root so 'src.modules.*' imports work
project_root = Path(__file__).parent.parent.parent.parent.parent
src_path = project_root / "src"
for p in [str(src_path), str(project_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Pre-import ALL fermentation entities so SQLAlchemy mapper cascade can resolve
# string references when the shared Base configures all mappers at once.
try:
    import src.modules.fermentation.src.domain.entities.fermentation_note  # noqa: F401
    import src.modules.fermentation.src.domain.entities.fermentation_lot_source  # noqa: F401
    import src.modules.fermentation.src.domain.entities.step_completion  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_step  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_protocol  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_execution  # noqa: F401
    import src.modules.fermentation.src.domain.entities.fermentation  # noqa: F401
except Exception:
    pass


@pytest.fixture
def session() -> AsyncMock:
    """
    Provide a mock AsyncSession for unit tests.

    Analysis Engine entities use PostgreSQL-specific types (JSONB, UUID) that
    are not supported by SQLite, so real DB sessions cannot be used in unit tests.
    Service tests only need the session as a constructor dependency; they do not
    execute actual DB queries (or use the mock's default return values).
    """
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.rollback = AsyncMock()

    # Configure execute() so that result.scalars().all() returns an empty list
    # by default — tests that need specific results configure it themselves.
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = []
    scalars_mock.first.return_value = None
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    execute_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=execute_result)

    return mock_session
