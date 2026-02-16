from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlmodel import Session, select
from app import schemas, models
from .. import oauth2
from datetime import datetime
from enum import Enum


router = APIRouter(tags=["projects"])


# Helper functions for permission checking
def get_project_member(db: Session, project_id: int, user_id: int) -> models.ProjectMember | None:
    """Get project member record for a user in a project"""
    return db.exec(
        select(models.ProjectMember).where(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == user_id
        )
    ).first()


def check_project_permission(db: Session, project_id: int, user_id: int, required_roles: list[models.ProjectRoleEnum]) -> models.ProjectMember:
    """Check if user has required role in project, raise exception if not"""
    member = get_project_member(db, project_id, user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    if member.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You need {' or '.join([r.value for r in required_roles])} role to perform this action"
        )
    return member


def get_user_projects_query(db: Session, user_id: int):
    """Get query for projects where user is a member"""
    member_project_ids = db.exec(
        select(models.ProjectMember.project_id).where(
            models.ProjectMember.user_id == user_id
        )
    ).all()
    return member_project_ids

@router.post("/projects", status_code=status.HTTP_201_CREATED ,response_model=schemas.ProjectResponse)
def create_project(project_data : schemas.ProjectCreate, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    new_project = models.Project(**project_data.model_dump(), owner_id=user_id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    # Automatically add the creator as owner member
    owner_member = models.ProjectMember(
        project_id=new_project.project_id,
        user_id=user_id,
        role=models.ProjectRoleEnum.OWNER
    )
    db.add(owner_member)
    db.commit()
    
    return new_project

@router.get("/projects", response_model=list[schemas.ProjectResponse])
def get_all_projects(
    search: str | None = Query(default=None, max_length=100, description="Search projects by name or description"),
    status: models.ProjectStatusEnum | None = None,
    created_at=None,
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user)
):
    # Get all project IDs where user is a member
    member_project_ids = get_user_projects_query(db, user_id)
    
    # Query projects where user is a member
    statement = select(models.Project).where(
        models.Project.project_id.in_(member_project_ids),
        models.Project.is_deleted == False
    )
    
    # search by name or description
    if search:
        from sqlalchemy import or_
        search_pattern = f"%{search}%"
        statement = statement.where(
            or_(
                models.Project.name.ilike(search_pattern),
                models.Project.description.ilike(search_pattern)
            )
        )
    # filters
    if status:
        statement = statement.where(models.Project.status == status)
    # sorting
    if created_at:
        column = getattr(models.Project, created_at.value)
        statement = statement.order_by(column.desc())
    projects = db.exec(statement).all()
    return projects

@router.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id : int, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    # Check if user has access to project (any role can view)
    check_project_permission(db, project_id, user_id, [
        models.ProjectRoleEnum.OWNER,
        models.ProjectRoleEnum.EDITOR,
        models.ProjectRoleEnum.VIEWER
    ])
    
    project = db.exec(select(models.Project).where(
        models.Project.project_id == project_id,
        models.Project.is_deleted == False
    )).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    return project

@router.put("/projects/{project_id}", response_model=schemas.ProjectResponse)
def update_project(project_id : int, project_data : schemas.ProjectUpdate, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    # Only owners and editors can update projects
    check_project_permission(db, project_id, user_id, [
        models.ProjectRoleEnum.OWNER,
        models.ProjectRoleEnum.EDITOR
    ])
    
    project = db.exec(select(models.Project).where(
        models.Project.project_id == project_id,
        models.Project.is_deleted == False
    )).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    for column, value in project_data.model_dump(exclude_unset=True).items():
        setattr(project, column, value)
    project.updated_at = datetime.utcnow()
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id : int, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    # Only owners can delete projects
    check_project_permission(db, project_id, user_id, [models.ProjectRoleEnum.OWNER])
    
    project = db.exec(
        select(models.Project).where(
            models.Project.project_id == project_id,
            models.Project.is_deleted == False,
        )
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    project.is_deleted = True
    project.deleted_at = datetime.utcnow()
    db.commit()


# ==================== PROJECT MEMBER MANAGEMENT ENDPOINTS ====================

@router.post("/projects/{project_id}/members", status_code=status.HTTP_201_CREATED, response_model=schemas.ProjectMemberResponse)
def add_project_member(
    project_id: int,
    member_data: schemas.ProjectMemberAdd,
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user)
):
    """Add a member to a project. Only owners can add members."""
    # Only owners can add members
    check_project_permission(db, project_id, user_id, [models.ProjectRoleEnum.OWNER])
    
    # Check if project exists and is not deleted
    project = db.exec(
        select(models.Project).where(
            models.Project.project_id == project_id,
            models.Project.is_deleted == False
        )
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    
    # Find user by email
    new_member_user = db.exec(
        select(models.User).where(models.User.email == member_data.user_email)
    ).first()
    if not new_member_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    # Check if user is already a member
    existing_member = get_project_member(db, project_id, new_member_user.user_id)
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user is already a member of this project"
        )
    
    # Add new member
    new_member = models.ProjectMember(
        project_id=project_id,
        user_id=new_member_user.user_id,
        role=member_data.role
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    
    # Prepare response with user details
    user_basic = schemas.UserBasic(
        user_id=new_member_user.user_id,
        name=new_member_user.name,
        email=new_member_user.email
    )
    
    return schemas.ProjectMemberResponse(
        member_id=new_member.member_id,
        project_id=new_member.project_id,
        user=user_basic,
        role=new_member.role,
        joined_at=new_member.joined_at
    )


@router.get("/projects/{project_id}/members", response_model=list[schemas.ProjectMemberResponse])
def get_project_members(
    project_id: int,
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user)
):
    """Get all members of a project. All members can view the member list."""
    # Check if user has access to project
    check_project_permission(db, project_id, user_id, [
        models.ProjectRoleEnum.OWNER,
        models.ProjectRoleEnum.EDITOR,
        models.ProjectRoleEnum.VIEWER
    ])
    
    # Get all members
    members = db.exec(
        select(models.ProjectMember).where(
            models.ProjectMember.project_id == project_id
        )
    ).all()
    
    # Build response with user details
    response = []
    for member in members:
        user = db.get(models.User, member.user_id)
        if user:
            user_basic = schemas.UserBasic(
                user_id=user.user_id,
                name=user.name,
                email=user.email
            )
            response.append(schemas.ProjectMemberResponse(
                member_id=member.member_id,
                project_id=member.project_id,
                user=user_basic,
                role=member.role,
                joined_at=member.joined_at
            ))
    
    return response


@router.put("/projects/{project_id}/members/{member_user_id}", response_model=schemas.ProjectMemberResponse)
def update_member_role(
    project_id: int,
    member_user_id: int,
    role_update: schemas.ProjectMemberRoleUpdate,
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user)
):
    """Update a member's role. Only owners can update roles."""
    # Only owners can update member roles
    check_project_permission(db, project_id, user_id, [models.ProjectRoleEnum.OWNER])
    
    # Get the member to update
    member = get_project_member(db, project_id, member_user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="member not found in this project"
        )
    
    # Prevent changing the role of the last owner
    if member.role == models.ProjectRoleEnum.OWNER and role_update.role != models.ProjectRoleEnum.OWNER:
        owner_count = db.exec(
            select(models.ProjectMember).where(
                models.ProjectMember.project_id == project_id,
                models.ProjectMember.role == models.ProjectRoleEnum.OWNER
            )
        ).all()
        if len(owner_count) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cannot change the role of the last owner. Add another owner first"
            )
    
    # Update role
    member.role = role_update.role
    db.add(member)
    db.commit()
    db.refresh(member)
    
    # Get user details for response
    user = db.get(models.User, member.user_id)
    user_basic = schemas.UserBasic(
        user_id=user.user_id,
        name=user.name,
        email=user.email
    )
    
    return schemas.ProjectMemberResponse(
        member_id=member.member_id,
        project_id=member.project_id,
        user=user_basic,
        role=member.role,
        joined_at=member.joined_at
    )


@router.delete("/projects/{project_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: int,
    member_user_id: int,
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user)
):
    """Remove a member from a project. Only owners can remove members."""
    # Only owners can remove members
    check_project_permission(db, project_id, user_id, [models.ProjectRoleEnum.OWNER])
    
    # Get the member to remove
    member = get_project_member(db, project_id, member_user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="member not found in this project"
        )
    
    # Prevent removing the last owner
    if member.role == models.ProjectRoleEnum.OWNER:
        owner_count = db.exec(
            select(models.ProjectMember).where(
                models.ProjectMember.project_id == project_id,
                models.ProjectMember.role == models.ProjectRoleEnum.OWNER
            )
        ).all()
        if len(owner_count) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cannot remove the last owner from the project"
            )
    
    # Remove member
    db.delete(member)
    db.commit()
