from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, UTC
from app.core.database import get_db, log_error
from app.core.config import settings
from app.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    UserProfile,
)
from app.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.auth.dependencies import get_current_user
from jose import JWTError

router = APIRouter()


def _make_token_response(user_id: str) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_DAYS * 86400,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    try:
        db = await get_db()

        existing = await db.users.find_one({"email": req.email.lower()})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        now = datetime.now(UTC)
        user_doc = {
            "email": req.email.lower(),
            "name": req.name,
            "password": hash_password(req.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "last_login": now,
        }

        result = await db.users.insert_one(user_doc)
        return _make_token_response(str(result.inserted_id))

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "auth.register")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    try:
        db = await get_db()

        user = await db.users.find_one({"email": req.email.lower()})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(req.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.now(UTC)}},
        )

        return _make_token_response(str(user["_id"]))

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "auth.login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: TokenRefreshRequest):
    try:
        payload = verify_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = payload.get("sub")
        return _make_token_response(user_id)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "auth.refresh")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.get("/me", response_model=UserProfile)
async def me(user: dict = Depends(get_current_user)):
    return UserProfile(
        user_id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        created_at=user["created_at"],
        is_active=user["is_active"],
    )
