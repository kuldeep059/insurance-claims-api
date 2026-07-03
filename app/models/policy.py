from sqlalchemy import Column, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    coverage_limit = Column(Float, nullable=False)
    issue_date = Column(Date, nullable=False)

    # Explicit relationships back and forth
    customer = relationship("Customer", back_populates="policies")
    claims = relationship("Claim", back_populates="policy", cascade="all, delete-orphan")