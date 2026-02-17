import sys
import os
from pathlib import Path

# Add the parent directory (workspace root) to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from app.main import app
from app import models, utils


# Create in-memory SQLite database for testing
@pytest.fixture(name="session", scope="function")
def session_fixture():
    """Create a fresh database session for each test"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session):
    """Create a test client with a test database session"""
    def get_session_override():
        return session
    
    app.dependency_overrides[models.get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# Mock email sending for tests
@pytest.fixture(autouse=True)
def mock_email_sending(monkeypatch):
    """Mock all email sending functions to prevent actual emails during tests"""
    def mock_send_verification_email(email, token):
        pass
    
    def mock_send_reset_password_email(receiver_email, reset_token):
        pass
    
    def mock_send_task_assignment_email(**kwargs):
        pass
    
    monkeypatch.setattr(utils, "send_verification_email", mock_send_verification_email)
    monkeypatch.setattr(utils, "send_reset_password_email", mock_send_reset_password_email)
    monkeypatch.setattr(utils, "send_task_assignment_email", mock_send_task_assignment_email)
