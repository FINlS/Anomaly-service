import os
import statistics
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .models import Anomaly, Visit
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv
maxMean = 3.0
HISTORY_HOURS = 168
minVisitors = 15
load_dotenv()

def evaluate(current: int, history: list[int]):
    mean = statistics.mean(history)
    std = statistics.pstdev(history)
    if std == 0:
        return current > mean and current > minVisitors, mean, std, None
    z = (current - mean) / std
    return z > maxMean and current > minVisitors, mean, std, z

def hourly_history(db: Session, hour_start: datetime) -> list[int]:
    start = hour_start - timedelta(hours=HISTORY_HOURS)
    hour = func.date_trunc("hour", Visit.ts)
    rows = db.execute(
        select(hour, func.count())
        .where(Visit.ts >= start, Visit.ts < hour_start)
        .group_by(hour)
    ).all()
    counts = {row[0]: row[1] for row in rows}
    return [counts.get(start + timedelta(hours=i), 0) for i in range(HISTORY_HOURS)]

def send_alert(detected_at, hour, visits, mean, z_score):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = [r.strip() for r in (os.getenv("EMAIL_RECEIVER") or "").split(",") if r.strip()]

    z_text = f"{z_score:.2f}" if z_score is not None else "н/д (std = 0)"
    body = (
        f"Обнаружена аномалия!\n"
        f"Время: {detected_at}\n"
        f"Час: {hour}\n"
        f"Текущие визиты: {visits}\n"
        f"Среднее: {mean:.2f}\n"
        f"Z-Score: {z_text}"
    )
    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = Header("Обнаружена аномалия", "utf-8")
    message["From"] = sender
    message["To"] = ", ".join(receiver)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, message.as_string())
        print("Письмо успешно отправлено!")
    except Exception as e:
        print(f"Ошибка при отправке: {e}")


def check_current_hour(db: Session) -> Anomaly | None:
    now = datetime.now(timezone.utc)
    hour_start = now.replace(minute=0, second=0, microsecond=0)

    current = db.scalar(
        select(func.count())
        .select_from(Visit)
        .where(Visit.ts >= hour_start, Visit.ts < hour_start + timedelta(hours=1))
    )
    history = hourly_history(db, hour_start)
    is_anomaly, mean, std, z = evaluate(current, history)

    if not is_anomaly:
        return None

    existing = db.scalar(select(Anomaly).where(Anomaly.hour == hour_start))
    if existing:
        existing.visits = current
        existing.mean = mean
        existing.std = std
        existing.z_score = z
        db.commit()
        return None

    anomaly = Anomaly(detected_at=now, hour=hour_start, visits=current,
                      mean=mean, std=std, z_score=z)
    db.add(anomaly)
    db.commit()
    return anomaly
