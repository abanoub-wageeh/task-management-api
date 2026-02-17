from fastapi import status
from app import models, oauth2, utils
from datetime import datetime, timedelta


def test_create_personal_task_success(client, session):
    """Test creating a personal task"""
    # Create user
    user = models.User(
        name="Task User",
        email="taskuser@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create auth headers
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Test Task",
            "description": "This is a test task with enough characters for validation",
            "priority": "high",
            "status": "pending"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["priority"] == "high"


def test_create_task_with_due_date(client, session):
    """Test creating a task with due date"""
    # Create user
    user = models.User(
        name="User",
        email="user@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
    response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Task with Due Date",
            "description": "This task has a due date set for next week",
            "due_date": due_date
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["due_date"] is not None


def test_create_project_task_as_owner(client, session):
    """Test owner can create tasks in their project"""
    # Create user
    user = models.User(
        name="Owner",
        email="owner@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create project
    project = models.Project(
        name="Test Project",
        description="A test project",
        status=models.ProjectStatusEnum.ACTIVE,
        owner_id=user.user_id
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # Add owner as project member
    member = models.ProjectMember(
        project_id=project.project_id,
        user_id=user.user_id,
        role=models.ProjectRoleEnum.OWNER
    )
    session.add(member)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Project Task",
            "description": "This is a task within a project context",
            "project_id": project.project_id
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["project_id"] == project.project_id


def test_create_task_in_project_as_editor(client, session):
    """Test editor can create tasks in project"""
    # Create owner
    owner = models.User(
        name="Owner",
        email="owner@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(owner)
    session.commit()
    session.refresh(owner)
    
    # Create editor
    editor = models.User(
        name="Editor",
        email="editor@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(editor)
    session.commit()
    session.refresh(editor)
    
    # Create project
    project = models.Project(
        name="Test Project",
        description="A test project",
        owner_id=owner.user_id
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # Add editor as member
    member = models.ProjectMember(
        project_id=project.project_id,
        user_id=editor.user_id,
        role=models.ProjectRoleEnum.EDITOR
    )
    session.add(member)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": editor.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Editor's Task",
            "description": "Task created by a project editor",
            "project_id": project.project_id
        }
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_create_task_in_project_as_viewer_fails(client, session):
    """Test viewer cannot create tasks in project"""
    # Create owner
    owner = models.User(
        name="Owner",
        email="owner@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(owner)
    session.commit()
    session.refresh(owner)
    
    # Create viewer
    viewer = models.User(
        name="Viewer",
        email="viewer@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(viewer)
    session.commit()
    session.refresh(viewer)
    
    # Create project
    project = models.Project(
        name="Test Project",
        description="A test project",
        owner_id=owner.user_id
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # Add viewer as member
    member = models.ProjectMember(
        project_id=project.project_id,
        user_id=viewer.user_id,
        role=models.ProjectRoleEnum.VIEWER
    )
    session.add(member)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": viewer.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Viewer's Task",
            "description": "This should fail as viewer cannot create",
            "project_id": project.project_id
        }
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_task_without_auth_fails(client):
    """Test creating task without authentication fails"""
    response = client.post(
        "/tasks",
        json={
            "title": "Unauthorized Task",
            "description": "This should fail without authentication"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_task_invalid_title_too_short(client, session):
    """Test creating task with too short title"""
    user = models.User(
        name="User",
        email="user1@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "T",
            "description": "Valid description with enough characters"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY




def test_get_all_tasks(client, session):
    """Test getting all tasks for current user"""
    # Create user and task
    user = models.User(
        name="User",
        email="user2@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    task = models.Task(
        title="Test Task",
        description="This is a test task description with enough characters",
        user_id=user.user_id
    )
    session.add(task)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/tasks", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1


def test_get_tasks_with_search(client, session):
    """Test searching tasks by title"""
    # Create user and task
    user = models.User(
        name="User",
        email="user3@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    task = models.Task(
        title="Searchable Task",
        description="This is a searchable test task description",
        user_id=user.user_id
    )
    session.add(task)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(
        "/tasks",
        headers=headers,
        params={"search": "Searchable"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1


def test_get_single_task(client, session):
    """Test getting a single task by ID"""
    # Create user and task
    user = models.User(
        name="User",
        email="user4@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    task = models.Task(
        title="Single Task",
        description="This is a single task to retrieve",
        user_id=user.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(
        f"/tasks/{task.task_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["task_id"] == task.task_id


def test_get_nonexistent_task(client, session):
    """Test getting non-existent task"""
    user = models.User(
        name="User",
        email="user5@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(
        "/tasks/99999",
        headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_other_users_personal_task_fails(client, session):
    """Test user cannot access another user's personal task"""
    # Create first user with task
    user1 = models.User(
        name="User 1",
        email="user6@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user1)
    session.commit()
    session.refresh(user1)
    
    task = models.Task(
        title="Private Task",
        description="This is a private task for user 1",
        user_id=user1.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    # Create second user
    user2 = models.User(
        name="User 2",
        email="user7@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user2)
    session.commit()
    session.refresh(user2)
    
    # Try to access user1's task as user2
    token = oauth2.create_access_token({"user_id": user2.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(
        f"/tasks/{task.task_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_update_task_title(client, session):
    """Test updating task title"""
    # Create user and task
    user = models.User(
        name="User",
        email="user8@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    task = models.Task(
        title="Original Title",
        description="Original description with enough characters",
        user_id=user.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.put(
        f"/tasks/{task.task_id}",
        headers=headers,
        json={"title": "Updated Task Title"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "Updated Task Title"


def test_update_task_status(client, session):
    """Test updating task status"""
    # Create user and task
    user = models.User(
        name="User",
        email="user9@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    task = models.Task(
        title="Task",
        description="Task description with enough characters",
        status=models.StatusEnum.PENDING,
        user_id=user.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.put(
        f"/tasks/{task.task_id}",
        headers=headers,
        json={"status": "completed"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "completed"


def test_update_other_users_personal_task_fails(client, session):
    """Test user cannot update another user's personal task"""
    # Create two users
    user1 = models.User(
        name="User 1",
        email="user10@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user1)
    session.commit()
    session.refresh(user1)
    
    task = models.Task(
        title="User 1 Task",
        description="This task belongs to user 1",
        user_id=user1.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    user2 = models.User(
        name="User 2",
        email="user11@example.com",
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
        f"/tasks/{task.task_id}",
        headers=headers,
        json={"title": "Unauthorized Update"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_nonexistent_task(client, session):
    """Test updating non-existent task"""
    user = models.User(
        name="User",
        email="user12@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.put(
        "/tasks/99999",
        headers=headers,
        json={"title": "This should fail"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_task_success(client, session):
    """Test successful task deletion"""
    # Create user and task
    user = models.User(
        name="User",
        email="user13@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    task = models.Task(
        title="Task to Delete",
        description="This task will be deleted",
        user_id=user.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.delete(
        f"/tasks/{task.task_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify task is deleted
    get_response = client.get(
        f"/tasks/{task.task_id}",
        headers=headers
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_nonexistent_task(client, session):
    """Test deleting non-existent task"""
    user = models.User(
        name="User",
        email="user16@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.delete(
        "/tasks/99999",
        headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_assign_task_to_self(client, session):
    """Test assigning personal task to self"""
    # Create user and task
    user = models.User(
        name="User",
        email="user18@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    task = models.Task(
        title="Self Assign Task",
        description="This task will be self-assigned",
        user_id=user.user_id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.put(
        f"/tasks/{task.task_id}/assign",
        headers=headers,
        json={"assignee_id": user.user_id}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["assignee_id"] == user.user_id

