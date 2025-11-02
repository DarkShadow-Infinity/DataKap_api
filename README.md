# DataKap API

This repository provides a FastAPI-based reference implementation of the DataKap backend specification.

## Getting started

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the application with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The OpenAPI documentation is available at `http://127.0.0.1:8000/docs` once the server is running.

## Project structure

- `app/schemas.py` – Pydantic models representing request and response payloads.
- `app/storage.py` – In-memory storage used to simulate persistence and authentication.
- `app/auth.py` – Dependency helpers for token-based authentication.
- `app/main.py` – FastAPI routes implementing the endpoints described in the specification.

The implementation favors readability and mirrors the behavior expected by the mobile application while keeping the persistence layer lightweight for demonstration purposes.
