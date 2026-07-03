import pandas as pd
from datetime import date
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.policy import Policy
from app.models.claim import Claim

def process_upload_pipeline(df_cust: pd.DataFrame, df_poly: pd.DataFrame, df_clam: pd.DataFrame, db: Session):
    errors = []
    
    # 1. Total records calculation
    total_input_records = len(df_cust) + len(df_poly) + len(df_clam)

    # 2. Clean column headers (lowercase and strip whitespace)
    df_cust.columns = df_cust.columns.str.strip().str.lower()
    df_poly.columns = df_poly.columns.str.strip().str.lower()
    df_clam.columns = df_clam.columns.str.strip().str.lower()

    # Trim text spaces inside text rows
    for df in [df_cust, df_poly, df_clam]:
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()

    # 3. Handle primary key mappings to avoid KeyErrors
    df_cust.rename(columns={'customer_id': 'id'}, inplace=True)
    df_poly.rename(columns={'policy_id': 'id'}, inplace=True)
    df_clam.rename(columns={'claim_id': 'id'}, inplace=True)

    # 4. Drop rows missing vital IDs
    df_cust.dropna(subset=['id', 'age', 'state'], inplace=True)
    df_poly.dropna(subset=['id', 'customer_id', 'coverage_limit'], inplace=True)
    df_clam.dropna(subset=['id', 'policy_id', 'loss_amount'], inplace=True)

    # 5. Deduplicate records based on primary key IDs
    df_cust.drop_duplicates(subset=['id'], keep='first', inplace=True)
    df_poly.drop_duplicates(subset=['id'], keep='first', inplace=True)
    df_clam.drop_duplicates(subset=['id'], keep='first', inplace=True)

    # 6. Parse and cast types safely
    try:
        df_cust['age'] = df_cust['age'].astype(int)
        df_poly['coverage_limit'] = df_poly['coverage_limit'].astype(float)
        df_poly['policy_issue_date'] = pd.to_datetime(df_poly['policy_issue_date']).dt.date
        df_clam['loss_amount'] = df_clam['loss_amount'].astype(float)
        df_clam['loss_date'] = pd.to_datetime(df_clam['loss_date']).dt.date
    except Exception as e:
        return {
            "total_records": total_input_records,
            "inserted": 0,
            "rejected": total_input_records,
            "errors": [f"Data parsing error: {str(e)}"]
        }

    valid_customers = {}
    valid_policies = {}
    inserted_count = 0
    today = date.today()

    # --- Process Customers ---
    for _, row in df_cust.iterrows():
        valid_customers[row['id']] = {
            "id": row['id'], "name": row.get('name', 'Unknown'), "age": int(row['age']),
            "city": row['city'], "state": row['state'], "claim_count": 0
        }

    # --- Process Policies ---
    for _, row in df_poly.iterrows():
        if row['customer_id'] not in valid_customers:
            errors.append(f"Policy {row['id']} rejected: Customer ID {row['customer_id']} does not exist.")
            continue
        
        valid_policies[row['id']] = {
            "id": row['id'], "customer_id": row['customer_id'],
            "coverage_limit": float(row['coverage_limit']), "issue_date": row['policy_issue_date']
        }

    # --- Process Claims & Apply Business Rules ---
    claims_to_insert = []
    for _, row in df_clam.iterrows():
        pid = row['policy_id']
        
        if pid not in valid_policies:
            errors.append(f"Claim {row['id']} rejected: Policy ID {pid} not found.")
            continue
            
        policy = valid_policies[pid]
        customer = valid_customers[policy['customer_id']]

        # Rule 1 & 2: Validate boundaries
        if row['loss_amount'] < 0:
            errors.append(f"Claim {row['id']} rejected: Loss amount cannot be negative.")
            continue
        if row['loss_date'] > today:
            errors.append(f"Claim {row['id']} rejected: Loss date cannot be in the future.")
            continue
        # Rule 3: Compare loss date with issue date since claim_date is omitted from CSV columns
        if row['loss_date'] < policy['issue_date']:
            errors.append(f"Claim {row['id']} rejected: Loss date precedes policy issue date.")
            continue

        payout = float(row['loss_amount'])

        # Rule 7: California Flood Deductible 10%
        if customer['state'] == "CA" and str(row['cause']).strip().lower() == "flood":
            payout = payout * 0.90

        # Rule 6: Minor demographic penalty (50% payout)
        if customer['age'] < 18:
            payout = payout * 0.50

        # Rule 4 & 5: Cap boundaries
        if payout > policy['coverage_limit']:
            payout = policy['coverage_limit']
        if payout < 0:
            payout = 0.0

        customer['claim_count'] += 1

        claims_to_insert.append(Claim(
            id=row['id'], policy_id=pid, loss_date=row['loss_date'],
            claim_date=row['loss_date'], cause=row['cause'],  # loss_date fulfills claim_date fallback
            loss_amount=row['loss_amount'], final_payout=payout
        ))

    # --- Database Sync Block ---
    try:
        for c_id, c_data in valid_customers.items():
            is_fraud = True if c_data['claim_count'] > 5 else False
            db.merge(Customer(
                id=c_data['id'], name=c_data['name'], age=c_data['age'],
                city=c_data['city'], state=c_data['state'], is_potential_fraud=is_fraud
            ))
            inserted_count += 1

        for p_id, p_data in valid_policies.items():
            db.merge(Policy(
                id=p_data['id'], customer_id=p_data['customer_id'],
                coverage_limit=p_data['coverage_limit'], issue_date=p_data['issue_date']
            ))
            inserted_count += 1

        for claim_obj in claims_to_insert:
            db.merge(claim_obj)
            inserted_count += 1

        db.commit()
    except Exception as e:
        db.rollback()
        return {
            "total_records": total_input_records, "inserted": 0, "rejected": total_input_records,
            "errors": [f"Database transaction failure: {str(e)}"]
        }

    return {
        "total_records": total_input_records,
        "inserted": inserted_count,
        "rejected": max(0, total_input_records - inserted_count),
        "errors": errors
    }