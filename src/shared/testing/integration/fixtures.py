"""
Repository fixture factory for integration tests.

Eliminates repetitive repository fixture code across test files.
"""

import pytest_asyncio
from typing import Type, TypeVar, Callable, Any, Dict, Optional
from .session_manager import TestSessionManager


T = TypeVar('T')


def create_repository_fixture(
    repository_class: Type[T],
    additional_deps: Optional[Dict[str, Any]] = None
) -> Callable:
    """
    Create a repository fixture dynamically.
    
    This factory eliminates the need to manually create repository fixtures
    in every test file. Instead of writing 15-20 lines of fixture code,
    you can create a repository fixture with a single function call.
    
    Args:
        repository_class: Repository class to instantiate
        additional_deps: Additional dependencies beyond session_manager
    
    Returns:
        Pytest async fixture function
    
    Example:
        # In conftest.py
        from mymodule.repositories import MyRepository
        from shared.testing.integration.fixtures import create_repository_fixture
        
        my_repository = create_repository_fixture(MyRepository)
        
        # Now 'my_repository' fixture is available in all test files
    
    Before (manual fixture - 15 lines):
        @pytest_asyncio.fixture
        async def my_repository(db_session):
            class TestSessionManager:
                def __init__(self, session):
                    self._session = session
                
                @asynccontextmanager
                async def get_session(self):
                    yield self._session
                
                async def close(self):
                    pass
            
            session_manager = TestSessionManager(db_session)
            return MyRepository(session_manager)
    
    After (using factory - 1 line):
        my_repository = create_repository_fixture(MyRepository)
    """
    
    @pytest_asyncio.fixture
    async def repository_fixture(db_session):
        """
        Dynamically created repository fixture.
        
        Wraps db_session with TestSessionManager and instantiates repository.
        """
        session_manager = TestSessionManager(db_session)
        
        if additional_deps:
            return repository_class(session_manager, **additional_deps)
        else:
            return repository_class(session_manager)
    
    # Set fixture name based on repository class
    # e.g., FermentationRepository -> fermentation_repository
    fixture_name = repository_class.__name__
    if fixture_name.endswith('Repository'):
        fixture_name = fixture_name[:-10]  # Remove 'Repository' suffix
    fixture_name = ''.join(['_' + c.lower() if c.isupper() else c for c in fixture_name]).lstrip('_')
    fixture_name = f"{fixture_name}_repository"
    
    repository_fixture.__name__ = fixture_name
    
    return repository_fixture
