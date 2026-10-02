from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select, desc
from .db import getDb
from .geo import lookup_ip
from .schemas import TrackIn
from .models import Anomaly, Visit
from fastapi import APIRouter, BackgroundTasks, Depends
from .anomaly import check_current_hour, send_alert
router = APIRouter()

@router.post("/track", status_code=201)
def track(data: TrackIn, background: BackgroundTasks, db: Session = Depends(getDb)):
    geo = lookup_ip(str(data.ip))
    visit = Visit(
        page_id=data.page_id, user_id=data.user_id, ip=str(data.ip),
        user_agent=data.user_agent, ts=data.timestamp, **geo,
    )
    db.add(visit)
    db.commit()

    anomaly = check_current_hour(db)
    if anomaly:
        background.add_task(send_alert, anomaly.detected_at, anomaly.hour,
                            anomaly.visits, anomaly.mean, anomaly.z_score)
    return {"status": "ok"}

@router.get("/reports/popular_pages")
def popular_pages(db: Session = Depends(getDb)):
    since = datetime.now(timezone.utc)-timedelta(days=1)
    rows = db.execute(
        select(
            Visit.page_id,
            func.count().label("visits"),
            func.count(func.distinct(Visit.user_id)).label("uniqueUsers"),
        ).where(Visit.ts >=since)
        .group_by(Visit.page_id)
        .order_by(func.count().desc())
        .limit(5)
    ).all()
    return [{"page_id": r.page_id, "visits": r.visits, "uniqueUsers": r.uniqueUsers} for r in rows]

@router.get("/reports/geo_stats")
def geo_stats(db: Session = Depends(getDb)):
    since = datetime.now(timezone.utc)-timedelta(days=7)
    rows = db.execute(
        select(
            Visit.country,
            func.count().label("visits"),
            func.count(func.distinct(Visit.user_id)).label("uniqueUsers"),
        ).where(Visit.ts >= since)
        .group_by(Visit.country)
        .order_by(func.count().desc())
    ).all()
    return [{"country": r.country, "visits": r.visits, "uniqueUsers": r.uniqueUsers} for r in rows]

@router.get("/reports/anomalies")
def anomalies(db: Session = Depends(getDb)):
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    rows = db.scalars(
        select(Anomaly)
        .where(Anomaly.detected_at >= since)
        .order_by(Anomaly.detected_at.desc())
    ).all()
    return [
        {
            "hour": a.hour,
            "detected_at": a.detected_at,
            "visits": a.visits,
            "mean": round(a.mean, 2),
            "z_score": round(a.z_score, 2) if a.z_score is not None else None,
        }
        for a in rows
    ]