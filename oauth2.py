from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

import jwt
from jwt import InvalidTokenError, ExpiredSignatureError

from datetime import datetime, timedelta


import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
ALGORITHM = os.getenv("ALGORITHM")
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_token(data : dict, expire_delta : timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expire_delta
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def create_access_token(data : dict):
    access_token = create_token({**data, "typ": "access"}, expire_delta=timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)))
    return access_token

def create_refresh_token(data : dict):
    refresh_token = create_token({**data, "typ": "refresh"}, expire_delta=timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS)))
    return refresh_token

def create_verification_token(data: dict):
    return create_token(
        {**data, "typ": "verify"}, expires_delta=timedelta(minutes=10)
    )

def create_reset_password_token(data : dict):
    return create_token({**data, "typ" : "verify"}, expire_delta=timedelta(minutes=10))

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id"), payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token has been expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="unauthorized access")


def verify_refresh_token(token: str):
    user_id, payload = decode_token(token)
    if payload.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="invalid token type")
    return user_id

def verify_account(token: str):
    user_id, payload = decode_token(token)
    if payload.get("typ") != "verify":
        raise HTTPException(status_code=401, detail="invalid token type")
    return user_id


def get_current_user(token: str = Depends(oauth2_scheme)):
    user_id, payload = decode_token(token)
    if payload.get("typ") != "access":
        raise HTTPException(status_code=401, detail="invalid token type")
    return user_id
