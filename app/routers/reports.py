from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="", tags=["Analytical Reports"])

@router.get("/customers/top")
def get_top_customers(n: int = 10, db: Session = Depends(get_db)):
    """
    [Raw SQL Query 1] Fetch the top N customers with the highest total insurance payouts.
    """
    raw_sql = text("""
        SELECT c.id, c.name, SUM(cl.final_payout) as total_payout
        FROM customers c
        JOIN policies p ON c.id = p.customer_id
        JOIN claims cl ON p.id = cl.policy_id
        GROUP BY c.id, c.name
        ORDER BY total_payout DESC
        LIMIT :limit
    """)
    
    result = db.execute(raw_sql, {"limit": n}).fetchall()
    
    # Map raw tuple rows into a clean JSON structure
    return [
        {
            "customer_id": row[0], 
            "name": row[1], 
            "total_payout": round(row[2], 2) if row[2] else 0.0
        } 
        for row in result
    ]

@router.get("/reports/state")
def get_state_report(db: Session = Depends(get_db)):
    """
    [Raw SQL Query 2] Generates a complete state-by-state geographic performance distribution report.
    """
    raw_sql = text("""
        SELECT c.state, 
               COUNT(cl.id) as total_claims,
               AVG(cl.final_payout) as average_payout,
               MAX(cl.final_payout) as max_payout,
               SUM(cl.final_payout) as total_payout
        FROM customers c
        JOIN policies p ON c.id = p.customer_id
        JOIN claims cl ON p.id = cl.policy_id
        GROUP BY c.state
        ORDER BY total_payout DESC
    """)
    
    result = db.execute(raw_sql).fetchall()
    
    return [
        {
            "state": row[0], 
            "total_claims": row[1],
            "average_payout": round(row[2], 2) if row[2] else 0.0,
            "max_payout": round(row[3], 2) if row[3] else 0.0,
            "total_payout": round(row[4], 2) if row[4] else 0.0
        } 
        for row in result
    ]