# Smart Safety Wearable Output Backend

This repository holds the production-ready FastAPI backend for the IoT-based Smart Safety Wearable device.

## Core Stack
- Python 3.11+
- FastAPI (0.115+) & Uvicorn
- SQLAlchemy 2.0 (asyncio + asyncpg)
- Alembic for database migrations
- Twilio SDK and OpenAI API integration for emergency calls and context analysis

## Local Setup

1. **Prerequisites**
   Have a local Postgres DB instance on port 5432 with password `password`, creating a database called `safety_wearable`.

2. **Environment Variables**
   The `.env` file is initialized from `.env.example`. Overwrite Twilio and OpenAI credentials to enable live capabilities. Without it, the application logs them conceptually.

3. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Application**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to experiment with Swagger UI.
# smart-safety-wearable_1
