from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

#databse url 
SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"

#db engine configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# create a db session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    ...

def get_db():
    with SessionLocal() as db:
        yield db
