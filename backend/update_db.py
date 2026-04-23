import asyncio
from sqlalchemy import text
from database import AsyncSessionLocal

async def update_db():
    print("🚀 Updating database schema...")
    async with AsyncSessionLocal() as db:
        try:
            # Add the missing column to the posts table
            await db.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS is_auto_approved BOOLEAN DEFAULT FALSE"))
            await db.commit()
            print("✅ Successfully added 'is_auto_approved' column to 'posts' table.")
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(update_db())
