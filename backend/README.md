# Backend (FastAPI)
Entry point: `app.py` -> `backend/main.py`. Core logic in `backend/core/` (detection rules, inspector, jobs, auth, providers, db).
Tests: `python -m unittest backend.tests.test_core backend.tests.test_api` (API tests need `requirements-dev.txt`).
