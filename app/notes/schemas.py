from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from typing import Optional


class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    week_start: date = Field(..., description="Must be a Monday (YYYY-MM-DD)")
    is_completed: bool = False

    @field_validator("week_start")
    @classmethod
    def validate_monday(cls, v: date) -> date:
        if v.weekday() != 0:
            raise ValueError("week_start must be a Monday")
        return v


class NoteUpdate(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    is_completed: Optional[bool] = None


class NoteResponse(BaseModel):
    id: str
    content: str
    is_completed: bool
    week_start: date
    user_id: str
    created_at: datetime
    updated_at: datetime


class NoteListResponse(BaseModel):
    notes: list[NoteResponse]
    total: int
