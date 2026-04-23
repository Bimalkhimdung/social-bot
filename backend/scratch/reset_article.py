
import asyncio
from sqlalchemy import select, delete
from database import AsyncSessionLocal
from models.article import Article
from models.post import Post

async def reset_one_article():
    async with AsyncSessionLocal() as db:
        # Get the latest article
        result = await db.execute(select(Article).order_by(Article.id.desc()).limit(1))
        article = result.scalar_one_or_none()
        
        if article:
            print(f"Deleting article: {article.title} (ID: {article.id})")
            # Delete associated post first (cascade would usually handle this, but let's be explicit)
            await db.execute(delete(Post).where(Post.article_id == article.id))
            # Delete article
            await db.execute(delete(Article).where(Article.id == article.id))
            await db.commit()
            print("Successfully deleted the latest article and its post.")
        else:
            print("No articles found to delete.")

if __name__ == "__main__":
    asyncio.run(reset_one_article())
