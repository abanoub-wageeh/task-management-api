from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session, select
import schemas
import models
import oauth2
from datetime import datetime

router = APIRouter(tags=["Tasks"])

@router.post("/tasks", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_data : schemas.TaskCreate, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    new_task = models.Task(**task_data.model_dump(exclude_unset=True))
    new_task.user_id = user_id
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.get("/tasks", response_model=list[schemas.TaskResponse])
def get_all_tasks(db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    tasks = db.exec(select(models.Task).where(models.Task.user_id == user_id)).all()
    return tasks

@router.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_a_task(task_id : int, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    task = db.exec(select(models.Task).where(models.Task.task_id == task_id, models.Task.user_id == user_id)).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return task

@router.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id : int, task_data : schemas.TaskUpdate, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    task = db.exec(select(models.Task).where(models.Task.task_id == task_id, models.Task.user_id == user_id)).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id : int, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    task = db.exec(select(models.Task).where(models.Task.task_id == task_id, models.Task.user_id == user_id)).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    db.delete(task)
    db.commit()
    return {"message": "the task has been deleted successfully"}