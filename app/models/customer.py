from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    
    # Rule 8 Flag: Will turn True if customer has > 5 claims
    is_potential_fraud = Column(Boolean, default=False)

    # Relationship linking back to the Policy table
    policies = relationship("Policy", back_populates="customer", cascade="all, delete-orphan")