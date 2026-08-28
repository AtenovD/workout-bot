from sqlalchemy import BigInteger, Numeric, Date, String, JSON, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    date: Mapped[Date] = mapped_column(Date)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    body_fat_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    measurements: Mapped[dict | None] = mapped_column(JSON)  # chest/waist/hips/arms...
    photo_url: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
