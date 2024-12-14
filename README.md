# The.Ideal.Leads: AI-Powered Lead Generation Platform

The.Ideal.Leads is an innovative, AI-driven lead generation platform designed to help businesses streamline their customer acquisition process. By leveraging advanced algorithms and data analysis, The.Ideal.Leads creates detailed customer personas and generates highly targeted leads, increasing conversion rates and ROI for its users.

## Technical Stack

### Frontend
- Vue.js 3.x
- Vue Router 4.x for navigation
- Vuex 4.x for state management
- Axios for API communication
- SASS for styling
- Cypress for E2E testing
- Jest for unit testing

### Backend
- FastAPI (Python web framework)
- SQLAlchemy ORM
- SQLite database
- Pydantic for data validation
- SMTP for email communications
- Background task processing
- Webhook integration for AI processing

## Key Features

1. **AI-Powered Lead Generation**
   - Custom Ideal Customer Profile (ICP) input
   - Automated lead generation process
   - Real-time processing status updates
   - Multi-Query Search System:
     * Generates 3 unique search queries from each ICP using Groq AI
     * Each query uses different combinations of terms to maximize relevant results
     * Example for "Sales managers in tech companies in London":
       - Query 1: "site:linkedin.com/in/ (Sales Manager OR Sales Director) AND (Technology OR Software) AND London"
       - Query 2: "site:linkedin.com/in/ (Head of Sales OR Sales Lead) AND (Tech OR SaaS) AND (London OR Greater London)"
       - Query 3: "site:linkedin.com/in/ (Sales Leadership OR Sales Management) AND (Technology Industry) AND (London UK)"
     * System processes each query's search results until enough leads are found
     * Automatically extracts profile information:
       - Name
       - Current designation
       - Organization/Company
       - LinkedIn Profile URL
     * Results are saved in CSV format for easy access

2. **Lead Management System**
   - Validated email addresses
   - Secure data storage
   - Automated email notifications

3. **User Interface**
   - Modern, responsive design
   - Interactive form components
   - Real-time feedback
   - Cross-browser compatibility

4. **Early Access Program**
   - Product testing opportunity
   - Feedback collection system
   - Priority access to new features

## Prerequisites

- Node.js (v14.x or later)
- Python (v3.8 or later)
- pip (Python package manager)
- npm (v6.x or later)
- Git

## Project Structure

```
targetsphere/
├── backend/                 # Python/FastAPI backend
│   ├── config_template.py   # Email configuration template
│   ├── main.py             # Main application file
│   ├── models.py           # Database models
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # Vue.js frontend
│   ├── public/            # Static files
│   ├── src/               # Source files
│   │   ├── assets/       # Images and styles
│   │   ├── components/   # Vue components
│   │   ├── router/       # Vue router configuration
│   │   ├── services/     # API services
│   │   ├── store/        # Vuex store
│   │   └── views/        # Vue views
│   └── tests/            # Frontend tests
│       ├── e2e/          # Cypress tests
│       └── unit/         # Jest tests
```

## Setup and Installation

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Configure email settings:
   - Copy `config_template.py` to `config.py`
   - Update the following variables:
     ```python
     EMAIL_HOST=your_smtp_server
     EMAIL_PORT=587
     EMAIL_USERNAME=your_email@example.com
     EMAIL_PASSWORD=your_email_password
     EMAIL_FROM=your_email@example.com
     ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Development

### Running the Backend

```bash
cd backend
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`

### Running the Frontend

```bash
cd frontend
npm run serve
```
The application will be available at `http://localhost:8080`

### Running Tests

Frontend tests:
```bash
cd frontend
# Unit tests
npm run test:unit
# E2E tests
npm run test:e2e
```

## API Endpoints

- `POST /submit-lead/`: Submit new lead information
  - Required fields: name, email, company, phone
  - Returns: Success message and lead status

- `POST /start-lead-generation/`: Initialize AI lead generation
  - Required fields: ideal_customer_profile, number_of_leads
  - Returns: Process initiation status

## Current State and Future Development

- Early access program active
- Core lead generation functionality implemented
- Planned features:
  - Advanced AI algorithms integration
  - Enhanced lead qualification
  - Custom reporting dashboard
  - Comprehensive pricing structure

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For technical issues or questions:
- Open an issue in the project repository
- Contact support at support@TheIdealLead.com

## License

This project is proprietary software. All rights reserved.
