# PersonalTracker Backend

## Structure

```
app/
├── main.py              # FastAPI entry point
├── core/
│   ├── config.py        # Pydantic Settings (env vars)
│   └── database.py      # MongoDB connection
├── auth/
│   ├── routes.py        # Auth endpoints (register, login, refresh, logout, me)
│   ├── schemas.py       # Auth Pydantic models
│   ├── utils.py         # Password hashing (bcrypt), JWT creation/verification
│   └── dependencies.py  # get_current_user dependency
├── tasks/
│   ├── routes.py        # Task CRUD endpoints
│   └── schemas.py       # Task Pydantic models
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
- `JWT_SECRET_KEY` - JWT signing secret (required)
- `JWT_ALGORITHM` - JWT algorithm (default: "HS256")
- `ACCESS_TOKEN_EXPIRE_DAYS` - Access token expiry (default: 7)
- `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiry (default: 30)
- `FRONTEND_URL` - Frontend origin for CORS (default: "http://localhost:5173")

### `app/auth/`
Email + password JWT authentication.
- `POST /auth/register` — register with email, password, name → auto-login, returns access_token + sets refresh_token cookie
- `POST /auth/login` — login with email + password → returns access_token + sets refresh_token cookie
- `POST /auth/refresh` — reads refresh_token from httpOnly cookie, returns new access_token + rotates cookie
- `POST /auth/logout` — clears refresh_token cookie
- `GET /auth/me` — get current user profile (protected)

**Token strategy:** access_token returned in JSON body (stored in memory by frontend). refresh_token set as httpOnly cookie (path=/auth/refresh, secure in production, samesite=lax).

User identifier is `email` (stored lowercase). JWT payload contains `sub` (user_id) and `type` (access/refresh).
Dependency: `get_current_user` from `app.auth.dependencies` for protected endpoints.

### `app/tasks/`
Task CRUD with status flow: todo → doing → testing → done. All endpoints protected, scoped to authenticated user.
- `POST /tasks/` — create task (auto status: todo)
- `GET /tasks/` — list tasks (filter by status, pagination via skip/limit)
- `GET /tasks/{task_id}` — get single task
- `PUT /tasks/{task_id}` — partial update (title, description, status)
- `DELETE /tasks/{task_id}` — delete task

## Rules

- Always use `await get_db()` for database access
- Always use `await log_error()` for exception logging
- Never create new MongoDB clients
- Add new env vars to `app/core/config.py` Settings class
