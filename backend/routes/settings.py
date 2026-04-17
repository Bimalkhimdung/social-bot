"""App settings routes (key-value store)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.settings import Setting
from routes.auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingItem(BaseModel):
    key: str
    value: str


@router.get("")
async def get_settings(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Setting))
    items = result.scalars().all()
    return {s.key: s.value for s in items}


@router.put("")
async def update_settings(
    body: list[SettingItem],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    for item in body:
        existing = await db.get(Setting, item.key)
        if existing:
            existing.value = item.value
        else:
            db.add(Setting(key=item.key, value=item.value))
    await db.commit()
    return {"updated": len(body)}
