
import asyncio
from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import get_settings
from models.settings import Setting

async def update_settings():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Update telegram_enabled to true
        stmt = (
            update(Setting)
            .where(Setting.key == "telegram_enabled")
            .values(value="true")
        )
        await session.execute(stmt)
        await session.commit()
        print("Updated telegram_enabled to true.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(update_settings())
