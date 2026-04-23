
import asyncio
import logging
from database import AsyncSessionLocal
from scraper.engine import scrape_all_sources

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nepsebot")

async def test_scrape():
    async with AsyncSessionLocal() as db:
        print("Starting manual scrape test...")
        results = await scrape_all_sources(db)
        print(f"Scrape completed: {results}")

if __name__ == "__main__":
    asyncio.run(test_scrape())
