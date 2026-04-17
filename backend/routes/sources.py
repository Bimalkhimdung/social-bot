"""Sources CRUD + test-scrape endpoint."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.source import Source
from routes.auth import get_current_user

router = APIRouter(prefix="/api/sources", tags=["sources"])


# -- Schemas --

class SourceBase(BaseModel):
    name: str
    url: str
    source_type: str = "html"
    selector_config: dict = {}
    is_active: bool = True


class SourceCreate(SourceBase):
    pass


class SourceUpdate(SourceBase):
    pass


class SourceOut(SourceBase):
    id: int
    last_scraped_at: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


# -- Routes --

@router.get("", response_model=list[SourceOut])
async def list_sources(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Source).order_by(Source.created_at.desc()))
    sources = result.scalars().all()
    return [_to_out(s) for s in sources]


@router.post("", response_model=SourceOut, status_code=201)
async def create_source(
    body: SourceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    source = Source(
        name=body.name,
        url=body.url,
        source_type=body.source_type,
        selector_config=json.dumps(body.selector_config),
        is_active=body.is_active,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return _to_out(source)


@router.put("/{source_id}", response_model=SourceOut)
async def update_source(
    source_id: int,
    body: SourceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    source = await _get_or_404(source_id, db)
    source.name = body.name
    source.url = body.url
    source.source_type = body.source_type
    source.selector_config = json.dumps(body.selector_config)
    source.is_active = body.is_active
    await db.commit()
    await db.refresh(source)
    return _to_out(source)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    source = await _get_or_404(source_id, db)
    await db.delete(source)
    await db.commit()


@router.post("/{source_id}/test")
async def test_source(
    source_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    """Test-scrape a source and return a preview of up to 5 articles."""
    from scraper.engine import _scrape_html, _scrape_api
    import httpx

    source = await _get_or_404(source_id, db)
    async with httpx.AsyncClient() as client:
        if source.source_type == "api":
            items = await _scrape_api(source, client)
        else:
            items = await _scrape_html(source, client)

    return {"source": source.name, "found": len(items), "preview": items[:5]}


# -- Helpers --

async def _get_or_404(source_id: int, db: AsyncSession) -> Source:
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


def _to_out(s: Source) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "url": s.url,
        "source_type": s.source_type,
        "selector_config": s.selector_config_dict,
        "is_active": s.is_active,
        "last_scraped_at": s.last_scraped_at.isoformat() if s.last_scraped_at else None,
        "created_at": s.created_at.isoformat(),
    }
