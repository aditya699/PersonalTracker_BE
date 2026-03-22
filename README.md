# PersonalTracker Backend

A FastAPI backend for personal productivity tracking — manage tasks, habits, and weekly notes with JWT authentication and MongoDB.

## Features

- **Authentication** — Email/password registration & login with JWT access tokens and httpOnly refresh token cookies
- **Tasks** — Full CRUD with status flow: `todo` → `doing` → `testing` → `done`
- **Habits** — Create habits, track daily entries, and monitor streaks
- **Notes** — Weekly notes organized by week start date
- **Health Check** — `GET /health` endpoint for monitoring

## Tech Stack

- **FastAPI** — async Python web framework
- **MongoDB** — document database via Motor (async driver)
- **Pydantic Settings** — configuration management
- **python-jose** — JWT token handling
- **bcrypt** — password hashing
- **uv** — fast Python package manager

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- MongoDB instance (local or Atlas)

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/PersonalTracker_BE.git
cd PersonalTracker_BE
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

| Variable | Description | Default |
|---|---|---|
| `MONGO_URI` | MongoDB connection string | *required* |
| `MONGO_DB_NAME` | Database name | `personal_tracker` |
| `JWT_SECRET_KEY` | Secret for signing JWTs | *required* |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_DAYS` | Access token lifetime | `7` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `30` |
| `FRONTEND_URL` | Frontend origin for CORS | `http://localhost:5173` |
| `OPENAI_API_KEY` | OpenAI API key | — |

Generate a secure JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Run the server

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs` (development mode only).

## API Endpoints

### Auth (`/auth`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register with email, password, name |
| POST | `/auth/login` | Login → access token + refresh cookie |
| POST | `/auth/refresh` | Rotate refresh token, get new access token |
| POST | `/auth/logout` | Clear refresh token cookie |
| GET | `/auth/me` | Get current user profile |

### Tasks (`/tasks`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/tasks/` | Create a task |
| GET | `/tasks/` | List tasks (filter by status, paginate) |
| GET | `/tasks/{task_id}` | Get a single task |
| PUT | `/tasks/{task_id}` | Update task (title, description, status) |
| DELETE | `/tasks/{task_id}` | Delete a task |

### Habits (`/habits`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/habits/` | Create a habit |
| GET | `/habits/` | List active habits |
| PUT | `/habits/{habit_id}` | Update a habit |
| DELETE | `/habits/{habit_id}` | Delete a habit |
| POST | `/habits/{habit_id}/entries` | Log a habit entry |
| GET | `/habits/entries` | Get entries for a date range |

### Notes (`/notes`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/notes/` | Create/update a weekly note |
| GET | `/notes/` | Get note for a specific week |

## Project Structure

```
app/
├── main.py              # FastAPI app, lifespan, CORS, routers
├── core/
│   ├── config.py        # Pydantic Settings (env vars)
│   └── database.py      # MongoDB connection (Motor)
├── auth/
│   ├── routes.py        # Auth endpoints
│   ├── schemas.py       # Auth request/response models
│   ├── utils.py         # Password hashing, JWT helpers
│   └── dependencies.py  # get_current_user dependency
├── tasks/
│   ├── routes.py        # Task CRUD
│   └── schemas.py       # Task models
├── habits/
│   ├── routes.py        # Habit + entry endpoints
│   └── schemas.py       # Habit models
└── notes/
    ├── routes.py        # Notes endpoints
    └── schemas.py       # Note models
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).
