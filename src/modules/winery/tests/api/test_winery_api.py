"""
API tests for Winery endpoints (Admin namespace).

Following TDD approach - tests written FIRST.

Tests the 6 winery REST API endpoints:
1. POST /api/v1/admin/wineries - Create winery (ADMIN only)
2. GET /api/v1/admin/wineries/{id} - Get winery by ID
3. GET /api/v1/admin/wineries/code/{code} - Get winery by code
4. GET /api/v1/admin/wineries - List wineries (ADMIN only)
5. PATCH /api/v1/admin/wineries/{id} - Update winery
6. DELETE /api/v1/admin/wineries/{id} - Soft delete winery (ADMIN only)

Authorization:
- CREATE/DELETE/LIST: ADMIN only
- GET/UPDATE: Users can access own winery, ADMIN can access all
"""
import pytest
import pytest_asyncio
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text

from src.modules.winery.src.domain.entities.winery import Winery


# =============================================================================
# Helper Functions
# =============================================================================

async def create_test_winery(session, winery_id: int = 1, code: str = "TEST-WINERY-001"):
    """Helper: Create a test winery in the database."""
    query = text("""
        INSERT INTO wineries (id, code, name, location, notes, is_deleted, created_at, updated_at)
        VALUES (:id, :code, :name, :location, :notes, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING
    """)
    
    await session.execute(query, {
        "id": winery_id,
        "code": code,
        "name": f"Test Winery {winery_id}",
        "location": "Test Location",
        "notes": "Test notes"
    })
    await session.commit()


async def create_admin_user(session, user_id: int = 1, winery_id: int = 1):
    """Helper: Create an admin user."""
    query = text("""
        INSERT INTO users (id, username, email, full_name, password_hash, role, winery_id, is_active, is_verified, created_at, updated_at)
        VALUES (:id, :username, :email, :full_name, :password_hash, :role, :winery_id, true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING
    """)
    
    await session.execute(query, {
        "id": user_id,
        "username": f"admin{user_id}",
        "email": f"admin{user_id}@test.com",
        "full_name": f"Admin User {user_id}",
        "password_hash": "hashed_password",
        "role": "ADMIN",
        "winery_id": winery_id
    })
    await session.commit()


async def create_winemaker_user(session, user_id: int = 2, winery_id: int = 1):
    """Helper: Create a winemaker user."""
    query = text("""
        INSERT INTO users (id, username, email, full_name, password_hash, role, winery_id, is_active, is_verified, created_at, updated_at)
        VALUES (:id, :username, :email, :full_name, :password_hash, :role, :winery_id, true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING
    """)
    
    await session.execute(query, {
        "id": user_id,
        "username": f"winemaker{user_id}",
        "email": f"winemaker{user_id}@test.com",
        "full_name": f"Winemaker User {user_id}",
        "password_hash": "hashed_password",
        "role": "WINEMAKER",
        "winery_id": winery_id
    })
    await session.commit()


def get_admin_headers():
    """Helper: Get authentication headers for admin user."""
    # Mock JWT token for admin (winery_id=1, role=ADMIN)
    return {"Authorization": "Bearer admin_token"}


def get_winemaker_headers():
    """Helper: Get authentication headers for winemaker user."""
    # Mock JWT token for winemaker (winery_id=1, role=WINEMAKER)
    return {"Authorization": "Bearer winemaker_token"}


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def setup_test_data(db_session):
    """Create test wineries and users."""
    await create_test_winery(db_session, winery_id=1, code="WINERY-001")
    await create_test_winery(db_session, winery_id=2, code="WINERY-002")
    await create_admin_user(db_session, user_id=1, winery_id=1)
    await create_winemaker_user(db_session, user_id=2, winery_id=1)
    yield
    # Cleanup handled by db_session fixture


# =============================================================================
# POST /admin/wineries - Create Winery (ADMIN only)
# =============================================================================

