from fastapi import status
from app import models, oauth2, utils


def test_register_user_success(client):
    """Test successful user registration"""
    response = client.post(
        "/register",
        json={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert "user had been created successfully" in response.json()["message"]


def test_register_duplicate_email(client, session):
    """Test registration with existing email"""
    # Create existing user
    user = models.User(
        name="Existing User",
        email="existing@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    
    # Try to register with same email
    response = client.post(
        "/register",
        json={
            "name": "Another User",
            "email": "existing@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "user already exist" in response.json()["detail"]


def test_register_invalid_email(client):  
    """Test registration with invalid email format"""
    response = client.post(
        "/register",
        json={
            "name": "Test User",
            "email": "invalidemail",
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_verify_account_success(client, session):
    """Test successful email verification"""
    # Create inactive user
    user = models.User(
        name="Verify User",
        email="verify@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=False
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Generate verification token
    token = oauth2.create_verification_token({"user_id": user.user_id})
    
    # Verify account
    response = client.get(f"/verify?token={token}")
    assert response.status_code == status.HTTP_200_OK
    assert "verified successfully" in response.json()["message"]
    
    # Check user is now active
    session.refresh(user)
    assert user.is_active == True


def test_verify_already_verified_account(client, session):
    """Test verifying an already verified account"""
    # Create active user
    user = models.User(
        name="Active User",
        email="active@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    token = oauth2.create_verification_token({"user_id": user.user_id})
    response = client.get(f"/verify?token={token}")
    assert response.status_code == status.HTTP_200_OK
    assert "already verified" in response.json()["message"]


def test_verify_invalid_token(client):
    """Test verification with invalid token"""
    response = client.get("/verify?token=invalid_token")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_verify_nonexistent_user(client):
    """Test verification with token for non-existent user"""
    token = oauth2.create_verification_token({"user_id": 99999})
    response = client.get(f"/verify?token={token}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_login_success(client, session):
    """Test successful login"""
    # Create active user
    user = models.User(
        name="Login User",
        email="loginuser@example.com",
        password_hash=utils.hash_password("testpassword123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    
    response = client.post(
        "/login",
        json={
            "email": "loginuser@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_invalid_credentials(client, session):
    """Test login with wrong password"""
    # Create user
    user = models.User(
        name="Test User",
        email="testuser@example.com",
        password_hash=utils.hash_password("correctpassword"),
        is_active=True
    )
    session.add(user)
    session.commit()
    
    response = client.post(
        "/login",
        json={
            "email": "testuser@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid credentials" in response.json()["detail"]


def test_login_nonexistent_user(client):
    """Test login with non-existent email"""
    response = client.post(
        "/login",
        json={
            "email": "notexist@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "user not found" in response.json()["detail"]


def test_login_inactive_user(client, session):
    """Test login with inactive account"""
    # Create inactive user
    user = models.User(
        name="Inactive User",
        email="inactive@example.com",
        password_hash=utils.hash_password("testpassword123"),
        is_active=False
    )
    session.add(user)
    session.commit()
    
    response = client.post(
        "/login",
        json={
            "email": "inactive@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "verify your account" in response.json()["detail"]

def test_refresh_token_success(client, session):
    """Test successful token refresh"""
    # Create user and login
    user = models.User(
        name="Refresh User",
        email="refresh@example.com",
        password_hash=utils.hash_password("testpassword123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    
    # Login to get refresh token
    login_response = client.post(
        "/login",
        json={
            "email": "refresh@example.com",
            "password": "testpassword123"
        }
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Use refresh token to get new access token
    response = client.post(f"/refresh?token={refresh_token}")
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


def test_refresh_token_invalid(client):
    """Test refresh with invalid token"""
    response = client.post("/refresh?token=invalid_token")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_token_mismatch(client, session):
    """Test refresh token that doesn't match stored token"""
    # Create user
    user = models.User(
        name="Token User",
        email="token@example.com",
        password_hash=utils.hash_password("testpassword123"),
        is_active=True,
        refresh_token="different_token"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create a valid refresh token but different from stored
    fake_token = oauth2.create_refresh_token({"user_id": user.user_id})
    
    response = client.post(f"/refresh?token={fake_token}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_revoke_refresh_token(client, session):
    """Test revoking refresh token"""
    # Create user with refresh token
    user = models.User(
        name="Revoke User",
        email="revoke@example.com",
        password_hash=utils.hash_password("testpassword123"),
        is_active=True,
        refresh_token="some_refresh_token"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create auth headers
    access_token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = client.put("/revoke", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert "revoked successfully" in response.json()["message"]
    
    # Verify token is cleared
    session.refresh(user)
    assert user.refresh_token is None


def test_revoke_without_auth(client):
    """Test revoke without authentication"""
    response = client.put("/revoke")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_change_password_success(client, session):
    """Test successful password change"""
    # Create user
    user = models.User(
        name="Change Pass User",
        email="changepass@example.com",
        password_hash=utils.hash_password("testpassword123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create auth headers
    access_token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = client.post(
        "/change_password",
        headers=headers,
        json={
            "old_password": "testpassword123",
            "new_password": "newpassword123",
            "new_password_conform": "newpassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert "changed successfully" in response.json()["message"]
    
    # Verify can login with new password
    login_response = client.post(
        "/login",
        json={
            "email": "changepass@example.com",
            "password": "newpassword123"
        }
    )
    assert login_response.status_code == status.HTTP_200_OK


def test_change_password_wrong_old_password(client, session):
    """Test password change with incorrect old password"""
    # Create user
    user = models.User(
        name="Test User",
        email="test@example.com",
        password_hash=utils.hash_password("correctpassword"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create auth headers
    access_token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = client.post(
        "/change_password",
        headers=headers,
        json={
            "old_password": "wrongpassword",
            "new_password": "newpassword123",
            "new_password_conform": "newpassword123"
        }
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Invalid credentials" in response.json()["detail"]


def test_change_password_mismatch(client, session):
    """Test password change with mismatched new passwords"""
    # Create user
    user = models.User(
        name="Test User",
        email="test2@example.com",
        password_hash=utils.hash_password("testpassword123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create auth headers
    access_token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = client.post(
        "/change_password",
        headers=headers,
        json={
            "old_password": "testpassword123",
            "new_password": "newpassword123",
            "new_password_conform": "differentpassword"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "do not match" in response.json()["detail"]


def test_change_password_too_short(client, session):
    """Test password change with too short password"""
    # Create user
    user = models.User(
        name="Test User",
        email="test3@example.com",
        password_hash=utils.hash_password("testpassword123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create auth headers
    access_token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = client.post(
        "/change_password",
        headers=headers,
        json={
            "old_password": "testpassword123",
            "new_password": "short",
            "new_password_conform": "short"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "at least 8 characters" in response.json()["detail"]


def test_change_password_without_auth(client):
    """Test password change without authentication"""
    response = client.post(
        "/change_password",
        json={
            "old_password": "testpassword123",
            "new_password": "newpassword123",
            "new_password_conform": "newpassword123"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_forget_password_existing_user(client, session):
    """Test forgot password request for existing user"""
    # Create user
    user = models.User(
        name="Forget User",
        email="forgetuser@example.com",
        password_hash=utils.hash_password("testpassword123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    
    response = client.post(
        "/forget_password",
        json={"email": "forgetuser@example.com"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "email has been sent" in response.json()["message"]


def test_forget_password_nonexistent_user(client):
    """Test forgot password for non-existent user (should still return success)"""
    response = client.post(
        "/forget_password",
        json={"email": "notexist@example.com"}
    )
    # Should return success to not leak user existence
    assert response.status_code == status.HTTP_200_OK


def test_reset_password_success(client, session):
    """Test successful password reset"""
    # Create user
    user = models.User(
        name="Reset User",
        email="resetuser@example.com",
        password_hash=utils.hash_password("oldpassword123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Generate reset token
    reset_token = oauth2.create_reset_password_token({"user_id": user.user_id})
    
    response = client.post(
        f"/forget_password/reset?token={reset_token}",
        json={
            "new_password": "resetpassword123",
            "new_password_conform": "resetpassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert "reset successfully" in response.json()["message"]
    
    # Verify can login with new password
    login_response = client.post(
        "/login",
        json={
            "email": "resetuser@example.com",
            "password": "resetpassword123"
        }
    )
    assert login_response.status_code == status.HTTP_200_OK


def test_reset_password_mismatch(client, session):
    """Test password reset with mismatched passwords"""
    # Create user
    user = models.User(
        name="Test User",
        email="test4@example.com",
        password_hash=utils.hash_password("oldpassword"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    reset_token = oauth2.create_reset_password_token({"user_id": user.user_id})
    
    response = client.post(
        f"/forget_password/reset?token={reset_token}",
        json={
            "new_password": "resetpassword123",
            "new_password_conform": "differentpassword"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "do not match" in response.json()["detail"]


def test_reset_password_invalid_token(client):
    """Test password reset with invalid token"""
    response = client.post(
        "/forget_password/reset?token=invalid_token",
        json={
            "new_password": "resetpassword123",
            "new_password_conform": "resetpassword123"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_reset_password_nonexistent_user(client):
    """Test password reset for non-existent user"""
    reset_token = oauth2.create_reset_password_token({"user_id": 99999})
    
    response = client.post(
        f"/forget_password/reset?token={reset_token}",
        json={
            "new_password": "resetpassword123",
            "new_password_conform": "resetpassword123"
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
