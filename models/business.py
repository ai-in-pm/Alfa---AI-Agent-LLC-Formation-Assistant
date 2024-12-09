from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from models import Base

class Business(Base):
    __tablename__ = 'businesses'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    state = Column(String, nullable=False)
    is_nonprofit = Column(Boolean, default=False)
    tax_classification = Column(String)
    mission_statement = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # Add relationship to AI employees
    ai_employees = relationship("AIEmployee", back_populates="business")
    ai_tasks = relationship("AITask")
