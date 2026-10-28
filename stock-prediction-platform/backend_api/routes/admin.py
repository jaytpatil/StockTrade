from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
import models
import auth
from database import get_db

router = APIRouter()

# -------------------------------------------------------------
# Admin Dependency: Validates JWT ensuring current_user is ADMIN
# -------------------------------------------------------------
admin_dependency = Depends(auth.get_current_admin)

@router.get("/users", response_model=List[Dict[str, Any]])
def list_all_users(db: Session = Depends(get_db), admin: models.User = admin_dependency):
    """Admin API: Retrieves all registered platform users."""
    users = db.query(models.User).all()
    # Masking sensitive parameters while returning structural JSON
    return [{
        "id": u.id, 
        "email": u.email, 
        "role": u.role, 
        "is_blocked": getattr(u, 'is_blocked', False),
        "created_at": u.created_at
    } for u in users]

@router.patch("/users/{user_id}/toggle-block")
def toggle_user_block(user_id: int, db: Session = Depends(get_db), admin: models.User = admin_dependency):
    """Admin API: Flips a User's block status (preventing JWT issuance)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Admins cannot block themselves.")
        
    user.is_blocked = not getattr(user, 'is_blocked', False)
    
    # Audit Logging
    audit_action = models.AdminAction(
        admin_id=admin.id, 
        action_type="USER_BLOCKED" if user.is_blocked else "USER_UNBLOCKED",
        target_entity_id=str(user.id)
    )
    db.add(audit_action)
    db.commit()
    return {"message": f"User {user.email} block status updated to: {user.is_blocked}"}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: models.User = admin_dependency):
    """Admin API: Permanently deletes a User and cleanly cascades DB relations."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    email = user.email
    db.delete(user)
    
    # Audit Logging
    audit_action = models.AdminAction(
        admin_id=admin.id, action_type="USER_DELETED", target_entity_id=str(user_id)
    )
    db.add(audit_action)
    db.commit()
    return {"message": f"User {email} has been permanently deleted."}

@router.get("/prediction-logs", response_model=List[Dict[str, Any]])
def view_prediction_logs(limit: int = 50, db: Session = Depends(get_db), admin: models.User = admin_dependency):
    """Admin API: Audits recent Machine Learning executions parsing chronological PredictionResult rows."""
    logs = db.query(models.PredictionResult).order_by(desc(models.PredictionResult.created_at)).limit(limit).all()
    return [{
        "id": log.id,
        "stock_id": log.stock_id,
        "target_date": log.target_date,
        "predicted_price": log.predicted_price,
        "model_engine": log.model_version,
        "execution_timestamp": log.created_at
    } for log in logs]

@router.get("/metrics/top-searched-stocks")
def view_top_searched_stocks(db: Session = Depends(get_db), admin: models.User = admin_dependency):
    """
    Admin API: Ranks Stocks by platform popularity.
    (Currently proxies popularity via counting user Watchlist associations)
    """
    popular_stocks = (
        db.query(models.Stock.symbol, func.count(models.Watchlist.id).label('popularity_score'))
        .join(models.Watchlist, models.Stock.id == models.Watchlist.stock_id)
        .group_by(models.Stock.symbol)
        .order_by(desc('popularity_score'))
        .limit(10)
        .all()
    )
    
    return [
        {"symbol": s.symbol, "popularity_score": s.popularity_score} 
        for s in popular_stocks
    ]
