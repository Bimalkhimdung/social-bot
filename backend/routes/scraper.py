"""Scraper control routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routes.auth import get_current_user
from scheduler import scheduler, _scraper_running

router = APIRouter(prefix="/api/scraper", tags=["scraper"])

_last_run_stats: dict = {}


@router.post("/run")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    """Manually trigger a scrape run in the background."""
    from scraper.engine import scrape_all_sources

    if _scraper_running:
        return {"message": "Scrape already running", "running": True}

    async def _run():
        global _last_run_stats
        async with db:
            _last_run_stats = await scrape_all_sources(db)

    background_tasks.add_task(_run)
    return {"message": "Scrape triggered", "running": True}


@router.get("/status")
async def scraper_status():
    return {
        "running": _scraper_running,
        "scheduler_running": scheduler.running,
        "last_run_stats": _last_run_stats,
        "jobs": [
            {
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in scheduler.get_jobs()
        ],
    }
