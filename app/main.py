import io
import time
import pandas as pd
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import database configuration blocks
from app.database import Base, engine, get_db, START_TIME
# Import specific endpoint routers
from app.routers import claims, reports
# Import backend calculation service
from app.services.upload_service import process_upload_pipeline

# 1. Instruct SQLAlchemy to generate SQLite tables if they do not exist
Base.metadata.create_all(bind=engine)

# 2. Instantiate the FastAPI Core Engine
app = FastAPI(
    title="Production Claims Processing Engine",
    description="Automated structural intake validation and payout evaluation services.",
    version="1.0.0"
)

# 3. Mount individual functional sub-routers
app.include_router(claims.router)
app.include_router(reports.router)

@app.get("/health", tags=["Infrastructure Monitors"])
def health_check(db: Session = Depends(get_db)):
    """
    Verifies API status, active database pipeline connectivity, and system uptime.
    """
    try:
        # Run a micro-query to verify the database connection is alive
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # Calculate system uptime since server initialization
    uptime_seconds = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m"

    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "uptime": uptime_str
    }

@app.post("/upload", tags=["Data Processing Hub"])
async def upload_data_files(
    customer_file: UploadFile = File(...),
    policy_file: UploadFile = File(...),
    claims_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts three attachments (CSV or Excel formats), reads them into DataFrames,
    and runs them through the data validation and business rules pipeline.
    """
    
    # Helper utility to read attachments into DataFrames based on their extension
    def read_to_df(file: UploadFile, content: bytes) -> pd.DataFrame:
        filename = file.filename.lower()
        if filename.endswith('.csv'):
            return pd.read_csv(io.BytesIO(content))
        elif filename.endswith(('.xlsx', '.xls')):
            return pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format for '{file.filename}'. Please provide a valid CSV or Excel file."
            )

    # Stream file contents asynchronously into memory buffers
    cust_bytes = await customer_file.read()
    poly_bytes = await policy_file.read()
    clam_bytes = await claims_file.read()

    # Convert binary blobs to Pandas DataFrames
    try:
        df_cust = read_to_df(customer_file, cust_bytes)
        df_poly = read_to_df(policy_file, poly_bytes)
        df_clam = read_to_df(claims_file, clam_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file structure: {str(e)}")

    # Forward the DataFrames directly down into our ingestion execution pipeline
    summary = process_upload_pipeline(df_cust, df_poly, df_clam, db)
    return summary