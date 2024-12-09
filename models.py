from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    businesses = relationship('Business', back_populates='owner')
    documents = relationship('Document', back_populates='owner')

class Business(Base):
    __tablename__ = 'businesses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    state = Column(String, nullable=False)
    entity_type = Column(String, default='LLC')
    formation_status = Column(String, default='pending')
    ein = Column(String)
    industry = Column(String)
    is_nonprofit = Column(Boolean, default=False)
    tax_classification = Column(String)
    mission_statement = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'))
    
    # Business Details
    business_address = Column(String)
    mailing_address = Column(String)
    phone = Column(String)
    website = Column(String)
    
    # Formation Progress
    formation_progress = Column(Integer, default=0)
    is_name_available = Column(Boolean)
    is_articles_filed = Column(Boolean, default=False)
    is_ein_obtained = Column(Boolean, default=False)
    
    # Relationships
    owner = relationship('User', back_populates='businesses')
    documents = relationship('Document', back_populates='business')
    compliance_items = relationship('ComplianceItem', back_populates='business')
    financial_records = relationship('FinancialRecord', back_populates='business')
    ai_employees = relationship("AIEmployee", back_populates="business")
    ai_tasks = relationship("AITask")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, default='draft')
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'))
    business_id = Column(Integer, ForeignKey('businesses.id'))
    
    # Relationships
    owner = relationship('User', back_populates='documents')
    business = relationship('Business', back_populates='documents')

class ComplianceItem(Base):
    __tablename__ = 'compliance_items'
    
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey('businesses.id'))
    type = Column(String, nullable=False)
    due_date = Column(DateTime)
    status = Column(String, default='pending')
    description = Column(String)
    requirements = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    business = relationship('Business', back_populates='compliance_items')

class FinancialRecord(Base):
    __tablename__ = 'financial_records'
    
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey('businesses.id'))
    type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    category = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    business = relationship('Business', back_populates='financial_records')

class BusinessInsight(Base):
    __tablename__ = 'business_insights'
    
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey('businesses.id'))
    type = Column(String, nullable=False)
    content = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    priority = Column(Integer, default=0)
    status = Column(String, default='active')

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    type = Column(String, nullable=False)
    content = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    priority = Column(String, default='normal')

class AIEmployee(Base):
    __tablename__ = 'ai_employees'
    
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey('businesses.id'))
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    business = relationship('Business', back_populates='ai_employees')

class AITask(Base):
    __tablename__ = 'ai_tasks'
    
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey('businesses.id'))
    type = Column(String, nullable=False)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

# Create database engine and tables
def init_db(database_url):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine
