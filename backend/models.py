from pydantic import BaseModel, EmailStr
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

# SQLAlchemy Models
class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    company = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    credits = Column(Integer, default=100)  # Starting credits for new users

class DBLead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    company = Column(String)
    phone = Column(String)
    work_email = Column(String)  # Added for work email service

class DBTask(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(String, index=True)
    icp = Column(String)
    total_leads_needed = Column(Integer)
    leads_to_find = Column(Integer)
    leads_found = Column(Integer, default=0)
    start_index = Column(Integer)
    get_work_email = Column(Boolean, default=False)
    get_phone_number = Column(Boolean, default=False)
    status = Column(String)  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result_file = Column(String, nullable=True)
    warning = Column(String, nullable=True)
    error = Column(String, nullable=True)

class DBTransaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    amount = Column(Float)
    credits = Column(Integer)
    stripe_payment_id = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String)  # 'pending', 'completed', 'failed'

# Pydantic Models for API
class UserBase(BaseModel):
    email: EmailStr
    name: str
    company: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    is_active: bool
    credits: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class LeadGenerationRequest(BaseModel):
    ideal_customer_profile: str
    number_of_leads: int
    get_work_email: bool = False  # Optional service for work email
    get_phone_number: bool = False  # Optional service for phone number

class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    company: str
    phone: Optional[str] = None
    work_email: Optional[str] = None

class CreditPurchaseRequest(BaseModel):
    credits: int
    payment_method_id: Optional[str] = None  # Made optional for development mode

class CreditPurchaseResponse(BaseModel):
    status: str
    amount: float
    credits: int
    message: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    group_id: str
    status: str
    status_message: str
    total_leads_found: int
    total_leads_needed: int
    warnings: List[str]
    can_download: bool
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime]

# For convenience, create aliases
Lead = DBLead
