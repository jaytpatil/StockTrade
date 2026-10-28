import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db
import models
import auth

# Initialize a completely isolated SQLite memory database specifically for fast testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
            
    # Override FastAPI dependency temporarily
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def auth_header(client, test_db):
    """Fixture that generates a fresh internal user and returns their JWT token."""
    # Build raw dummy user payload manually for tests without hitting standard routes
    password_hash = auth.get_password_hash("testpass")
    test_user = models.User(email="fixture@test.com", hashed_password=password_hash, role=models.RoleEnum.USER)
    test_db.add(test_user)
    test_db.commit()

    token = auth.create_access_token({"sub": "fixture@test.com"})
    return {"Authorization": f"Bearer {token}"}
