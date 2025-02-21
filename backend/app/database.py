from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import urllib.parse

def create_db_engine():
    # Create connection parameters
    params = {
        'host': settings.db_host,
        'port': settings.db_port,
        'database': settings.db_name,
        'user': settings.db_user,
        'password': urllib.parse.quote_plus(settings.db_password)  # URL encode the password
    }
    
    # Construct URL with encoded parameters
    url = f"postgresql://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
    
    # Create engine with explicit parameters
    return create_engine(
        url,
        pool_pre_ping=True,
        echo=True,
        connect_args={
            'client_encoding': 'utf8',
            'options': '-c timezone=utc'
        }
    )

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def recreate_tables():
    """Recreate all database tables"""
    try:
        # First try to create the database if it doesn't exist
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error recreating tables: {e}")
        raise