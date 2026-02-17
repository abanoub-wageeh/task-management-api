from fastapi import status
from app import models, oauth2, utils


def test_create_project_success(client, session):
    """Test creating a project"""
    # Create user
    user = models.User(
        name="Project Owner",
        email="owner@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/projects",
        headers=headers,
        json={
            "name": "Test Project",
            "description": "This is a test project"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "This is a test project"


def test_get_all_projects(client, session):
    """Test getting all projects for user"""
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
    
    # Create project
    project = models.Project(
        name="User Project",
        description="A project for user",
        owner_id=user.user_id
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # Add user as member
    member = models.ProjectMember(
        project_id=project.project_id,
        user_id=user.user_id,
        role=models.ProjectRoleEnum.OWNER
    )
    session.add(member)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/projects", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1


def test_get_single_project(client, session):
    """Test getting a single project"""
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
    
    # Create project
    project = models.Project(
        name="Single Project",
        description="A single project to retrieve",
        owner_id=user.user_id
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # Add user as member
    member = models.ProjectMember(
        project_id=project.project_id,
        user_id=user.user_id,
        role=models.ProjectRoleEnum.OWNER
    )
    session.add(member)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(f"/projects/{project.project_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["project_id"] == project.project_id


def test_update_project_as_owner(client, session):
    """Test project owner can update project"""
    # Create user
    user = models.User(
        name="Owner",
        email="owner2@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create project
    project = models.Project(
        name="Original Name",
        description="Original description",
        owner_id=user.user_id
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # Add user as member
    member = models.ProjectMember(
        project_id=project.project_id,
        user_id=user.user_id,
        role=models.ProjectRoleEnum.OWNER
    )
    session.add(member)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.put(
        f"/projects/{project.project_id}",
        headers=headers,
        json={
            "name": "Updated Project",
            "description": "Updated description"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Updated Project"


def test_update_project_as_editor(client, session):
    """Test project editor can update project"""
    # Create owner
    owner = models.User(
        name="Owner",
        email="owner3@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(owner)
    session.commit()
    session.refresh(owner)
    
    # Create editor
    editor = models.User(
        name="Editor",
        email="editor1@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(editor)
    session.commit()
    session.refresh(editor)
    
    # Create project
    project = models.Project(
        name="Project",
        description="A project",
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
    
    response = client.put(
        f"/projects/{project.project_id}",
        headers=headers,
        json={
            "name": "Updated by Editor",
            "description": "Editor updated this"
        }
    )
    assert response.status_code == status.HTTP_200_OK


def test_delete_project_as_owner(client, session):
    """Test project owner can delete project"""
    # Create user
    user = models.User(
        name="Owner",
        email="owner4@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create project
    project = models.Project(
        name="Project to Delete",
        description="This project will be deleted",
        owner_id=user.user_id
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # Add user as member
    member = models.ProjectMember(
        project_id=project.project_id,
        user_id=user.user_id,
        role=models.ProjectRoleEnum.OWNER
    )
    session.add(member)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": user.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.delete(f"/projects/{project.project_id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_add_member_to_project(client, session):
    """Test adding a member to project"""
    # Create owner
    owner = models.User(
        name="Owner",
        email="owner5@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(owner)
    session.commit()
    session.refresh(owner)
    
    # Create new member user
    new_member = models.User(
        name="New Member",
        email="newmember@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(new_member)
    session.commit()
    session.refresh(new_member)
    
    # Create project
    project = models.Project(
        name="Team Project",
        description="A team project",
        owner_id=owner.user_id
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # Add owner as member
    member = models.ProjectMember(
        project_id=project.project_id,
        user_id=owner.user_id,
        role=models.ProjectRoleEnum.OWNER
    )
    session.add(member)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": owner.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        f"/projects/{project.project_id}/members",
        headers=headers,
        json={
            "user_email": "newmember@example.com",
            "role": "editor"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_get_project_members(client, session):
    """Test getting all members of a project"""
    # Create owner
    owner = models.User(
        name="Owner",
        email="owner6@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(owner)
    session.commit()
    session.refresh(owner)
    
    # Create project
    project = models.Project(
        name="Team Project",
        description="A project with members",
        owner_id=owner.user_id
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # Add owner as member
    member = models.ProjectMember(
        project_id=project.project_id,
        user_id=owner.user_id,
        role=models.ProjectRoleEnum.OWNER
    )
    session.add(member)
    session.commit()
    
    token = oauth2.create_access_token({"user_id": owner.user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(f"/projects/{project.project_id}/members", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1


def test_viewer_cannot_update_project(client, session):
    """Test project viewer cannot update project"""
    # Create owner
    owner = models.User(
        name="Owner",
        email="owner7@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(owner)
    session.commit()
    session.refresh(owner)
    
    # Create viewer
    viewer = models.User(
        name="Viewer",
        email="viewer1@example.com",
        password_hash=utils.hash_password("password123"),
        is_active=True
    )
    session.add(viewer)
    session.commit()
    session.refresh(viewer)
    
    # Create project
    project = models.Project(
        name="Project",
        description="A project",
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
    
    response = client.put(
        f"/projects/{project.project_id}",
        headers=headers,
        json={
            "name": "Unauthorized Update",
            "description": "This should fail"
        }
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
