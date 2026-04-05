"""FastAPI dependencies for dependency injection."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings
from app.services.wikidata_client import WikidataClient
from app.services.embedding_service import EmbeddingService
from app.services.fuzzy_matcher import FuzzyMatcher
from app.services.alias_store import AliasStore
from app.services.canonicalizer import EntityCanonicalizer

# Database engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Global instances (singleton pattern)
_wikidata_client: WikidataClient = None
_embedding_service: EmbeddingService = None
_fuzzy_matcher: FuzzyMatcher = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_wikidata_client() -> WikidataClient:
    """Get Wikidata client (singleton)."""
    global _wikidata_client
    if _wikidata_client is None:
        _wikidata_client = WikidataClient()
    return _wikidata_client


def get_embedding_service() -> EmbeddingService:
    """Get embedding service (singleton)."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_fuzzy_matcher() -> FuzzyMatcher:
    """Get fuzzy matcher (singleton)."""
    global _fuzzy_matcher
    if _fuzzy_matcher is None:
        _fuzzy_matcher = FuzzyMatcher()
    return _fuzzy_matcher


async def get_alias_store(
    session: AsyncSession = None
) -> AliasStore:
    """Get alias store with database session."""
    if session is None:
        async with AsyncSessionLocal() as session:
            return AliasStore(session)
    return AliasStore(session)


async def get_canonicalizer(
    session: AsyncSession = None
) -> EntityCanonicalizer:
    """Get entity canonicalizer with all dependencies."""
    alias_store = await get_alias_store(session)
    wikidata_client = get_wikidata_client()
    embedding_service = get_embedding_service()
    fuzzy_matcher = get_fuzzy_matcher()

    return EntityCanonicalizer(
        alias_store=alias_store,
        wikidata_client=wikidata_client,
        embedding_service=embedding_service,
        fuzzy_matcher=fuzzy_matcher
    )
