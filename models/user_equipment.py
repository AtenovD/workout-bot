from sqlalchemy import BigInteger, Boolean, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base


class UserEquipment(Base):
    __tablename__ = "user_equipment"
    __table_args__ = (UniqueConstraint("user_id", "equipment_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    equipment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("equipment.id"))
    has_it: Mapped[bool] = mapped_column(Boolean, default=True)
    added_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
