"""Alembic environment configuration for News MCP microservices.

This env.py file manages migrations for all services in a centralized manner.
It imports all models from the database/models/ directory and detects schema changes.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add parent directory to path to import models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import base metadata from models
# This will import ALL models from news-mcp/app/models/
try:
    from news_mcp.app.models.base import Base as MCPBase
    target_metadata = MCPBase.metadata
except ImportError:
    # Fallback if news-mcp models not available
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    target_metadata = Base.metadata
    print("WARNING: Could not import news-mcp models. Using empty metadata.")

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Allow database URL override from environment
database_url = os.environ.get('ALEMBIC_DATABASE_URL')
if database_url:
    config.set_main_option('sqlalchemy.url', database_url)


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter which objects should be considered by Alembic autogenerate.

    Returns True if the object should be included, False otherwise.
    """
    # Always include indexes and constraints
    if type_ == "index":
        return True
    if type_ == "unique_constraint":
        return True
    if type_ == "foreign_key_constraint":
        return True

    # Exclude tables that start with underscore (temporary/internal)
    if type_ == "table" and name.startswith('_'):
        return False

    # Include everything else
    return True


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    # Build connection configuration
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = config.get_main_option("sqlalchemy.url")

    # Create engine with connection pooling
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No connection pooling for migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
            compare_server_default=True,
            # Transaction per migration (recommended for PostgreSQL)
            transaction_per_migration=True,
            # Version table configuration
            version_table='alembic_version',
            # Include schemas if using schema separation
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
