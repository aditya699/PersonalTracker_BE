from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class TaskStatus(str, Enum):
    todo = "todo"
    doing = "doing"
    testing = "testing"
    done = "done"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[TaskStatus] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus
    user_id: str
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
