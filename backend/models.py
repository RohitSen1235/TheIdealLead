from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError




# Define the request model
class LeadGenerationRequest(BaseModel):
    ideal_customer_profile: str
    number_of_leads: int

# Pydantic model for request validation
class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    company: str
    phone: str
