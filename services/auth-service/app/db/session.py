"""
Database session management and initialization.
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings
from app.models.auth import Base
import logging

logger = logging.getLogger(__name__)

# Create database engine
# Note: Use psycopg2 (postgresql://) for synchronous operations, not asyncpg
database_url = settings.get_database_url()
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(
    database_url,
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
    connect_args={
        "connect_timeout": 60,  # Connection timeout (psycopg2 parameter)
        "options": "-c statement_timeout=30000"  # 30 second query timeout
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency function to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database by creating all tables.
    Also creates default roles if they don't exist.
    """
    from app.models.auth import Role
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    
    # Create default roles
    db = SessionLocal()
    try:
        default_roles = [
            {"name": "admin", "description": "Administrator with full access"},
            {"name": "user", "description": "Regular user with basic access"},
            {"name": "moderator", "description": "Moderator with content management access"},
        ]
        
        for role_data in default_roles:
            existing_role = db.query(Role).filter_by(name=role_data["name"]).first()
            if not existing_role:
                role = Role(**role_data)
                db.add(role)
                logger.info(f"Created default role: {role_data['name']}")
        
        db.commit()
        logger.info("Default roles initialized")
    except Exception as e:
        logger.error(f"Error initializing default roles: {e}")
        db.rollback()
    finally:
        db.close()


def check_db_connection(max_retries=5, retry_delay=2):
    """
    Check if database connection is working with retry logic.

    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Delay between retries in seconds

    Returns:
        True if connection is working, False otherwise
    """
    import time

    for attempt in range(1, max_retries + 1):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            logger.info(f"Database connection successful (attempt {attempt}/{max_retries})")
            return True
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"Database connection failed (attempt {attempt}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                return False

    return False
