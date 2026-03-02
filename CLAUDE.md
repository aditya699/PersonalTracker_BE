# PersonalTracker Backend

## Structure

```
app/
├── main.py              # FastAPI entry point
├── core/
│   ├── config.py        # Pydantic Settings (env vars)
│   └── database.py      # MongoDB connection
```

## Running

```bash
uv run uvicorn app.main:app --reload
```

## Core Files

### `app/core/database.py`
MongoDB client using Motor. **YOU MUST use these functions:**
- `get_db()` - Get database instance
- `get_client()` - Get/initialize client (connection pool: 50)
- `close_client()` - Cleanup on shutdown
- `log_error()` - Log errors to `error_logs` collection

### `app/core/config.py`
Pydantic Settings loading from `.env`:
- `APP_NAME` - Application name (default: "PersonalTracker")
- `APP_VERSION` - Version string
- `ENVIRONMENT` - development/production (controls docs visibility)
- `MONGO_URI` - MongoDB connection string (required)
- `MONGO_DB_NAME` - Database name (default: "personal_tracker")
- `OPENAI_API_KEY` - OpenAI API key

## Rules

- Always use `await get_db()` for database access
- Always use `await log_error()` for exception logging
- Never create new MongoDB clients
- Add new env vars to `app/core/config.py` Settings class
