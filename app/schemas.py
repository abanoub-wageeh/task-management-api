from pydantic import BaseModel, EmailStr, Field
import models
from datetime import datetime

class UserCreate(BaseModel):
    name : str
    email : EmailStr
    password : str


class UserLogin(BaseModel):
    email : EmailStr
    password : str

class PasswordReset(BaseModel):
    old_password : str
    new_password : str
    new_password_conform : str


class EmailSend(BaseModel):
    email : EmailStr


class PasswordForget(BaseModel):
    new_password : str = Field(..., min_length=8)
    new_password_conform : str = Field(..., min_length=8)



class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=15, max_length=500)
    priority: models.PriorityEnum = Field(default=models.PriorityEnum.LOW)
    status: models.StatusEnum = Field(default=models.StatusEnum.PENDING)
    due_date: models.datetime | None = Field(default=None)

class TaskResponse(BaseModel):
    title : str
    description : str
    status : str
    priority : str
    due_date : datetime
    created_at : datetime

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, min_length=15, max_length=500)
    priority: models.PriorityEnum | None = Field(default=None)
    status: models.StatusEnum | None = Field(default=None)
    due_date: models.datetime | None = Field(default=None)