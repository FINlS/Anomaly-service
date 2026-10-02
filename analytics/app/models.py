from datetime import datetime
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Visit(Base):
    __tablename__ = "visits"
    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String)
    ip: Mapped[str] = mapped_column(String)
    user_agent: Mapped[str | None]
    country: Mapped[str | None]
    city: Mapped[str| None]
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(primary_key=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    hour: Mapped[datetime] = mapped_column(DateTime(timezone=True), unique=True)
    visits: Mapped[int]
    mean: Mapped[float]
    std: Mapped[float]
    z_score: Mapped[float | None]