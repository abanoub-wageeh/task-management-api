from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlmodel import Session, select
import schemas
import models
import oauth2
from datetime import datetime
from enum import Enum

router = APIRouter(tags=["Tasks"])


@router.post(
    "/tasks", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED
)
def create_task(
    task_data: schemas.TaskCreate,
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user),
):
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
    sort_by: SortBy | None = None,
    sort_order : SortOrder | None = None,
    limit : int = Query(default=10, ge=1, le=100),
    offset : int = Query(default=0, ge=0),
    db: Session = Depends(models.get_db),
    user_id=Depends(oauth2.get_current_user),
):
    statement = select(models.Task).where(models.Task.user_id == user_id, models.Task.is_deleted == False)
    # filtering
    if status:
        statement = statement.where(models.Task.status == status)
    if priority:
        statement = statement.where(models.Task.priority == priority)
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
            models.Task.task_id == task_id, models.Task.user_id == user_id, models.Task.is_deleted == False
        )
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="task not found"
        )
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
            models.Task.task_id == task_id, models.Task.user_id == user_id, models.Task.is_deleted == False
        )
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="task not found"
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
            models.Task.task_id == task_id, models.Task.user_id == user_id, models.Task.is_deleted == False
        )
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="task not found"
        )
    task.is_deleted = True
    task.deleted_at = datetime.utcnow()
    db.commit()


@router.post("/tasks/{task_id}/restore", response_model=schemas.TaskResponse)
def restore_deleted_task(task_id : int, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    task = db.exec(select(models.Task).where(models.Task.task_id == task_id, models.Task.user_id == user_id, models.Task.is_deleted == True)).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="deleted task not found")
    task.is_deleted = False
    task.deleted_at = None
    db.commit()
    db.refresh(task)
    return task