from sqlalchemy import BigInteger, String, Date, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from zoneinfo import ZoneInfo
from database.base import Base
import enum


class MoodPeriod(str, enum.Enum):
    MORNING = "morning"
    EVENING = "evening"
    CANDIDATE = "candidate"


class AIZone(str, enum.Enum):
    GREEN = "green"
    ORANGE = "orange"
    RED = "red"


class MoodLog(Base):
    __tablename__ = "mood_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # candidate or employee
    reaction: Mapped[str] = mapped_column(String(10), nullable=False)
    period: Mapped[MoodPeriod] = mapped_column(Enum(MoodPeriod), nullable=False)
    date: Mapped[date] = mapped_column(Date, default=lambda: datetime.now(ZoneInfo("Europe/Moscow")).date())
    time: Mapped[str] = mapped_column(String(5), default=lambda: datetime.now(ZoneInfo("Europe/Moscow")).strftime("%H:%M"))
    note: Mapped[str] = mapped_column(Text, nullable=True)
    ai_zone: Mapped[AIZone | None] = mapped_column(Enum(AIZone), nullable=True)
    ai_recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Europe/Moscow")))

    user: Mapped["User"] = relationship("User", back_populates="mood_logs")
