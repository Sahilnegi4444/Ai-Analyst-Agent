from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# #####################################################################
# Database Engine Initialization
# #####################################################################
# pool_pre_ping checks the connection health before yielding a session
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True,
    pool_size=2,
    max_overflow=0
)

# Session factory for generating local database transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy ORM models
Base = declarative_base()

# FastAPI Dependency injection function to retrieve database sessions
def get_db():
    """
    Yields a database session and guarantees safe closing upon context exit.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
