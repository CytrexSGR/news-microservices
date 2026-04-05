"""
Celery tasks for background processing
"""
import logging
from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.indexing_service import IndexingService
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(name='app.workers.tasks.sync_articles_task', bind=True)
def sync_articles_task(self):
    """
    Sync articles from Feed Service (periodic task).

    This task runs every 5 minutes to index new articles.
    """
    import asyncio

    async def _sync():
        async with AsyncSessionLocal() as db:
            service = IndexingService(db)
            return await service.sync_articles(batch_size=settings.BATCH_SIZE)

    try:
        logger.info("Starting article sync task...")
        result = asyncio.run(_sync())
        logger.info(f"Article sync complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in article sync task: {e}")
        raise


@celery_app.task(name='app.workers.tasks.index_article_task', bind=True)
def index_article_task(self, article_data: dict):
    """
    Index a single article.

    Args:
        article_data: Article data to index
    """
    import asyncio

    async def _index():
        async with AsyncSessionLocal() as db:
            service = IndexingService(db)
            return await service.index_article(article_data)

    try:
        logger.info(f"Indexing article: {article_data.get('id')}")
        result = asyncio.run(_index())
        logger.info(f"Article indexed successfully: {article_data.get('id')}")
        return str(result.id)
    except Exception as e:
        logger.error(f"Error indexing article {article_data.get('id')}: {e}")
        raise


@celery_app.task(name='app.workers.tasks.reindex_all_task', bind=True)
def reindex_all_task(self):
    """
    Reindex all articles (manual trigger).

    This is a long-running task that reindexes all articles.
    """
    import asyncio

    async def _reindex():
        async with AsyncSessionLocal() as db:
            service = IndexingService(db)
            return await service.reindex_all()

    try:
        logger.info("Starting full reindex...")
        result = asyncio.run(_reindex())
        logger.info(f"Full reindex complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in full reindex: {e}")
        raise
