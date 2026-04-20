
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import get_settings
from models.settings import Setting

async def check_settings():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Setting))
        items = result.scalars().all()
        print("Database Settings:")
        for item in items:
            print(f"{item.key}: {item.value}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_settings())
