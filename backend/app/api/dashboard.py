from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import store_service as svc

router = APIRouter()


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return svc.dashboard_metrics(db)
