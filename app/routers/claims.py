from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.claim import Claim
from app.models.policy import Policy
from app.models.customer import Customer

router = APIRouter(prefix="/claims", tags=["Claims Extraction"])

@router.get("/{claim_id}")
def get_claim_details(claim_id: str, db: Session = Depends(get_db)):
    """
    Fetch comprehensive structural details for a single claim, 
    including linked customer and policy information.
    """
    # Join all three tables together using foreign keys
    result = db.query(Claim, Policy, Customer).\
        join(Policy, Claim.policy_id == Policy.id).\
        join(Customer, Policy.customer_id == Customer.id).\
        filter(Claim.id == claim_id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Claim ID tracking record not found")
    
    claim, policy, customer = result
    return {
        "claim_information": {
            "id": claim.id, 
            "loss_date": claim.loss_date, 
            "claim_date": claim.claim_date,
            "cause": claim.cause, 
            "loss_amount": claim.loss_amount, 
            "final_payout": claim.final_payout
        },
        "customer_information": {
            "id": customer.id, 
            "name": customer.name, 
            "age": customer.age, 
            "city": customer.city, 
            "state": customer.state, 
            "potential_fraud": customer.is_potential_fraud
        },
        "policy_information": {
            "id": policy.id, 
            "coverage_limit": policy.coverage_limit, 
            "issue_date": policy.issue_date
        }
    }

@router.get("")
def search_claims(
    city: Optional[str] = None, 
    state: Optional[str] = None, 
    cause: Optional[str] = None,
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None,
    min_payout: Optional[float] = None, 
    max_payout: Optional[float] = None,
    sort_by: Optional[str] = Query("claim_date", description="Field to sort by (e.g., claim_date, loss_amount, final_payout)"),
    order: Optional[str] = Query("desc", description="Sorting direction: 'asc' or 'desc'"),
    db: Session = Depends(get_db)
):
    """
    Search and filter through claims across multiple parameters with dynamic sorting.
    """
    # Begin building the base query by joining needed tables
    query = db.query(Claim).join(Policy).join(Customer)
    
    # Apply text filters (case-insensitive where possible)
    if city: 
        query = query.filter(Customer.city.ilike(f"%{city}%"))
    if state: 
        query = query.filter(Customer.state.iexact(state))
    if cause: 
        query = query.filter(Claim.cause.ilike(f"%{cause}%"))
        
    # Apply date boundaries
    if start_date: 
        query = query.filter(Claim.claim_date >= start_date)
    if end_date: 
        query = query.filter(Claim.claim_date <= end_date)
        
    # Apply numeric financial boundaries
    if min_payout is not None: 
        query = query.filter(Claim.final_payout >= min_payout)
    if max_payout is not None: 
        query = query.filter(Claim.final_payout <= max_payout)

    # Dynamic sorting safety check
    sort_attr = getattr(Claim, sort_by, None)
    if sort_attr is None:
        # Fall back to default if field string is invalid
        sort_attr = Claim.claim_date

    if order.lower() == "desc":
        query = query.order_by(sort_attr.desc())
    else:
        query = query.order_by(sort_attr.asc())

    return query.all()