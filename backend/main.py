from datetime import timedelta
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import EmailStr
import pandas as pd
import tempfile
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Import internal modules
from config import settings
from models import (
    LeadGenerationRequest, LeadCreate, User, UserCreate, Token,
    Base, DBLead, DBUser, CreditPurchaseRequest, CreditPurchaseResponse
)
from services.lead_generator import LeadGenerator
from services.task_manager import task_manager, TaskStatus
from services.auth import (
    create_user, authenticate_user, create_access_token,
    get_current_user_from_token, check_user_credits, deduct_user_credits
)
from services.payment import create_payment_intent

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

# Create all tables
Base.metadata.create_all(bind=engine)

# Initialize LeadGenerator
lead_generator = LeadGenerator()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get current user
async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> DBUser:
    return get_current_user_from_token(token, db)

async def send_welcome_email(to_email: str, name: str):
    if not settings.is_email_configured:
        print("Email settings not configured, skipping email send")
        return

    message = MIMEMultipart("alternative")
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = "Welcome to TargetSphere!"

    text = f"""
    Dear {name},

    Welcome to TargetSphere! We're excited to have you on board.
    
    You've received 100 credits to start generating leads right away.
    
    Best regards,
    The TargetSphere Team
    """

    part1 = MIMEText(text, "plain")
    message.attach(part1)

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            server.send_message(message)
        print(f"Welcome email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send welcome email: {str(e)}")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": f"Error: {exc.detail}"},
    )

@app.post("/register", response_model=Token)
async def register_user(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(DBUser).filter(DBUser.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = create_user(db, user)
    
    # Send welcome email
    background_tasks.add_task(send_welcome_email, user.email, user.name)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: DBUser = Depends(get_current_user)):
    return current_user

@app.post("/calculate-credits/")
async def calculate_credits(
    request: LeadGenerationRequest,
    current_user: DBUser = Depends(get_current_user)
):
    """Calculate credits required for lead generation"""
    if request.number_of_leads <= 0:
        raise HTTPException(status_code=400, detail="Number of leads must be greater than 0")
    try:
        credits_info = await lead_generator.calculate_credits(
            request.ideal_customer_profile,
            request.number_of_leads,
            request.get_work_email,
            request.get_phone_number
        )
        return credits_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start-lead-generation/")
async def start_lead_generation(
    request: LeadGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Calculate required credits
        credits_info = await lead_generator.calculate_credits(
            request.ideal_customer_profile,
            request.number_of_leads,
            request.get_work_email,
            request.get_phone_number
        )
        
        # Check if user has enough credits
        required_credits = credits_info["total_credits"]
        if not check_user_credits(current_user, required_credits):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Required: {required_credits}, Available: {current_user.credits}"
            )
        
        # Deduct credits
        deduct_user_credits(db, current_user, required_credits)
        
        # Create distributed tasks
        group_id = task_manager.create_distributed_tasks(
            icp=request.ideal_customer_profile,
            num_leads=request.number_of_leads,
            get_work_email=request.get_work_email,
            get_phone_number=request.get_phone_number
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
async def get_task_status(
    task_id: str,
    current_user: DBUser = Depends(get_current_user)
):
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
async def download_results(
    group_id: str,
    current_user: DBUser = Depends(get_current_user)
):
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

@app.post("/purchase-credits/", response_model=CreditPurchaseResponse)
async def purchase_credits(
    request: CreditPurchaseRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Purchase credits (development mode - automatically adds credits)"""
    if request.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of credits must be greater than 0"
        )
    
    return create_payment_intent(db, current_user, request.credits)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
