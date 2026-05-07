"""Alembic migration environment configuration.

This module configures Alembic to work with our async SQLAlchemy models.
It loads models directly to avoid triggering the api package's complex imports.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Determine the apps/api directory path
script_dir = os.path.dirname(os.path.abspath(__file__))
apps_api_dir = os.path.dirname(script_dir)  # goes from alembic/ to api/
apps_dir = os.path.dirname(apps_api_dir)  # goes from api/ to apps/

# Ensure apps/ is in the path so 'api' can be found as a package
if apps_dir not in sys.path:
    sys.path.insert(0, apps_dir)

# Alembic Config object
config = context.config

# Load logging configuration from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import the Base from models.base directly using importlib
# This bypasses the api package's __init__.py which has complex router imports
import importlib.util

def import_file_to_module(name: str, path: str):
    """Import a Python file directly as a module."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Load models.base module
models_base_path = os.path.join(apps_api_dir, "models", "base.py")
models_base = import_file_to_module("api.models.base", models_base_path)
Base = models_base.Base

# Now we need to load all model files to register them with Base.metadata
# We'll import them one by one to avoid the api package's __init__.py
model_files = [
    "tenant", "person", "student", "teacher", "parent",
    "academic", "attendance", "gradebook", "scheduling",
    "fees", "lms", "communication", "ai"
]

for model_file in model_files:
    model_path = os.path.join(apps_api_dir, "models", f"{model_file}.py")
    if os.path.exists(model_path):
        import_file_to_module(f"api.models.{model_file}", model_path)

# Get the models module's __init__ to get the list of all models
# But we'll get it without triggering the full init
models_init_path = os.path.join(apps_api_dir, "models", "__init__.py")

# Read the __all__ from models/__init__.py to get the list of model names
with open(models_init_path, 'r') as f:
    content = f.read()

# Extract __all__ list
import re
all_match = re.search(r'__all__\s*=\s*\[(.*?)\]', content, re.DOTALL)
if all_match:
    all_models = re.findall(r'"(\w+)"', all_match.group(1))
    # Add Base and TimestampMixin to the exported names
    all_models = ["Base", "TimestampMixin"] + all_models

# Target metadata for autogenerate support
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from config or environment."""
    # Try to get from alembic config section first
    url = config.get_main_option("sqlalchemy.url")
    if url is None:
        # Fallback to environment variable
        url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/sis"
        )
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with an active connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode using async engine."""
    # Get database URL
    url = get_url()

    # Set the URL in config so async_engine_from_config can use it
    config.set_main_option("sqlalchemy.url", url)

    # Create async engine using alembic's config
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        echo=False,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine."""
    import asyncio
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
