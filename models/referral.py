from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, func
from core.database import Base


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(BigInteger, nullable=False, index=True)
    referee_id = Column(BigInteger, nullable=False, unique=True)
    code = Column(String(32), nullable=False, index=True)
    rewarded = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
