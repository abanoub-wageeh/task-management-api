from fastapi import status
from app import models, oauth2, utils


def test_create_comment_on_task(client, session):
    """Test creating a comment on a task"""
    # Create user
    user = models.User(
        name="User",
        email="user1@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create task
    task = models.Task(
        title="Task with Comments",
        description="This task will have comments",
        user_id=user.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        f"/tasks/{task.task_id}/comments",
        headers=headers,
        json={"content": "This is a test comment"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["content"] == "This is a test comment"


def test_get_all_comments_for_task(client, session):
    """Test getting all comments for a task"""
    # Create user
    user = models.User(
        name="User",
        email="user2@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create task
    task = models.Task(
        title="Task",
        description="A task with comments",
        user_id=user.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    # Create comment
    comment = models.Comment(
        content="Test comment",
        user_id=user.user_id,
        task_id=task.task_id
    )
    session.add(comment)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(f"/tasks/{task.task_id}/comments", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1


def test_update_comment(client, session):
    """Test updating a comment"""
    # Create user
    user = models.User(
        name="User",
        email="user3@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create task
    task = models.Task(
        title="Task",
        description="A task with updatable comment",
        user_id=user.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    # Create comment
    comment = models.Comment(
        content="Original comment",
        user_id=user.user_id,
        task_id=task.task_id
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.put(
        f"/tasks/{task.task_id}/comments/{comment.comment_id}",
        headers=headers,
        json={"content": "Updated comment"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["content"] == "Updated comment"


def test_update_other_users_comment_fails(client, session):
    """Test user cannot update another user's comment"""
    # Create user 1 with task and comment
    user1 = models.User(
        name="User 1",
        email="user4@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user1)
    session.commit()
    session.refresh(user1)
    
    task = models.Task(
        title="Task",
        description="A task with comment",
        user_id=user1.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    comment = models.Comment(
        content="User 1 comment",
        user_id=user1.user_id,
        task_id=task.task_id
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    
    # Create user 2
    user2 = models.User(
        name="User 2",
        email="user5@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user2)
    session.commit()
    session.refresh(user2)
    
    # Try to update as user2
    token = oauth2.create_access_token({"user_id": user2.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.put(
        f"/tasks/{task.task_id}/comments/{comment.comment_id}",
        headers=headers,
        json={"content": "Unauthorized update"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_comment(client, session):
    """Test deleting a comment"""
    # Create user
    user = models.User(
        name="User",
        email="user6@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create task
    task = models.Task(
        title="Task",
        description="A task with deletable comment",
        user_id=user.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    # Create comment
    comment = models.Comment(
        content="Comment to delete",
        user_id=user.user_id,
        task_id=task.task_id
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.delete(
        f"/tasks/{task.task_id}/comments/{comment.comment_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert "deleted" in response.json()["message"]


def test_delete_other_users_comment_fails(client, session):
    """Test user cannot delete another user's comment"""
    # Create user 1 with task and comment
    user1 = models.User(
        name="User 1",
        email="user7@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user1)
    session.commit()
    session.refresh(user1)
    
    task = models.Task(
        title="Task",
        description="A task with comment",
        user_id=user1.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    comment = models.Comment(
        content="User 1 comment",
        user_id=user1.user_id,
        task_id=task.task_id
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    
    # Create user 2
    user2 = models.User(
        name="User 2",
        email="user8@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user2)
    session.commit()
    session.refresh(user2)
    
    # Try to delete as user2
    token = oauth2.create_access_token({"user_id": user2.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.delete(
        f"/tasks/{task.task_id}/comments/{comment.comment_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_comment_on_nonexistent_task_fails(client, session):
    """Test creating comment on non-existent task fails"""
    # Create user
    user = models.User(
        name="User",
        email="user9@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/tasks/99999/comments",
        headers=headers,
        json={"content": "This should fail"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
