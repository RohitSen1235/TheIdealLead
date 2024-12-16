from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError   
from typing import Optional
import pandas as pd
import tempfile
import os

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Import internal modules
from config import settings
from models import LeadGenerationRequest, LeadCreate
from services.lead_generator import LeadGenerator
from services.task_manager import task_manager, TaskStatus

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    company = Column(String)
    phone = Column(String)

Base.metadata.create_all(bind=engine)

# Initialize LeadGenerator
lead_generator = LeadGenerator()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def send_email(to_email: str, name: str, task_id: Optional[str] = None, result_file: Optional[str] = None):
    if not settings.is_email_configured:
        print("Email settings not configured, skipping email send")
        return

    message = MIMEMultipart("alternative")
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    
    if task_id and result_file:
        message["Subject"] = "Your Lead Generation Results Are Ready!"
        text = f"""
        Dear {name},

        Your lead generation task has been completed! You can check the results in your dashboard.

        Task ID: {task_id}

        Best regards,
        The LeadGen Pro Team
        """
    else:
        message["Subject"] = "Welcome to LeadGen Pro's Early Access Program!"
        text = f"""
        Dear {name},

        Thank you for your interest in LeadGen Pro! We're excited to have you on board.

        You are now eligible for our exclusive early access program, offering you the opportunity to test our product and provide valuable feedback.

        Best regards,
        The LeadGen Pro Team
        """

    part1 = MIMEText(text, "plain")
    message.attach(part1)

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            server.send_message(message)
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        # Don't raise the exception as email sending is not critical

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": f"Error: {exc.detail}"},
    )

@app.post("/submit-lead/")
async def submit_lead(lead: LeadCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    print(f"Received lead data: {lead.dict()}")

    db_lead = Lead(**lead.dict())
    db.add(db_lead)
    try:
        db.commit()
        db.refresh(db_lead)
        is_new_lead = True
    except IntegrityError as e:
        db.rollback()
        print(f"Lead already exists: {str(e)}")
        is_new_lead = False
    except Exception as e:
        db.rollback()
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing lead: {str(e)}")

    background_tasks.add_task(send_email, lead.email, lead.name)
    print(f"Email task added for {lead.email}")

    if is_new_lead:
        message = "Lead submitted successfully and email will be sent."
    else:
        message = "Lead already exists, but email will be sent."

    return {"message": message}

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Lead Generation API"}

class CreditCalculationRequest(BaseModel):
    icp: str
    num_leads: int

@app.post("/calculate-credits/")
async def calculate_credits(request: CreditCalculationRequest):
    """Calculate credits required for lead generation"""
    if request.num_leads <= 0:
        raise HTTPException(status_code=400, detail="Number of leads must be greater than 0")
    try:
        credits_info = await lead_generator.calculate_credits(request.icp, request.num_leads)
        return credits_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start-lead-generation/")
async def start_lead_generation(request: LeadGenerationRequest, background_tasks: BackgroundTasks):
    try:
        # Create distributed tasks
        group_id = task_manager.create_distributed_tasks(
            icp=request.ideal_customer_profile,
            num_leads=request.number_of_leads
        )
        
        # Start processing each task in the group
        group_status = task_manager.get_group_status(group_id)
        for task_id in group_status["task_statuses"].keys():
            background_tasks.add_task(
                task_manager.process_task,
                task_id,
                lead_generator
            )
        
        return {
            "message": "Lead generation process has started.",
            "group_id": group_id,
            "task_ids": list(group_status["task_statuses"].keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    # First try to get individual task status
    status = task_manager.get_task_status(task_id)
    if status:
        return status
        
    # If not found, try to get group status
    status = task_manager.get_group_status(task_id)  # task_id might be a group_id
    if status:
        return status
        
    raise HTTPException(status_code=404, detail="Task or group not found")

@app.get("/download-results/{group_id}")
async def download_results(group_id: str):
    # Get group status
    group_status = task_manager.get_group_status(group_id)
    if not group_status:
        raise HTTPException(status_code=404, detail="Group not found")
        
    if group_status["status"] != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Not all tasks in group completed yet")
        
    if not group_status["result_files"]:
        raise HTTPException(status_code=404, detail="No result files found")
    
    try:
        # Read and combine all CSV files
        all_data = []
        for file_path in group_status["result_files"]:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                all_data.append(df)
        
        if not all_data:
            raise HTTPException(status_code=404, detail="No valid result files found")
            
        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Create a temporary file for the combined results
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            combined_df.to_csv(tmp_file.name, index=False)
            
            # Create a meaningful filename
            timestamp = group_status["result_files"][0].split("_")[-1]  # Get timestamp from first file
            filename = f"combined_leads_{timestamp}"
            
            return FileResponse(
                tmp_file.name,
                media_type="text/csv",
                filename=filename,
                background=BackgroundTasks().add_task(os.unlink, tmp_file.name)  # Delete temp file after sending
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error combining results: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
