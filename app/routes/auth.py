from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app import models, schemas
from .. import utils, oauth2
router = APIRouter(tags=["authorization"])


@router.post("/register")
def create_account(user_data : schemas.UserCreate, db : Session = Depends(models.get_db)):
    user = db.exec(select(models.User).where(models.User.email == user_data.email)).first()
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user already exist, login to your account")
    hashed_password = utils.hash_password(user_data.password)
    new_user = models.User(**user_data.model_dump(exclude_unset=True))
    new_user.password_hash = hashed_password
    db.add(new_user)
    db.commit()
    token = oauth2.create_verification_token({"user_id": new_user.user_id})
    utils.send_verification_email(new_user.email, token)
    return {"message": "user had been created successfully, check your email to verify your account"}


@router.get("/verify")
def verify_account(token : str, db : Session = Depends(models.get_db)):
    user_id = oauth2.verify_account(token)
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found, create an account")
    if user.is_active == True:
        return {"message": "user has been already verified"}
    user.is_active = True
    db.commit()
    return {"message": "your account has been verified successfully"}


@router.post("/login")
def login(user_data : schemas.UserLogin, db : Session = Depends(models.get_db)):
    user = db.exec(select(models.User).where(models.User.email == user_data.email)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found, create an account")
    if user.is_active == False:
        token = oauth2.create_access_token({"user_id": user.user_id})
        utils.send_verification_email(user.email, token)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="verify your account first, check your email to verify your account")
    if not utils.verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = oauth2.create_access_token({"user_id": user.user_id})
    refresh_token = oauth2.create_refresh_token({"user_id": user.user_id})
    user.refresh_token = refresh_token
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/refresh")
def create_new_access_token(token : str, db : Session = Depends(models.get_db)):
    user_id = oauth2.verify_refresh_token(token)
    user = db.get(models.User, user_id)
    if user.refresh_token != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    new_access_token = oauth2.create_access_token({"user_id": user_id})
    return {"access_token": new_access_token}

@router.put("/revoke")
def revoke_refresh_token(db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    user = db.get(models.User, user_id)
    user.refresh_token = None
    db.commit()
    return {"message": "refresh token has been revoked successfully"}


@router.post("/change_password")
def change_password(password_data : schemas.PasswordReset, db : Session = Depends(models.get_db), user_id = Depends(oauth2.get_current_user)):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found, create an account")
    if not utils.verify_password(password_data.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    if password_data.new_password != password_data.new_password_conform:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="passwords do not match")
    if len(password_data.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters")
    new_password = utils.hash_password(password_data.new_password)
    user.password_hash = new_password
    db.commit()
    return {"message": "password has been changed successfully"}

@router.post("/forget_password")
def forget_password(email : schemas.EmailSend, db : Session = Depends(models.get_db)):
    user = db.exec(select(models.User).where(models.User.email == email.email)).first()
    if user:
        utils.send_reset_password_email(receiver_email=user.email,reset_token = oauth2.create_reset_password_token({"user_id": user.user_id}))
    return {"message": "an email has been sent to you to reset your password"}


@router.post("/forget_password/reset")
def reset_password(token : str, password : schemas.PasswordForget, db : Session = Depends(models.get_db)):
    user_id = oauth2.verify_account(token)
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired token")
    if password.new_password != password.new_password_conform:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="password do not match")
    user.password_hash = utils.hash_password(password.new_password)
    db.commit()
    return {"message": "password has been reset successfully"}
