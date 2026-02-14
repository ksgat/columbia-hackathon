# Prophecy Backend

FastAPI backend for Prophecy social prediction markets.

## Setup

1. **Create virtual environment:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Fill in your Supabase credentials
   - Add your Anthropic API key

4. **Run development server:**
   ```bash
   python -m app.main
   # Or with uvicorn directly:
   uvicorn app.main:app --reload --port 8000
   ```

5. **Access API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI app & startup
│   ├── config.py         # Configuration & env vars
│   ├── database.py       # Database connection
│   ├── routers/          # API endpoints
│   ├── models/           # SQLAlchemy models
│   ├── services/         # Business logic (LMSR, resolution, etc.)
│   ├── agents/           # Prophet AI agents
│   └── tasks/            # Background tasks
├── scripts/              # Utility scripts (seeding, etc.)
├── tests/               # Temporary verification tests
└── requirements.txt      # Python dependencies
```

## Development

- FastAPI auto-reload is enabled in development
- Access interactive API docs at `/docs`
- All routes are prefixed with `/api`
