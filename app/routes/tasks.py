from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlmodel import Session, select
from app import schemas, models
from .. import oauth2
from datetime import datetime
from enum import Enum

router = APIRouter(tags=["Tasks"])


# Helper functions for task permission checking
def get_project_member(db: Session, project_id: int, user_id: int) -> models.ProjectMember | None:
    """Get project member record for a user in a project"""
    return db.exec(
        select(models.ProjectMember).where(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == user_id
        )
    ).first()


def check_task_access(db: Session, task: models.Task, user_id: int, required_roles: list[models.ProjectRoleEnum] | None = None):
    """
    Check if user has access to a task.
    - If task has no project: only creator can access
    - If task has project: user must be a project member with required role
    """
    # If task belongs to a project
    if task.project_id:
        member = get_project_member(db, task.project_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project's tasks"
            )
        
        # If specific roles are required, check them
        if required_roles and member.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You need {' or '.join([r.value for r in required_roles])} role to perform this action"
            )
        return member
    else:
        # Personal task - only creator can access
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this task"
            )
        return None


def get_accessible_project_ids(db: Session, user_id: int) -> list[int]:
    """Get all project IDs where user is a member"""
    return db.exec(
        select(models.ProjectMember.project_id).where(
            models.ProjectMember.user_id == user_id
        )
    ).all()


@router.post(
    "/tasks", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED
)
def create_task(
    task_data: schemas.TaskCreate,
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user),
):
    # If task is assigned to a project, verify user has permission
    if task_data.project_id:
        member = get_project_member(db, task_data.project_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project"
            )
        # Only owners and editors can create tasks in a project
        if member.role not in [models.ProjectRoleEnum.OWNER, models.ProjectRoleEnum.EDITOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You need owner or editor role to create tasks in this project"
            )
        
        # Verify project exists and is not deleted
        project = db.exec(
            select(models.Project).where(
                models.Project.project_id == task_data.project_id,
                models.Project.is_deleted == False
            )
        ).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # If assignee is specified, verify they are a project member
        if task_data.assignee_id:
            assignee_member = get_project_member(db, task_data.project_id, task_data.assignee_id)
            if not assignee_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee must be a member of the project"
                )
    else:
        # For personal tasks, can only assign to self
        if task_data.assignee_id and task_data.assignee_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Personal tasks can only be assigned to yourself"
            )
    
    # Verify assignee exists if provided
    if task_data.assignee_id:
        assignee = db.get(models.User, task_data.assignee_id)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee user not found"
            )
    
    new_task = models.Task(**task_data.model_dump(exclude_unset=True))
    new_task.user_id = user_id
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

class SortBy(Enum):
    CREATED_AT = "created_at"
    DUE_DATE = "due_date"

class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"

@router.get("/tasks", response_model=list[schemas.TaskResponse])
def get_all_tasks(
    status: models.StatusEnum | None = None,
    priority: models.PriorityEnum | None = None,
    project_id: int | None = None,
    assignee_id: int | None = None,
    sort_by: SortBy | None = None,
    sort_order : SortOrder | None = None,
    limit : int = Query(default=10, ge=1, le=100),
    offset : int = Query(default=0, ge=0),
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user),
):
    # Get projects where user is a member
    accessible_project_ids = get_accessible_project_ids(db, user_id)
    
    # Build query: personal tasks OR tasks in accessible projects
    from sqlalchemy import or_
    statement = select(models.Task).where(
        models.Task.is_deleted == False
    ).where(
        or_(
            models.Task.user_id == user_id,
            models.Task.project_id.in_(accessible_project_ids)
        )
    )
    
    # Filter by specific project if requested
    if project_id:
        # Verify user has access to this project
        if project_id not in accessible_project_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project"
            )
        statement = statement.where(models.Task.project_id == project_id)
    
    # filtering
    if status:
        statement = statement.where(models.Task.status == status)
    if priority:
        statement = statement.where(models.Task.priority == priority)
    if assignee_id is not None:
        statement = statement.where(models.Task.assignee_id == assignee_id)
    # sorting
    if sort_by:
        column = getattr(models.Task, sort_by.value)
        if sort_order == SortOrder.DESC:
            statement = statement.order_by(column.desc())
        else:
            statement = statement.order_by(column.asc())
    # pagination
    statement = statement.offset(offset).limit(limit)
    tasks = db.exec(statement).all()
    return tasks


@router.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_a_task(
    task_id: int,
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user),
):
    task = db.exec(
        select(models.Task).where(
            models.Task.task_id == task_id,
            models.Task.is_deleted == False
        )
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="task not found"
        )
    
    # Check if user has access to this task
    check_task_access(db, task, user_id)
    
    return task


@router.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_data: schemas.TaskUpdate,
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user),
):
    task = db.exec(
        select(models.Task).where(
            models.Task.task_id == task_id,
            models.Task.is_deleted == False
        )
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="task not found"
        )
    
    # Check if user has permission to edit (owners and editors only for project tasks)
    if task.project_id:
        check_task_access(db, task, user_id, [
            models.ProjectRoleEnum.OWNER,
            models.ProjectRoleEnum.EDITOR
        ])
    else:
        check_task_access(db, task, user_id)
    
    # Validate assignee_id if being updated
    if 'assignee_id' in task_data.model_dump(exclude_unset=True):
        new_assignee_id = task_data.assignee_id
        if new_assignee_id is not None:
            # Verify assignee exists
            assignee = db.get(models.User, new_assignee_id)
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignee user not found"
                )
            
            # For project tasks, verify assignee is a project member
            if task.project_id:
                assignee_member = get_project_member(db, task.project_id, new_assignee_id)
                if not assignee_member:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Assignee must be a member of the project"
                    )
            else:
                # For personal tasks, can only assign to self
                if new_assignee_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Personal tasks can only be assigned to yourself"
                    )
    
    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user),
):
    task = db.exec(
        select(models.Task).where(
            models.Task.task_id == task_id,
            models.Task.is_deleted == False
        )
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="task not found"
        )
    
    # Check if user has permission to delete (owners and editors only for project tasks)
    if task.project_id:
        check_task_access(db, task, user_id, [
            models.ProjectRoleEnum.OWNER,
            models.ProjectRoleEnum.EDITOR
        ])
    else:
        check_task_access(db, task, user_id)
    
    task.is_deleted = True
    task.deleted_at = datetime.utcnow()
    db.commit()


