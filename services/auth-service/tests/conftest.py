"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.auth import Base, User, Role
from app.db.session import get_db
from app.utils.security import get_password_hash

# Create in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # Create default roles
    roles = [
        Role(name="admin", description="Administrator"),
        Role(name="user", description="Regular user"),
        Role(name="moderator", description="Moderator"),
    ]
    for role in roles:
        db.add(role)
    db.commit()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from app.models.auth import UserRole
    
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("TestPassword123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    
    # Assign user role
    role = db_session.query(Role).filter_by(name="user").first()
    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)
    
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user."""
    from app.models.auth import UserRole
    
    user = User(
        email="admin@example.com",
        username="adminuser",
        password_hash=get_password_hash("AdminPassword123!"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.flush()
    
    # Assign admin role
    role = db_session.query(Role).filter_by(name="admin").first()
    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)
    
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPassword123!"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Get authentication headers for admin user."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "adminuser",
            "password": "AdminPassword123!"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
