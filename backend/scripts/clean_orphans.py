import asyncio
from sqlalchemy import text
from src.core.database import create_database_engine

async def clean_orphans():
    # Initialize engine
    await create_database_engine()
    
    # Import factory after initialization
    from src.core.database import AsyncSessionLocal
    
    print("Cleaning orphan paragraphs...")
    async with AsyncSessionLocal() as session:
        # Check for orphans
        result = await session.execute(text("SELECT COUNT(*) FROM paragraphs WHERE chapter_id NOT IN (SELECT id FROM chapters)"))
        count = result.scalar()
        print(f"Found {count} orphan paragraphs.")
        
        if count > 0:
            await session.execute(text("DELETE FROM paragraphs WHERE chapter_id NOT IN (SELECT id FROM chapters)"))
            await session.commit()
            print("Orphans deleted.")
        else:
            print("No orphans found.")

if __name__ == "__main__":
    asyncio.run(clean_orphans())
