from sqlalchemy import Column, Integer, BigInteger, Float, DateTime, String, func
from core.database import Base


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    weight_kg = Column(Float, nullable=True)
    chest_cm = Column(Float, nullable=True)
    waist_cm = Column(Float, nullable=True)
    hips_cm = Column(Float, nullable=True)
    biceps_left_cm = Column(Float, nullable=True)
    biceps_right_cm = Column(Float, nullable=True)
    thigh_left_cm = Column(Float, nullable=True)
    thigh_right_cm = Column(Float, nullable=True)
    neck_cm = Column(Float, nullable=True)
    bodyfat_pct = Column(Float, nullable=True)
    notes = Column(String(512), nullable=True)
    recorded_at = Column(DateTime, server_default=func.now())
