# CodeCelix Lead Finder (v2)

Next.js frontend (Vercel) + FastAPI backend (EthioDeploy). The browser only talks to Next.js `/api/*`; that route proxies to
FastAPI with `BACKEND_API_URL` / `BACKEND_API_KEY` and keeps the session token in an httpOnly cookie.

## What it does (per the build spec)
Pick country → niche (allowed combos enforced by the server from the `country_niches` table) → cities (search, state filter, select all) →
lead count 10–200 → filters → Start. A background job discovers businesses, inspects websites (up to 5 pages), keeps only businesses with a
WhatsApp number, and loops until N leads are found or candidates/budget run out (then PARTIAL with a shortfall breakdown).
Results: confidence, evidence drawer, feedback buttons, save, CSV/XLSX export (formula-injection safe), job history, re-run, cancel, resume.
Accounts (email+password, PBKDF2, hashed session tokens), roles admin/user, per-user data isolation, daily lead quota, admin panel
(matrix, keywords, chatbot signatures, limits, suppression list, cost).

## Detection rules (deterministic, no LLM)
WhatsApp: CONFIRMED = wa.me / api.whatsapp.com link, floating-button plugin config, or "WhatsApp" within 60 chars of a number, found on the
business's own pages. PROBABLE = valid mobile from discovery with no WhatsApp mention (only when "confirmed only" is off).
Type: AUTOMATED if a WhatsApp-automation vendor/bot text is found, else MANUAL ("no bot signal found", not a live test).
Chatbot: YES (vendor signature or generic widget), NO only when the site was fetched fully, UNKNOWN when blocked/timeout/no site.
Hot lead = CONFIRMED + MANUAL + chatbot NO.
Known limit: inspection is static HTTP only (no Playwright), so widgets injected purely by JavaScript can be missed; confidence is lowered accordingly.

## Run locally
    python -m venv .venv && .venv\Scripts\activate && python -m pip install -r requirements-dev.txt
    python -m uvicorn app:app --reload          # http://127.0.0.1:8000
    npm install && npm run dev                  # needs BACKEND_API_URL=http://127.0.0.1:8000 in .env
Tests: `python -m unittest backend.tests.test_core backend.tests.test_api`

## Deploy
Backend (EthioDeploy): build `pip install -r requirements.txt`, start `uvicorn app:app --host 0.0.0.0 --port $PORT`.
Set `DATABASE_URL` (PostgreSQL) for persistence. Frontend (Vercel): `npm install && npm run build`. Variables: see `.env.example`.
Full city list: `python scripts/load_geonames.py cities15000.txt` (GeoNames, CC-BY 4.0 attribution required).
