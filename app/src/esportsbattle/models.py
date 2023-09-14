from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class EsportsBattleRawData(Base):
    __tablename__ = "esportsbattle_raw_data"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    game: Mapped[str] = mapped_column(String(50), index=False)
    tour_name: Mapped[str] = mapped_column(String(100), index=False)
    date_utc: Mapped[datetime] = mapped_column(DateTime(), index=False)
    team_1: Mapped[str] = mapped_column(String(50), index=False)
    team_2: Mapped[str] = mapped_column(String(50), index=False)

    # __table_args__ = (
    #     PrimaryKeyConstraint(game, tour_name, date_utc, team_1, team_2),
    #     {},
    # )
