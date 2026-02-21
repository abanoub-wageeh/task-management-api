from sqlmodel import SQLModel, create_engine, Field, Session
from pydantic import EmailStr
from datetime import datetime
from enum import Enum
from app.config import settings

class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class StatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS  = "in progress"
    COMPLETED = "completed"


class User(SQLModel, table=True):
    __tablename__ = "users"

    user_id : int | None = Field(default=None, primary_key=True)
    name : str = Field(..., min_length=2, max_length=60)
    email : EmailStr = Field(unique=True)
    password_hash : str
    refresh_token : str | None = Field(default=None)
    is_active : bool | None = Field(default=False) 
    created_at : datetime = Field(default_factory=datetime.utcnow)


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    task_id : int | None = Field(default=None, primary_key=True)
    title : str = Field(..., min_length=2, max_length=100)
    description : str = Field(..., min_length=15, max_length=500)
    priority : PriorityEnum = Field(default=PriorityEnum.LOW)
    status  :StatusEnum = Field(default=StatusEnum.PENDING)
    due_date : datetime | None = Field(default=None)
    created_at : datetime = Field(default_factory=datetime.utcnow)
    updated_at : datetime = Field(default_factory=datetime.utcnow)
    is_deleted : bool = Field(default=False)
    deleted_at : datetime | None = Field(default=None)

    user_id : int | None = Field(default=None, foreign_key="users.user_id")
    assignee_id : int | None = Field(default=None, foreign_key="users.user_id")
    project_id: int | None = Field(default=None, foreign_key="projects.project_id")

class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    comment_id : int | None = Field(default=None, primary_key=True)
    content : str = Field(..., min_length=2, max_length=500)
    created_at : datetime = Field(default_factory=datetime.utcnow)
    updated_at : datetime = Field(default_factory=datetime.utcnow)
    user_id : int | None = Field(default=None, foreign_key="users.user_id")
    task_id : int | None = Field(default=None, foreign_key="tasks.task_id")


engine = create_engine(settings.DATABASE_URL)

def get_db():
    with Session(engine) as db:
        yield db


class ProjectStatusEnum(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class ProjectRoleEnum(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    project_id: int | None = Field(default=None, primary_key=True)
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)

    status: ProjectStatusEnum = Field(default=ProjectStatusEnum.ACTIVE)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    is_deleted: bool = Field(default=False)
    deleted_at: datetime | None = Field(default=None)

    owner_id: int | None = Field(default=None, foreign_key="users.user_id")


class ProjectMember(SQLModel, table=True):
    __tablename__ = "project_members"

    member_id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.project_id")
    user_id: int = Field(foreign_key="users.user_id")
    role: ProjectRoleEnum = Field(default=ProjectRoleEnum.VIEWER)
    joined_at: datetime = Field(default_factory=datetime.utcnow)
