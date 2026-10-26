
# Document Intelligence API

A REST API built with Flask and PostgreSQL that accepts PDF and TXT documents, extracts their text, generates keywords using TF-IDF, and supports document search and management.

## Features

- Upload PDF and TXT documents
- Extract and store document text
- Generate keywords using TF-IDF
- Store document metadata and text in PostgreSQL
- Retrieve, update, list, and delete documents
- Search documents using PostgreSQL full-text search
- Paginate document listings and search results
- Validate file types and upload sizes
- Return JSON responses with appropriate HTTP status codes

## Tech Stack

- Python 3.11
- Flask
- Flask-SQLAlchemy
- PostgreSQL
- Psycopg
- scikit-learn
- pypdf
- Postman

## Setup

### 1. Clone the repository

    git clone <your-repository-url>
    cd document-intelligence-api

### 2. Create a virtual environment

    python -m venv venv

On Windows PowerShell:

    .\venv\Scripts\Activate.ps1

### 3. Install dependencies

    python -m pip install flask flask-sqlalchemy "psycopg[binary]" pypdf scikit-learn python-dotenv

### 4. Configure environment variables

Create a `.env` file in the project root:

    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=document_intelligence
    DB_USER=postgres
    DB_PASSWORD=your_postgresql_password

Replace the password with your local PostgreSQL password.

### 5. Create the database

Create a PostgreSQL database named `document_intelligence`.

The application creates its initial tables when it starts.

### 6. Run the application

    python run.py

The API will be available at:

    http://127.0.0.1:5000

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API status |
| GET | `/health/db` | Database health check |
| POST | `/api/documents` | Upload a document |
| GET | `/api/documents` | List documents with pagination |
| GET | `/api/documents/<id>` | Retrieve a document |
| PUT | `/api/documents/<id>` | Replace a document |
| DELETE | `/api/documents/<id>` | Delete a document |
| GET | `/api/documents/search?q=<query>` | Search documents |

Listing and search endpoints support `page` and `per_page` parameters. The maximum page size is 100.

## Testing

Use Postman to test the endpoints. For document uploads, select Body → form-data, use `file` as the key, change its type to File, and select a PDF or TXT document.

## Notes

- The maximum upload size is 10 MB.
- Keyword extraction uses TF-IDF; no model training is required.
- The current search implementation combines PostgreSQL full-text search with filename and keyword matching.
- This is a local development project, not a production-hardened service.

## Future Improvements

- Authentication and authorization
- Database migrations
- Automated API tests
- SQL-level pagination for search
- Improved keyword ranking
- Production deployment
