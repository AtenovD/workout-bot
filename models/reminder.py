from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Time, DateTime, func
from core.db import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    type = Column(String(32), nullable=False)  # workout, weekly_report, motivation
    time_of_day = Column(Time, nullable=False)
    days_of_week = Column(String(32), default="1,2,3,4,5,6,7")  # comma-sep 1=mon..7=sun
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
