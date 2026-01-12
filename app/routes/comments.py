from fastapi import APIRouter, status, Depends, HTTPException
from sqlmodel import Session, select
from .. import models, schemas, oauth2
from ..models import get_db
from datetime import datetime

router = APIRouter(tags=["comments"])

@router.post("/tasks/{task_id}/comments", status_code=status.HTTP_201_CREATED, response_model=schemas.CommentResponse)
def add_comment(task_id : int, comment_data : schemas.CommentCreate, db : Session = Depends(get_db), user_id = Depends(oauth2.get_current_user)):
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    new_comment = models.Comment(content=comment_data.content, user_id=user_id, task_id=task_id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

@router.get("/tasks/{task_id}/comments", response_model=list[schemas.CommentResponse])
def get_all_comments(task_id : int, db : Session = Depends(get_db), user_id = Depends(oauth2.get_current_user)):
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="task not found"
        )
    comments = db.exec(select(models.Comment).where(models.Comment.task_id == task_id).order_by(models.Comment.created_at)).all()
    return comments

@router.put("/tasks/{task_id}/comments/{comment_id}", response_model=schemas.CommentResponse)
def update_comment(task_id : int, comment_id : int, comment_data : schemas.CommentUpdate, db : Session = Depends(get_db), user_id = Depends(oauth2.get_current_user)):
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    comment = db.get(models.Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="comment not found")
    if comment.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not allowed to edit this comment")
    comment.content = comment_data.content
    comment.updated_at = datetime.utcnow()
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

@router.delete("/tasks/{task_id}/comments/{comment_id}")
def delete_comment(task_id : int, comment_id : int, db : Session = Depends(get_db), user_id = Depends(oauth2.get_current_user)):
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="task not found"
        )
    comment = db.get(models.Comment, comment_id)
    if not comment or comment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="comment not found"
        )
    db.delete(comment)
    db.commit()
    return {"message": "comment has been deleted succucfully"}