@router.post("/tasks/{task_id}/restore", response_model=schemas.TaskResponse)
def restore_deleted_task(task_id : int, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    task = db.exec(
        select(models.Task).where(
            models.Task.task_id == task_id,
            models.Task.is_deleted == True
        )
    ).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="deleted task not found")
    
    # Check if user has permission to restore (owners and editors only for project tasks)
    if task.project_id:
        check_task_access(db, task, user_id, [
            models.ProjectRoleEnum.OWNER,
            models.ProjectRoleEnum.EDITOR
        ])
    else:
        check_task_access(db, task, user_id)
    
    task.is_deleted = False
    task.deleted_at = None
    db.commit()
    db.refresh(task)
    return task


# ==================== PROJECT TASKS ENDPOINT ====================

@router.get("/projects/{project_id}/tasks", response_model=list[schemas.TaskResponse])
def get_project_tasks(
    project_id: int,
    status: models.StatusEnum | None = None,
    priority: models.PriorityEnum | None = None,
    assignee_id: int | None = None,
    sort_by: SortBy | None = None,
    sort_order: SortOrder | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user)
):
    """Get all tasks for a specific project. User must be a project member."""
    # Verify user is a member of the project
    member = get_project_member(db, project_id, user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project"
        )
    
    # Verify project exists and is not deleted
    project = db.exec(
        select(models.Project).where(
            models.Project.project_id == project_id,
            models.Project.is_deleted == False
        )
    ).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Build query for tasks in this project
    statement = select(models.Task).where(
        models.Task.project_id == project_id,
        models.Task.is_deleted == False
    )
    
    # Apply filters
    if status:
        statement = statement.where(models.Task.status == status)
    if priority:
        statement = statement.where(models.Task.priority == priority)
    if assignee_id is not None:
        statement = statement.where(models.Task.assignee_id == assignee_id)
    
    # Apply sorting
    if sort_by:
        column = getattr(models.Task, sort_by.value)
        if sort_order == SortOrder.DESC:
            statement = statement.order_by(column.desc())
        else:
            statement = statement.order_by(column.asc())
    
    # Apply pagination
    statement = statement.offset(offset).limit(limit)
    
    tasks = db.exec(statement).all()
    return tasks


# ==================== TASK ASSIGNMENT ENDPOINTS ====================

@router.put("/tasks/{task_id}/assign", response_model=schemas.TaskResponse)
def assign_task(
    task_id: int,
    assignment: schemas.TaskAssignment,
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user)
):
    """
    Assign or unassign a task to a user.
    - For project tasks: assignee must be a project member
    - For personal tasks: can only assign to yourself
    - Set assignee_id to null to unassign
    """
    task = db.exec(
        select(models.Task).where(
            models.Task.task_id == task_id,
            models.Task.is_deleted == False
        )
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has permission to assign (owners and editors only for project tasks)
    if task.project_id:
        check_task_access(db, task, user_id, [
            models.ProjectRoleEnum.OWNER,
            models.ProjectRoleEnum.EDITOR
        ])
    else:
        check_task_access(db, task, user_id)
    
    # If assigning to someone
    if assignment.assignee_id is not None:
        # Verify assignee exists
        assignee = db.get(models.User, assignment.assignee_id)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee user not found"
            )
        
        # For project tasks, verify assignee is a project member
        if task.project_id:
            assignee_member = get_project_member(db, task.project_id, assignment.assignee_id)
            if not assignee_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee must be a member of the project"
                )
        else:
            # For personal tasks, can only assign to self
            if assignment.assignee_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Personal tasks can only be assigned to yourself"
                )
    
    # Update the assignment
    task.assignee_id = assignment.assignee_id
    task.updated_at = datetime.utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks/assigned-to-me", response_model=list[schemas.TaskResponse])
def get_my_assigned_tasks(
    status: models.StatusEnum | None = None,
    priority: models.PriorityEnum | None = None,
    project_id: int | None = None,
    sort_by: SortBy | None = None,
    sort_order: SortOrder | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user)
):
    """Get all tasks assigned to the current user."""
    # Get projects where user is a member
    accessible_project_ids = get_accessible_project_ids(db, user_id)
    
    # Build query for tasks assigned to current user
    from sqlalchemy import or_
    statement = select(models.Task).where(
        models.Task.is_deleted == False,
        models.Task.assignee_id == user_id
    ).where(
        or_(
            models.Task.user_id == user_id,
            models.Task.project_id.in_(accessible_project_ids)
        )
    )
    
    # Apply filters
    if project_id:
        if project_id not in accessible_project_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project"
            )
        statement = statement.where(models.Task.project_id == project_id)
    
    if status:
        statement = statement.where(models.Task.status == status)
    if priority:
        statement = statement.where(models.Task.priority == priority)
    
    # Apply sorting
    if sort_by:
        column = getattr(models.Task, sort_by.value)
        if sort_order == SortOrder.DESC:
            statement = statement.order_by(column.desc())
        else:
            statement = statement.order_by(column.asc())
    
    # Apply pagination
    statement = statement.offset(offset).limit(limit)
    
    tasks = db.exec(statement).all()
    return tasks


