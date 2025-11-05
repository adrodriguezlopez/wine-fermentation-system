"""
Integration tests for multi-tenancy and role-based access control.

Tests that verify data isolation between wineries and proper
role-based authorization enforcement.
"""

import pytest

from src.shared.auth.domain.dtos import UserCreate, LoginRequest
from src.shared.auth.domain.enums import UserRole
from src.shared.auth.infra.services import AuthService


@pytest.mark.asyncio
class TestMultiTenancy:
    """Test multi-tenancy data isolation."""

    async def test_users_belong_to_correct_winery(
        self, auth_service: AuthService, sample_winery_id: int, another_winery_id: int
    ):
        """Test that users are correctly associated with their winery."""
        # Arrange - Create users in different wineries
        user1_create = UserCreate(
            username="winery1user",
            email="user1@winery1.com",
            password="Password123",
            full_name="Winery 1 User",
            winery_id=sample_winery_id,
            role=UserRole.WINEMAKER,
        )
        user1 = await auth_service.register_user(user1_create)

        user2_create = UserCreate(
            username="winery2user",
            email="user2@winery2.com",
            password="Password123",
            full_name="Winery 2 User",
            winery_id=another_winery_id,
            role=UserRole.WINEMAKER,
        )
        user2 = await auth_service.register_user(user2_create)

        # Act - Verify winery associations
        retrieved_user1 = await auth_service.get_user(user1.id)
        retrieved_user2 = await auth_service.get_user(user2.id)

        # Assert
        assert retrieved_user1.winery_id == sample_winery_id
        assert retrieved_user2.winery_id == another_winery_id
        assert retrieved_user1.winery_id != retrieved_user2.winery_id

    async def test_login_includes_winery_context(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test that login token includes winery context."""
        # Arrange - Create and activate user
        user_create = UserCreate(
            username="contextuser",
            email="context@winery.com",
            password="Password123",
            full_name="Context User",
            winery_id=sample_winery_id,
            role=UserRole.WINEMAKER,
        )
        registered_user = await auth_service.register_user(user_create)
        
        from src.shared.auth.domain.dtos import UserUpdate
        await auth_service.update_user(
            registered_user.id,
            UserUpdate(is_active=True, is_verified=True)
        )

        # Act - Login and extract user context
        login_request = LoginRequest(
            email="context@winery.com",
            password="Password123",
        )
        login_response = await auth_service.login(login_request)
        user_context = await auth_service.verify_token(login_response.access_token)

        # Assert - Token contains winery information
        assert user_context.winery_id == sample_winery_id
        assert user_context.user_id == registered_user.id

    async def test_multiple_users_same_winery(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test multiple users can belong to same winery."""
        # Arrange & Act - Create multiple users in same winery
        users = []
        for i in range(3):
            user_create = UserCreate(
                username=f"user{i}",
                email=f"user{i}@samewinery.com",
                password="Password123",
                full_name=f"User {i}",
                winery_id=sample_winery_id,
                role=UserRole.OPERATOR if i == 0 else UserRole.VIEWER,
            )
            user = await auth_service.register_user(user_create)
            users.append(user)

        # Assert - All users belong to same winery but different roles
        assert all(u.winery_id == sample_winery_id for u in users)
        assert users[0].role == UserRole.OPERATOR
        assert users[1].role == UserRole.VIEWER
        assert users[2].role == UserRole.VIEWER


@pytest.mark.asyncio
class TestRoleBasedAccessControl:
    """Test role-based access control scenarios."""

    async def test_admin_role_assignment(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test creating user with ADMIN role."""
        # Arrange & Act
        admin_create = UserCreate(
            username="admin",
            email="admin@winery.com",
            password="AdminPass123",
            full_name="Admin User",
            winery_id=sample_winery_id,
            role=UserRole.ADMIN,
        )
        admin_user = await auth_service.register_user(admin_create)

        # Assert
        assert admin_user.role == UserRole.ADMIN
        
        # Verify through login token
        from src.shared.auth.domain.dtos import UserUpdate
        await auth_service.update_user(
            admin_user.id,
            UserUpdate(is_active=True, is_verified=True)
        )
        
        login_request = LoginRequest(
            email="admin@winery.com",
            password="AdminPass123",
        )
        login_response = await auth_service.login(login_request)
        user_context = await auth_service.verify_token(login_response.access_token)
        
        assert user_context.role == UserRole.ADMIN

    async def test_winemaker_role_assignment(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test creating user with WINEMAKER role."""
        # Arrange & Act
        winemaker_create = UserCreate(
            username="winemaker",
            email="winemaker@winery.com",
            password="WinemakerPass123",
            full_name="Winemaker User",
            winery_id=sample_winery_id,
            role=UserRole.WINEMAKER,
        )
        winemaker = await auth_service.register_user(winemaker_create)

        # Assert
        assert winemaker.role == UserRole.WINEMAKER

    async def test_operator_role_assignment(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test creating user with OPERATOR role."""
        # Arrange & Act
        operator_create = UserCreate(
            username="operator",
            email="operator@winery.com",
            password="OperatorPass123",
            full_name="Operator User",
            winery_id=sample_winery_id,
            role=UserRole.OPERATOR,
        )
        operator = await auth_service.register_user(operator_create)

        # Assert
        assert operator.role == UserRole.OPERATOR

    async def test_viewer_role_default(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test that VIEWER is default role when not specified."""
        # Arrange & Act - Create user without specifying role
        viewer_create = UserCreate(
            username="viewer",
            email="viewer@winery.com",
            password="ViewerPass123",
            full_name="Viewer User",
            winery_id=sample_winery_id,
            # role not specified, should default to VIEWER
        )
        viewer = await auth_service.register_user(viewer_create)

        # Assert
        assert viewer.role == UserRole.VIEWER

    async def test_role_update(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test updating user role."""
        # Arrange - Create user with VIEWER role
        user_create = UserCreate(
            username="upgradeuser",
            email="upgrade@winery.com",
            password="Password123",
            full_name="Upgrade User",
            winery_id=sample_winery_id,
            role=UserRole.VIEWER,
        )
        user = await auth_service.register_user(user_create)
        assert user.role == UserRole.VIEWER

        # Act - Upgrade to WINEMAKER
        from src.shared.auth.domain.dtos import UserUpdate
        updated_user = await auth_service.update_user(
            user.id,
            UserUpdate(role=UserRole.WINEMAKER)
        )

        # Assert
        assert updated_user.role == UserRole.WINEMAKER
        
        # Verify persistence
        retrieved_user = await auth_service.get_user(user.id)
        assert retrieved_user.role == UserRole.WINEMAKER

    async def test_token_contains_role_information(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test that JWT tokens include role information."""
        # Arrange - Create users with different roles
        roles_to_test = [UserRole.ADMIN, UserRole.WINEMAKER, UserRole.OPERATOR, UserRole.VIEWER]
        
        for idx, role in enumerate(roles_to_test):
            user_create = UserCreate(
                username=f"roletest{idx}",
                email=f"roletest{idx}@winery.com",
                password="Password123",
                full_name=f"Role Test {idx}",
                winery_id=sample_winery_id,
                role=role,
            )
            user = await auth_service.register_user(user_create)
            
            # Activate user
            from src.shared.auth.domain.dtos import UserUpdate
            await auth_service.update_user(
                user.id,
                UserUpdate(is_active=True, is_verified=True)
            )
            
            # Act - Login and verify token
            login_request = LoginRequest(
                email=f"roletest{idx}@winery.com",
                password="Password123",
            )
            login_response = await auth_service.login(login_request)
            user_context = await auth_service.verify_token(login_response.access_token)
            
            # Assert - Token contains correct role
            assert user_context.role == role


@pytest.mark.asyncio
class TestUserIsolation:
    """Test user data isolation and security."""

    async def test_users_in_different_wineries_isolated(
        self, auth_service: AuthService, sample_winery_id: int, another_winery_id: int
    ):
        """Test that users in different wineries are properly isolated."""
        # Arrange - Create users in two different wineries
        winery1_user = UserCreate(
            username="isolated1",
            email="isolated1@winery1.com",
            password="Password123",
            full_name="Isolated User 1",
            winery_id=sample_winery_id,
        )
        user1 = await auth_service.register_user(winery1_user)

        winery2_user = UserCreate(
            username="isolated2",
            email="isolated2@winery2.com",
            password="Password123",
            full_name="Isolated User 2",
            winery_id=another_winery_id,
        )
        user2 = await auth_service.register_user(winery2_user)

        # Act - Login both users and check contexts
        from src.shared.auth.domain.dtos import UserUpdate
        await auth_service.update_user(user1.id, UserUpdate(is_active=True, is_verified=True))
        await auth_service.update_user(user2.id, UserUpdate(is_active=True, is_verified=True))

        login1 = LoginRequest(email="isolated1@winery1.com", password="Password123")
        login2 = LoginRequest(email="isolated2@winery2.com", password="Password123")
        
        response1 = await auth_service.login(login1)
        response2 = await auth_service.login(login2)
        
        context1 = await auth_service.verify_token(response1.access_token)
        context2 = await auth_service.verify_token(response2.access_token)

        # Assert - Each user only sees their own winery
        assert context1.winery_id == sample_winery_id
        assert context2.winery_id == another_winery_id
        assert context1.user_id != context2.user_id
        assert context1.email != context2.email

    async def test_email_uniqueness_across_wineries(
        self, auth_service: AuthService, sample_winery_id: int, another_winery_id: int
    ):
        """Test that email must be unique across all wineries."""
        # Arrange - Create user in first winery
        user1_create = UserCreate(
            username="user1",
            email="unique@email.com",
            password="Password123",
            full_name="User 1",
            winery_id=sample_winery_id,
        )
        await auth_service.register_user(user1_create)

        # Act & Assert - Try to create user with same email in different winery
        user2_create = UserCreate(
            username="user2",
            email="unique@email.com",  # Same email
            password="Password123",
            full_name="User 2",
            winery_id=another_winery_id,  # Different winery
        )
        
        from src.shared.auth.domain.errors import UserAlreadyExistsError
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await auth_service.register_user(user2_create)
        
        assert exc_info.value.field == "email"

    async def test_username_uniqueness_across_wineries(
        self, auth_service: AuthService, sample_winery_id: int, another_winery_id: int
    ):
        """Test that username must be unique across all wineries."""
        # Arrange - Create user in first winery
        user1_create = UserCreate(
            username="uniqueusername",
            email="email1@winery1.com",
            password="Password123",
            full_name="User 1",
            winery_id=sample_winery_id,
        )
        await auth_service.register_user(user1_create)

        # Act & Assert - Try to create user with same username in different winery
        user2_create = UserCreate(
            username="uniqueusername",  # Same username
            email="email2@winery2.com",
            password="Password123",
            full_name="User 2",
            winery_id=another_winery_id,  # Different winery
        )
        
        from src.shared.auth.domain.errors import UserAlreadyExistsError
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await auth_service.register_user(user2_create)
        
        assert exc_info.value.field == "username"
