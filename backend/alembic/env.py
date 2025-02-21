from __future__ import with_statement
import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the app folder to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

# Import settings from the Pydantic class
from app.config import settings  # Make sure the correct import path is used

# Alembic Config object
config = context.config

# Set the SQLAlchemy URL dynamically from Pydantic settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up logging
fileConfig(config.config_file_name)

# Create the target metadata
from app.sql_models.models import Base  # Make sure your Base is imported from models
target_metadata = Base.metadata

def run_migrations_online():
    # Connect to the database and run migrations
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
