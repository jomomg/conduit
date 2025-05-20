# Conduit

Conduit is a Medium clone implementation of the [RealWorld spec](https://github.com/gothinkster/realworld). It's a full-stack application built with FastAPI that demonstrates how to build a real-world application with modern best practices.

## Features

- User authentication (signup, login, update profile)
- Article management (create, read, update, delete)
- Profile management
- Follow/unfollow users
- Like/unlike articles
- Comments on articles

## Tech Stack

- **Backend Framework**: FastAPI
- **Database**: SQLite (with SQLAlchemy ORM)
- **Authentication**: JWT
- **Database Migrations**: Alembic
- **Testing**: Pytest

## Project Structure

```
conduit/
├── alembic/           # Database migrations
├── routers/          # API route handlers
├── schemas/          # Pydantic models
├── tests/            # Test files
├── main.py           # Application entry point
├── models.py         # SQLAlchemy models
├── database.py       # Database configuration
├── dependencies.py   # FastAPI dependencies
├── crud.py          # Database operations
└── utils.py         # Utility functions
```

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/jomomg/conduit
cd conduit
```

2. Install dependencies:
```bash
# Install pipenv if you haven't already
pip install pipenv

# Install project dependencies
pipenv install
```

3. Set up the database:
```bash
alembic upgrade head
```

4. Run the application:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:
- Interactive API documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative API documentation (ReDoc): `http://localhost:8000/redoc`

## Testing

Run the test suite:
```bash
pytest
```
