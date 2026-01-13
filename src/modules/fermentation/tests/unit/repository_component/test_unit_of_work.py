"""
Unit tests for UnitOfWork facade pattern.

Following TDD approach - tests written before implementation.

Test Coverage:
- Repository access (lazy loading)
- Session manager sharing
- All repository properties
- Facade pattern behavior

Note: Transaction management is tested in test_transaction_scope.py
since UnitOfWork is now a facade (ADR-031).
"""

import pytest
from unittest.mock import Mock

from src.modules.fermentation.src.repository_component.unit_of_work import UnitOfWork
from src.shared.infra.interfaces.session_manager import ISessionManager


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    manager = Mock(spec=ISessionManager)
    return manager


class TestUnitOfWorkRepositoryAccess:
    """Test repository access via UnitOfWork facade."""
    
    def test_fermentation_repo_accessible(self, mock_session_manager):
        """
        Given: A UnitOfWork instance
        When: Accessing fermentation_repo
        Then: Should return repository instance
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act
        repo = uow.fermentation_repo
        
        # Assert
        assert repo is not None
        assert hasattr(repo, 'create')
        assert hasattr(repo, 'get_by_id')
    
    def test_sample_repo_accessible(self, mock_session_manager):
        """
        Given: A UnitOfWork instance
        When: Accessing sample_repo
        Then: Should return repository instance
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act
        repo = uow.sample_repo
        
        # Assert
        assert repo is not None
        assert hasattr(repo, 'create')
    
    def test_lot_source_repo_accessible(self, mock_session_manager):
        """
        Given: A UnitOfWork instance
        When: Accessing lot_source_repo
        Then: Should return repository instance
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act
        repo = uow.lot_source_repo
        
        # Assert
        assert repo is not None
    
    def test_harvest_lot_repo_accessible(self, mock_session_manager):
        """
        Given: A UnitOfWork instance
        When: Accessing harvest_lot_repo
        Then: Should return repository instance
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act
        repo = uow.harvest_lot_repo
        
        # Assert
        assert repo is not None
    
    def test_vineyard_repo_accessible(self, mock_session_manager):
        """
        Given: A UnitOfWork instance
        When: Accessing vineyard_repo
        Then: Should return repository instance
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act
        repo = uow.vineyard_repo
        
        # Assert
        assert repo is not None
    
    def test_vineyard_block_repo_accessible(self, mock_session_manager):
        """
        Given: A UnitOfWork instance
        When: Accessing vineyard_block_repo
        Then: Should return repository instance
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act
        repo = uow.vineyard_block_repo
        
        # Assert
        assert repo is not None


class TestUnitOfWorkLazyLoading:
    """Test lazy initialization of repositories."""
    
    def test_repos_lazy_initialized(self, mock_session_manager):
        """
        Given: A newly created UnitOfWork
        When: Not accessing any repos
        Then: Repos should not be initialized
        """
        # Arrange & Act
        uow = UnitOfWork(mock_session_manager)
        
        # Assert
        assert uow._fermentation_repo is None
        assert uow._sample_repo is None
        assert uow._lot_source_repo is None
    
    def test_fermentation_repo_initialized_on_first_access(self, mock_session_manager):
        """
        Given: A UnitOfWork with no fermentation_repo
        When: Accessing fermentation_repo first time
        Then: Should initialize and cache repository
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        assert uow._fermentation_repo is None
        
        # Act
        repo1 = uow.fermentation_repo
        repo2 = uow.fermentation_repo
        
        # Assert
        assert repo1 is repo2  # Same instance (cached)
        assert uow._fermentation_repo is not None
    
    def test_sample_repo_initialized_on_first_access(self, mock_session_manager):
        """
        Given: A UnitOfWork with no sample_repo
        When: Accessing sample_repo first time
        Then: Should initialize and cache repository
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        assert uow._sample_repo is None
        
        # Act
        repo1 = uow.sample_repo
        repo2 = uow.sample_repo
        
        # Assert
        assert repo1 is repo2  # Same instance (cached)
        assert uow._sample_repo is not None
    
    def test_repos_initialized_independently(self, mock_session_manager):
        """
        Given: A UnitOfWork
        When: Accessing one repo
        Then: Other repos should remain uninitialized
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act
        _ = uow.fermentation_repo
        
        # Assert
        assert uow._fermentation_repo is not None
        assert uow._sample_repo is None  # Still None
        assert uow._lot_source_repo is None  # Still None


class TestUnitOfWorkSessionSharing:
    """Test that all repositories share the same session manager."""
    
    def test_all_repos_use_same_session_manager(self, mock_session_manager):
        """
        Given: A UnitOfWork with session manager
        When: Accessing multiple repos
        Then: All should receive same session manager instance
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act
        ferm_repo = uow.fermentation_repo
        sample_repo = uow.sample_repo
        lot_repo = uow.lot_source_repo
        
        # Assert - all repos were created
        assert ferm_repo is not None
        assert sample_repo is not None
        assert lot_repo is not None
        
        # Verify they all have the session manager (checking public attribute)
        assert ferm_repo.session_manager is mock_session_manager
        assert sample_repo.session_manager is mock_session_manager
        assert lot_repo.session_manager is mock_session_manager


