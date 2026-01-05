from pydantic import BaseModel, EmailStr


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