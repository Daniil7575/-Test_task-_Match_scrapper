from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from src.esportsbattle.schemas import SRawData
from src.database import get_async_session
from src.esportsbattle.service import apply_new_raw_data

router = APIRouter(prefix="/esportsbattle", tags=["EsportsBattle"])


@router.post("")
async def raw_data_insert(
    data: SRawData, session: AsyncSession = Depends(get_async_session)
):
    await apply_new_raw_data(data.data, session)
    return {
        "status": "success",
        "data": None,
        "details": "Info updated!",
    }