@pytest.mark.asyncio
async def test_create_winery_success(client: TestClient, db_session):
    """Test successful winery creation (ADMIN)."""
    # Arrange
    await create_admin_user(db_session, user_id=1, winery_id=1)
    
    request_data = {
        "code": "NEW-WINERY-001",
        "name": "New Winery Name",
        "location": "California",
        "notes": "Test notes"
    }
    
    # Act
    response = client.post(
        "/api/v1/admin/wineries",
        json=request_data,
        headers=get_admin_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["code"] == "NEW-WINERY-001"
    assert data["name"] == "New Winery Name"
    assert data["location"] == "California"
    assert data["notes"] == "Test notes"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_winery_duplicate_code(client: TestClient, db_session, setup_test_data):
    """Test create winery with duplicate code returns 409."""
    # Arrange
    request_data = {
        "code": "WINERY-001",  # Already exists
        "name": "Duplicate Winery",
        "location": "California"
    }
    
    # Act
    response = client.post(
        "/api/v1/admin/wineries",
        json=request_data,
        headers=get_admin_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "code" in response.json()["detail"].lower() or "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_winery_duplicate_name(client: TestClient, db_session, setup_test_data):
    """Test create winery with duplicate name returns 409."""
    # Arrange
    request_data = {
        "code": "UNIQUE-CODE-001",
        "name": "Test Winery 1",  # Already exists (from winery_id=1)
        "location": "California"
    }
    
    # Act
    response = client.post(
        "/api/v1/admin/wineries",
        json=request_data,
        headers=get_admin_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "name" in response.json()["detail"].lower() or "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_winery_invalid_code_format(client: TestClient, db_session):
    """Test create winery with invalid code format returns 400."""
    # Arrange
    await create_admin_user(db_session, user_id=1, winery_id=1)
    
    request_data = {
        "code": "invalid code with spaces",  # Invalid format
        "name": "Test Winery",
        "location": "California"
    }
    
    # Act
    response = client.post(
        "/api/v1/admin/wineries",
        json=request_data,
        headers=get_admin_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_winery_missing_required_fields(client: TestClient, db_session):
    """Test create winery without required fields returns 422."""
    # Arrange
    await create_admin_user(db_session, user_id=1, winery_id=1)
    
    request_data = {
        "location": "California"  # Missing code and name
    }
    
    # Act
    response = client.post(
        "/api/v1/admin/wineries",
        json=request_data,
        headers=get_admin_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_winery_forbidden_for_winemaker(winemaker_client: TestClient, db_session):
    """Test create winery forbidden for WINEMAKER role."""
    # Arrange
    await create_winemaker_user(db_session, user_id=2, winery_id=1)
    
    request_data = {
        "code": "NEW-WINERY-001",
        "name": "New Winery",
        "location": "California"
    }
    
    # Act
    response = winemaker_client.post(
        "/api/v1/admin/wineries",
        json=request_data
    )
    
    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# GET /admin/wineries/{id} - Get Winery by ID
# =============================================================================

@pytest.mark.asyncio
async def test_get_winery_by_id_success_admin(client: TestClient, setup_test_data):
    """Test admin can get any winery by ID."""
    # Act
    response = client.get(
        "/api/v1/admin/wineries/1",
        headers=get_admin_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 1
    assert data["code"] == "WINERY-001"
    assert data["name"] == "Test Winery 1"


@pytest.mark.asyncio
async def test_get_winery_by_id_success_own_winery(client: TestClient, setup_test_data):
    """Test winemaker can get their own winery."""
    # Act
    response = client.get(
        "/api/v1/admin/wineries/1",  # Winemaker belongs to winery_id=1
        headers=get_winemaker_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_get_winery_by_id_forbidden_other_winery(winemaker_client: TestClient, setup_test_data):
    """Test winemaker cannot get different winery."""
    # Act
    response = winemaker_client.get(
        "/api/v1/admin/wineries/2",  # Winemaker belongs to winery_id=1
    )
    
    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_winery_by_id_not_found(client: TestClient, setup_test_data):
    """Test get non-existent winery returns 404."""
    # Act
    response = client.get(
        "/api/v1/admin/wineries/999",
        headers=get_admin_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# GET /admin/wineries/code/{code} - Get Winery by Code
# =============================================================================

@pytest.mark.asyncio
async def test_get_winery_by_code_success_admin(client: TestClient, setup_test_data):
    """Test admin can get any winery by code."""
    # Act
    response = client.get(
        "/api/v1/admin/wineries/code/WINERY-001",
        headers=get_admin_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["code"] == "WINERY-001"
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_get_winery_by_code_success_own_winery(client: TestClient, setup_test_data):
    """Test winemaker can get their own winery by code."""
    # Act
    response = client.get(
        "/api/v1/admin/wineries/code/WINERY-001",  # Winemaker belongs to winery_id=1
        headers=get_winemaker_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["code"] == "WINERY-001"


@pytest.mark.asyncio
async def test_get_winery_by_code_forbidden_other_winery(client: TestClient, setup_test_data):
    """Test winemaker cannot get different winery by code."""
    # Act
    response = client.get(
        "/api/v1/admin/wineries/code/WINERY-002",  # Winemaker belongs to winery_id=1
        headers=get_winemaker_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_winery_by_code_not_found(client: TestClient, setup_test_data):
    """Test get non-existent winery by code returns 404."""
    # Act
    response = client.get(
        "/api/v1/admin/wineries/code/NON-EXISTENT",
        headers=get_admin_headers()
    )
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# LIST TESTS - GET /admin/wineries
# =============================================================================

@pytest.mark.asyncio
async def test_list_wineries_success(client: TestClient, setup_test_data):
    """Test list wineries with default pagination."""
    # Act
    response = client.get("/api/v1/admin/wineries")
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["limit"] == 10
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_list_wineries_with_pagination(client: TestClient, setup_test_data):
    """Test list wineries with custom pagination."""
    # Act
    response = client.get("/api/v1/admin/wineries?limit=1&offset=1")
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 1
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert data["items"][0]["code"] == "WINERY-002"


@pytest.mark.asyncio
async def test_list_wineries_forbidden_for_winemaker(winemaker_client: TestClient, setup_test_data):
    """Test winemaker cannot list all wineries."""
    # Act
    response = winemaker_client.get("/api/v1/admin/wineries")
    
    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# UPDATE TESTS - PATCH /admin/wineries/{id}
# =============================================================================

@pytest.mark.asyncio
async def test_update_winery_success_admin(client: TestClient, setup_test_data):
    """Test admin can update any winery."""
    # Arrange
    update_data = {
        "name": "Updated Winery Name",
        "location": "New Location",
        "notes": "Updated notes"
    }
    
    # Act
    response = client.patch("/api/v1/admin/wineries/1", json=update_data)
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Winery Name"
    assert data["location"] == "New Location"
    assert data["notes"] == "Updated notes"
    assert data["code"] == "WINERY-001"  # Code should not change


@pytest.mark.asyncio
async def test_update_winery_success_own_winery(winemaker_client: TestClient, setup_test_data):
    """Test winemaker can update own winery."""
    # Arrange
    update_data = {
        "name": "My Updated Winery",
        "location": "My New Location"
    }
    
    # Act - Winemaker belongs to winery_id=1
    response = winemaker_client.patch("/api/v1/admin/wineries/1", json=update_data)
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "My Updated Winery"
    assert data["location"] == "My New Location"


@pytest.mark.asyncio
async def test_update_winery_forbidden_other_winery(winemaker_client: TestClient, setup_test_data):
    """Test winemaker cannot update different winery."""
    # Arrange
    update_data = {"name": "Hacked Name"}
    
    # Act - Winemaker belongs to winery_id=1, trying to update winery_id=2
    response = winemaker_client.patch("/api/v1/admin/wineries/2", json=update_data)
    
    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_update_winery_not_found(client: TestClient, setup_test_data):
    """Test update non-existent winery returns 404."""
    # Arrange
    update_data = {"name": "New Name"}
    
    # Act
    response = client.patch("/api/v1/admin/wineries/999", json=update_data)
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_winery_partial_update(client: TestClient, setup_test_data):
    """Test partial update (only name)."""
    # Arrange
    update_data = {"name": "Partially Updated Name"}
    
    # Act
    response = client.patch("/api/v1/admin/wineries/1", json=update_data)
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Partially Updated Name"
    assert data["location"] == "Test Location"  # Should remain unchanged


# =============================================================================
# DELETE TESTS - DELETE /admin/wineries/{id}
# =============================================================================

@pytest.mark.asyncio
async def test_delete_winery_success(client: TestClient, setup_test_data):
    """Test admin can delete winery."""
    # Act
    response = client.delete("/api/v1/admin/wineries/1")
    
    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify winery is soft-deleted (not actually removed)
    get_response = client.get("/api/v1/admin/wineries/1")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_winery_not_found(client: TestClient, setup_test_data):
    """Test delete non-existent winery returns 404."""
    # Act
    response = client.delete("/api/v1/admin/wineries/999")
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_winery_forbidden_for_winemaker(winemaker_client: TestClient, setup_test_data):
    """Test winemaker cannot delete winery."""
    # Act
    response = winemaker_client.delete("/api/v1/admin/wineries/1")
    
    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
