import asyncio
import json
from database import AsyncSessionLocal
from models.source import Source
from scraper.engine import scrape_source
from sqlalchemy import select

async def test_scrape():
    async with AsyncSessionLocal() as db:
        url = "https://bajarkochirfar.com/news-nepse/stockmarket"
        result = await db.execute(select(Source).where(Source.url == url))
        source = result.scalar_one_or_none()
        
        if not source:
            print(f"Source {url} not found.")
            return

        print(f"Starting test scrape for {source.name}...")
        stats = await scrape_source(source, db)
        print(f"Scrape results: {stats}")

if __name__ == "__main__":
    asyncio.run(test_scrape())
