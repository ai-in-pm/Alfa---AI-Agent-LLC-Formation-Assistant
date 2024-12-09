from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from models import Base

class AIEmployee(Base):
    __tablename__ = 'ai_employees'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    department = Column(String, nullable=False)
    skills = Column(JSON)
    performance_metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    business_id = Column(Integer, ForeignKey('businesses.id'))
    
    business = relationship("Business", back_populates="ai_employees")
    tasks = relationship("AITask", back_populates="employee")

class AITask(Base):
    __tablename__ = 'ai_tasks'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default='pending')
    priority = Column(Integer)
    completion_rate = Column(Float)
    metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)
    business_id = Column(Integer, ForeignKey('businesses.id'))
    employee_id = Column(Integer, ForeignKey('ai_employees.id'))
    
    business = relationship("Business", back_populates="ai_tasks")
    employee = relationship("AIEmployee", back_populates="tasks")
