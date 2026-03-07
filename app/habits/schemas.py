from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional


class HabitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class HabitUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    is_active: Optional[bool] = None


class HabitResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    user_id: str
    created_at: datetime
    updated_at: datetime


class HabitListResponse(BaseModel):
    habits: list[HabitResponse]
    total: int


class EntryUpsert(BaseModel):
    completed: bool


class EntryResponse(BaseModel):
    habit_id: str
    date: date
    completed: bool


class EntryListResponse(BaseModel):
    entries: list[EntryResponse]
