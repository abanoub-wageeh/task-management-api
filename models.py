from sqlmodel import SQLModel, create_engine, Field
from pydantic import EmailStr
from datetime import datetime
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

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


engine = create_engine(os.getenv("DATABASE_URL"))