import asyncio
import sys
import os
import logging
from sqlalchemy import inspect

# add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
# import models to register with base
from app.models.company import Company
from app.models.allocation import User, Allocation 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_pipeline_db():
    logger.info("starting database initialization...")
    
    try:
        async with engine.begin() as conn:
            # check existing tables
            def check_tables(connection):
                inspector = inspect(connection)
                return inspector.get_table_names()
            
            existing_tables = await conn.run_sync(check_tables)
            logger.info(f"existing tables: {existing_tables}")
            
            # create tables safely (skips existing)
            logger.info("running create_all (safe mode)...")
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("database verification/initialization completed!")
        
    except Exception as e:
        logger.error(f"initialization failed: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(init_pipeline_db())
