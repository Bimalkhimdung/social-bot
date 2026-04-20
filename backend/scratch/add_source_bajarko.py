import asyncio
import json
from database import AsyncSessionLocal
from models.source import Source
from sqlalchemy import select

async def add_source():
    async with AsyncSessionLocal() as db:
        # Check if already exists
        url = "https://bajarkochirfar.com/news-nepse/stockmarket"
        result = await db.execute(select(Source).where(Source.url == url))
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Source {url} already exists.")
            return

        new_source = Source(
            name="BAJARKO CHIRFAR",
            url=url,
            source_type="html",
            is_active=True,
            selector_config=json.dumps({
                "title_selector": "h2 a, h3 a",
                "link_attr": "href",
                "image_selector": "img",
                "image_attr": "data-src",
                "base_url": "https://bajarkochirfar.com"
            })
        )
        db.add(new_source)
        await db.commit()
        print("Source 'BAJARKO CHIRFAR' added successfully.")

if __name__ == "__main__":
    asyncio.run(add_source())
