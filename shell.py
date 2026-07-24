# because i miss my Django shell
import code
from sqlalchemy import select
# NOTE: You need the actual SessionLocal class from database.py, not the get_db dependency
from database import Base, engine, SessionLocal  
import models

def start_shell():
    # ensure tables exist
    print("checking/creating database tables")
    Base.metadata.create_all(bind=engine)

    # 1. Create a database session
    db = SessionLocal()

    # 2. Define what you want available in the terminal without typing imports
    shell_context = {
        "db": db,
        "select": select,
        "models": models,
        "User": models.User,
        "Post": models.Post,
        "engine": engine,
        
    }

    print("🚀 FastAPI ORM Shell")
    print("Available objects: db, select, User, Post, models, engine")
    print("Type 'exit()' to quit.\n")

    try:
        # Try to use IPython if the user has it installed (pip install ipython)
        import IPython
        IPython.start_ipython(argv=[], user_ns=shell_context)
    except ImportError:
        # Fallback to the standard Python REPL if IPython is not installed
        code.interact(local=shell_context)
    finally:
        # Always close the database connection when the shell exits
        db.close()

if __name__ == "__main__":
    start_shell()