from sqlalchemy import Column, BigInteger, Date, Numeric, ForeignKey, DateTime, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from core.db import Base


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    weight_kg = Column(Numeric(5, 2))
    body_fat_pct = Column(Numeric(5, 2))
    measurements = Column(JSON)
    photo_url = Column(String(512))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
