import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from src.esportsbattle.models import EsportsBattleRawData
from src import settings
import pytz
from datetime import datetime


async def apply_new_raw_data(data: dict, session: AsyncSession):
    local = pytz.timezone(settings.TIMEZONE)
    stmt = sa.delete(EsportsBattleRawData).where(
        EsportsBattleRawData.game == list(data.keys())[0]
    )
    await session.execute(stmt)

    for game_name, tours in data.items():
        for tour_name, matches in tours.items():
            for match_ in matches:
                # Convert data from scrapped timezone to utc
                naive = datetime.strptime(match_["date"], "%Y/%m/%d %H:%M")
                local_dt = local.localize(naive, is_dst=None)
                date_utc = local_dt.astimezone(pytz.utc)
                date_utc = datetime.strptime(
                    date_utc.strftime("%Y/%m/%d %H:%M"), "%Y/%m/%d %H:%M"
                )

                data = EsportsBattleRawData(
                    game=game_name,
                    tour_name=tour_name,
                    date_utc=date_utc,
                    team_1=match_["team_1"],
                    team_2=match_["team_2"],
                )
                session.add(data)
    await session.commit()
