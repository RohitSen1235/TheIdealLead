from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib  # Add this line

# for making HTTP request to webhook
import httpx  # Make sure to install httpx for making HTTP request
import json
import uuid
# import internal modules
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_FROM
from models import LeadGenerationRequest, LeadCreate


app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./leads.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
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


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def send_email(to_email: str, name: str):
    message = MIMEMultipart("alternative")
    message["From"] = EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = "Welcome to LeadGen Pro's Early Access Program!"

    # Plain text version of the email (for email clients that don't support HTML)
    text = f"""
    Dear {name},

    Thank you for your interest in LeadGen Pro! We're excited to have you on board.

    You are now eligible for our exclusive early access program, offering you the opportunity to test our product and provide valuable feedback.

    We'll be in touch soon with more details about accessing the early version of LeadGen Pro.

    Best regards,
    The LeadGen Pro Team
    """

    # HTML version of the email
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to LeadGen Pro</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #4a90e2, #50e3c2);
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .content {{
                background-color: #f9f9f9;
                border-radius: 5px;
                padding: 20px;
                margin-top: 20px;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #4a90e2;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Welcome to The.Ideal.Leads</h1>
        </div>
        <div class="content">
            <h2>Dear {name},</h2>
            <p>Thank you for your interest in LeadGen Pro! We're thrilled to have you on board.</p>
            <p>We're excited to inform you that you are now eligible for our <strong>exclusive early access program</strong>. This program offers you the unique opportunity to:</p>
            <ul>
                <li>Use and Review our cutting-edge lead generation product</li>
                    <ul>
                        <li><em>Free of charge For limited time only</em></li>
                    </ul>
                <li>Provide valuable feedback to shape its development</li>
                <li>Be one of the first to experience new features and improvements</li>
                <li>Gain a competitive edge in your industry</li>
            </ul>
            <p>Your insights and experiences will be instrumental in refining LeadGen Pro to better meet the needs of professionals like yourself. We truly value your input and look forward to your participation.</p>
            <p>We'll be in touch soon with more details about how you can access the early version of LeadGen Pro and share your thoughts with us.</p>
            <a href="#" class="cta-button">Learn More About Early Access</a>
        </div>
        <p>Thank you again for your interest and support. We're thrilled to have you as part of our community of early adopters!</p>
        <p>Best regards,<br>The.Ideal.Leads Team</p>
    </body>
    </html>
    """

    # Attach both plain text and HTML versions
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()  # Enable TLS
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(message)
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": f"Error: {exc.detail}"},
    )

@app.post("/submit-lead/")
async def submit_lead(lead: LeadCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    print(f"Received lead data: {lead.dict()}")  # Debugging line

    # Try to add the lead to the database
    db_lead = Lead(**lead.dict())
    db.add(db_lead)
    try:
        db.commit()
        db.refresh(db_lead)
        is_new_lead = True
    except IntegrityError as e:
        db.rollback()
        print(f"Lead already exists: {str(e)}")  # Debugging line
        is_new_lead = False
    except Exception as e:
        db.rollback()
        print(f"Database error: {str(e)}")  # Debugging line
        raise HTTPException(status_code=500, detail=f"Error processing lead: {str(e)}")

    # Add email sending as a background task
    background_tasks.add_task(send_email, lead.email, lead.name)
    print(f"Email task added for {lead.email}")  # Debugging line

    # Prepare the response message
    if is_new_lead:
        message = "Lead submitted successfully and email will be sent."
    else:
        message = "Lead already exists, but email will be sent."

    return {"message": message}

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Lead Generation API"}


@app.post("/start-lead-generation/")
async def start_lead_generation(request: LeadGenerationRequest):
    print(f"Received lead generation request: {request}")  # Debug print
    webhook_url = "https://n8n.rsfreelance.com/webhook/find-leads"  # Verify this URL

    payload = {
        "ideal_customer_profile": request.ideal_customer_profile,
        "number_of_leads": request.number_of_leads,
        "task_id": str(uuid.uuid4())
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)

        print(f"Webhook response status: {response.status_code}")
        print(f"Webhook response content: {response.text}")

        # Parse the JSON response
        webhook_response = json.loads(response.text)

        if webhook_response.get("status") == 200:
            return {"message": "Lead generation process has started. You will be notified via email once completed."}
        else:
            raise HTTPException(status_code=400, detail="Webhook returned an unexpected response")

    except json.JSONDecodeError:
        print("Failed to parse webhook response as JSON")
        raise HTTPException(status_code=500, detail="Error processing webhook response")
    except httpx.HTTPStatusError as e:
        print(f"HTTP Status Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error calling webhook: {str(e)}")
    except httpx.RequestError as e:
        print(f"Request Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error making request to webhook: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