class TestUnitOfWorkFacadePattern:
    """Test UnitOfWork as a facade for repository access."""
    
    def test_uow_provides_unified_interface(self, mock_session_manager):
        """
        Given: A UnitOfWork
        When: Using UnitOfWork
        Then: Should provide single access point to all repositories
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act & Assert - all repos accessible from one object
        assert hasattr(uow, 'fermentation_repo')
        assert hasattr(uow, 'sample_repo')
        assert hasattr(uow, 'lot_source_repo')
        assert hasattr(uow, 'harvest_lot_repo')
        assert hasattr(uow, 'vineyard_repo')
        assert hasattr(uow, 'vineyard_block_repo')
    
    def test_uow_implements_interface(self, mock_session_manager):
        """
        Given: A UnitOfWork
        When: Checking interface compliance
        Then: Should implement IUnitOfWork
        """
        # Arrange
        from src.modules.fermentation.src.domain.interfaces.unit_of_work_interface import IUnitOfWork
        
        # Act
        uow = UnitOfWork(mock_session_manager)
        
        # Assert
        assert isinstance(uow, IUnitOfWork)
    
    def test_uow_initialization_with_session_manager(self, mock_session_manager):
        """
        Given: A session manager
        When: Creating UnitOfWork
        Then: Should store session manager for repository creation
        """
        # Act
        uow = UnitOfWork(mock_session_manager)
        
        # Assert
        assert uow._session_manager is mock_session_manager


class TestUnitOfWorkCrossModuleSupport:
    """Test UnitOfWork provides repositories from multiple modules."""
    
    def test_fermentation_module_repos_available(self, mock_session_manager):
        """
        Given: A UnitOfWork
        When: Accessing fermentation module repos
        Then: Should provide fermentation, sample, lot_source repos
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act
        ferm_repo = uow.fermentation_repo
        sample_repo = uow.sample_repo
        lot_repo = uow.lot_source_repo
        
        # Assert
        assert ferm_repo is not None
        assert sample_repo is not None
        assert lot_repo is not None
    
    def test_fruit_origin_module_repos_available(self, mock_session_manager):
        """
        Given: A UnitOfWork
        When: Accessing fruit_origin module repos
        Then: Should provide harvest_lot, vineyard, vineyard_block repos
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act
        harvest_repo = uow.harvest_lot_repo
        vineyard_repo = uow.vineyard_repo
        block_repo = uow.vineyard_block_repo
        
        # Assert
        assert harvest_repo is not None
        assert vineyard_repo is not None
        assert block_repo is not None
    
    def test_cross_module_session_sharing(self, mock_session_manager):
        """
        Given: A UnitOfWork
        When: Accessing repos from different modules
        Then: All should share same session manager (enables cross-module transactions)
        """
        # Arrange
        uow = UnitOfWork(mock_session_manager)
        
        # Act
        ferm_repo = uow.fermentation_repo  # fermentation module
        vineyard_repo = uow.vineyard_repo  # fruit_origin module
        
        # Assert - both use same session manager
        assert ferm_repo.session_manager is mock_session_manager
        assert vineyard_repo.session_manager is mock_session_manager
