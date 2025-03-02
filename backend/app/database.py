from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import urllib.parse
import logging
import os

logger = logging.getLogger(__name__)

# Use settings consistently
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

def create_db_engine():
    """Create and configure the database engine with secure logging"""
    # Create connection parameters
    params = {
        'host': settings.db_host,
        'port': settings.db_port,
        'database': settings.db_name,
        'user': settings.db_user,
        'password': urllib.parse.quote_plus(settings.db_password)
    }
    
    # Log connection attempt with masked credentials
    logger.info(
        f"Connecting to database: host={params['host']}, "
        f"port={params['port']}, database={params['database']}, "
        f"user={'*' * len(params['user'])}"
    )
    
    # Create database URL
    url = f"postgresql://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
    
    return create_engine(
        url,
        pool_pre_ping=True,
        echo=False,  # Set to True for SQL query logging
        connect_args={
            'client_encoding': 'utf8',
            'options': '-c timezone=utc'
        }
    )

# Create engine and session factory
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for FastAPI routes to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def recreate_tables():
    """Drop and recreate all database tables - Use with caution!"""
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables recreated successfully")
    except Exception as e:
        logger.error(f"Error recreating database tables: {e}")
        raise