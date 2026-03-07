from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import get_db, close_client
from app.core.config import settings
from app.auth import auth_router
from app.tasks import tasks_router
from app.notes import notes_router
from app.habits import habits_router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    try:
        db = await get_db()
        logger.info("MongoDB connected")
        await db.users.create_index("email", unique=True)
        await db.tasks.create_index([("user_id", 1), ("status", 1)])
        await db.tasks.create_index([("user_id", 1), ("created_at", -1)])
        await db.tasks.create_index([("user_id", 1), ("scheduled_date", 1)])
        await db.notes.create_index([("user_id", 1), ("week_start", 1)])
        await db.habits.create_index([("user_id", 1), ("is_active", 1)])
        await db.habit_entries.create_index(
            [("habit_id", 1), ("date", 1), ("user_id", 1)],
            unique=True,
        )
        await db.habit_entries.create_index([("user_id", 1), ("date", 1)])
        logger.info("Database indexes ensured")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    logger.info("Shutting down...")
    await close_client()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
app.include_router(notes_router, prefix="/notes", tags=["Notes"])
app.include_router(habits_router, prefix="/habits", tags=["Habits"])


@app.get("/", response_class=HTMLResponse)
async def root():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{settings.APP_NAME}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #0ea5e9 0%, #10b981 100%);
            }}
            .container {{ text-align: center; color: white; }}
            h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
            .version {{ opacity: 0.8; margin-bottom: 2rem; }}
            .btn {{
                display: inline-block;
                padding: 12px 32px;
                background: white;
                color: #0ea5e9;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{settings.APP_NAME}</h1>
            <p class="version">v{settings.APP_VERSION}</p>
            <a href="/docs" class="btn">API Docs</a>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
