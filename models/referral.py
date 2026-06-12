from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, func
from core.database import Base


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inviter_id = Column(BigInteger, nullable=False, index=True)
    invitee_id = Column(BigInteger, nullable=False, unique=True)
    bonus_granted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
