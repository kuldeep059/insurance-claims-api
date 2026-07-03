import time
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Define where the SQLite database file will be saved
DATABASE_URL = "sqlite:///./insurance.db"

# 2. Create the Database Engine
# 'check_same_thread=False' is specific to SQLite so multiple API requests can read/write safely
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# 3. Create a Session Factory
# This creates a unique transaction worker (session) whenever a user hits our API
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create a Base Class for our Models
# All our database tables (Customer, Policy, Claim) will inherit from this class
Base = declarative_base()

# Track the server startup time so we can calculate system uptime later
START_TIME = time.time()

# 5. Dependency helper function
# This safely opens a database connection when an API request comes in,
# and automatically closes it when the request is done!
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()