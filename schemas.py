from pydantic import BaseModel, EmailStr, Field


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
