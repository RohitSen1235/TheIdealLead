# The.Ideal.Leads: AI-Powered Lead Generation Platform

The.Ideal.Leads is an innovative, AI-driven lead generation platform designed to help businesses streamline their customer acquisition process. By leveraging advanced algorithms and data analysis, The.Ideal.Leads creates detailed customer personas and generates highly targeted leads, increasing conversion rates and ROI for its users.

## Key Features

1. **Customer Persona-based Lead Generation**: AI algorithms analyze vast amounts of data to create detailed customer personas, allowing for highly targeted lead generation.

2. **Validated Email Addresses**: Ensures that all generated leads have valid and active email addresses, improving outreach efficiency.

3. **Early Access Program**: Offers users the opportunity to test the product and provide valuable feedback during the development phase.


## Project Structure

The project is divided into two main parts:

1. **Frontend**: A Vue.js application that handles the user interface and interactions.
2. **Backend**: A FastAPI application that manages data processing, storage, and email communications.

## Prerequisites

Before running the project, ensure you have the following installed:

- Node.js (v14 or later)
- Python (v3.8 or later)
- pip (Python package manager)
- npm (Node package manager)

## Setup and Installation

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   Create a `config.py` file in the backend directory and add the following:
   ```
   EMAIL_HOST=your_smtp_server
   EMAIL_PORT=587
   EMAIL_USERNAME=your_email@example.com
   EMAIL_PASSWORD=your_email_password
   EMAIL_FROM=your_email@example.com
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install the required npm packages:
   ```
   npm install
   ```

## Running the Project

### Start the Backend Server

1. From the backend directory, with the virtual environment activated, run:
   ```
   uvicorn main:app --reload
   ```
   The backend server will start running on `http://localhost:8000`.

### Start the Frontend Development Server

1. From the frontend directory, run:
   ```
   npm run serve
   ```
   The frontend development server will start running on `http://localhost:8080`.

## Accessing the Application

Open a web browser and navigate to `http://localhost:8080` to access the The.Ideal.Leads application.

## Current State and Future Development

- The application currently showcases the main features and collects leads through the early access program.
- The pricing page is hidden as the product is still in the early access phase.
- Future development will include implementing the full lead generation functionality, integrating advanced AI algorithms, and introducing a comprehensive pricing structure.


## Support

For any questions or issues, please open an issue in the project repository or contact our support team at support@TheIdealLead.com.
