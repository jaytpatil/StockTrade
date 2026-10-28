from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, auth
from database import get_db

router = APIRouter()

@router.get("/users")
def get_users(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin)):
    users = db.query(models.User).all()
    return [{"id": u.id, "email": u.email, "role": u.role} for u in users]

@router.delete("/delete-user/{id}")
def delete_user(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}
