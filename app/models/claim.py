from sqlalchemy import Column, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Claim(Base):
    __tablename__ = "claims"

    id = Column(String, primary_key=True, index=True)
    policy_id = Column(String, ForeignKey("policies.id"), nullable=False)
    loss_date = Column(Date, nullable=False)
    claim_date = Column(Date, nullable=False)
    cause = Column(String, nullable=False)
    loss_amount = Column(Float, nullable=False)
    final_payout = Column(Float, nullable=False)

    # Link back up to parent Policy
    policy = relationship("Policy", back_populates="claims")