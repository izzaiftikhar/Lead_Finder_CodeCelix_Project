# Backend API Work

The API contract remains in the root FastAPI application. Pydantic request and response models live in `backend/schemas.py`, with API tests in `backend/tests/`.

## Run locally

From the repository root, install the project dependencies and start the API:

```bash
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

The interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Test

Run the API contract tests from the repository root:

```bash
python -m unittest discover -s backend/tests -v
```

Tests use a temporary SQLite database and do not modify the local demo database. Invalid Pydantic inputs use FastAPI's standard `422` response; unsupported countries retain the existing `400` response.