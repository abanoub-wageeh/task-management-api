from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlmodel import Session, select
from app import schemas, models
from .. import oauth2
from datetime import datetime
from enum import Enum


router = APIRouter(tags=["projects"])

@router.post("/projects", status_code=status.HTTP_201_CREATED ,response_model=schemas.ProjectResponse)
def create_project(project_data : schemas.ProjectCreate, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    new_project = models.Project(**project_data.model_dump(), owner_id=user_id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/projects", response_model=list[schemas.ProjectResponse])
def get_all_projects(status : models.ProjectStatusEnum | None = None, created_at = None, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    statement = select(models.Project).where(models.Project.owner_id == user_id, models.Project.is_deleted == False)
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
    project = db.exec(select(models.Project).where(models.Project.project_id == project_id, models.Project.owner_id == user_id, models.Project.is_deleted == False)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    return project

@router.put("/projects/{project_id}", response_model=schemas.ProjectResponse)
def update_project(project_id : int, project_data : schemas.ProjectUpdate, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    project = db.exec(select(models.Project).where(models.Project.project_id == project_id, models.Project.owner_id == user_id, models.Project.is_deleted == False)).first()
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
    project = db.exec(
        select(models.Project).where(
            models.Project.project_id == project_id,
            models.Project.owner_id == user_id,
            models.Project.is_deleted == False,
        )
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    project.is_deleted = True
    project.deleted_at = datetime.utcnow()
    db.commit()
