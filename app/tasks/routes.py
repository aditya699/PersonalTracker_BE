from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, date, time, UTC
from bson import ObjectId
from bson.errors import InvalidId
from app.core.database import get_db, log_error
from app.auth.dependencies import get_current_user
from app.tasks.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskStatus,
)

router = APIRouter()


def _task_to_response(task: dict) -> TaskResponse:
    scheduled = task.get("scheduled_date")
    if isinstance(scheduled, datetime):
        scheduled = scheduled.date()
    return TaskResponse(
        id=str(task["_id"]),
        title=task["title"],
        description=task.get("description"),
        status=task["status"],
        scheduled_date=scheduled,
        user_id=task["user_id"],
        created_at=task["created_at"],
        updated_at=task["updated_at"],
    )


def _validate_object_id(task_id: str) -> ObjectId:
    try:
        return ObjectId(task_id)
    except (InvalidId, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format",
        )


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(req: TaskCreate, user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        now = datetime.now(UTC)

        task_doc = {
            "title": req.title,
            "description": req.description,
            "status": TaskStatus.todo.value,
            "scheduled_date": datetime.combine(req.scheduled_date, time.min) if req.scheduled_date else None,
            "user_id": str(user["_id"]),
            "created_at": now,
            "updated_at": now,
        }

        result = await db.tasks.insert_one(task_doc)
        task_doc["_id"] = result.inserted_id
        return _task_to_response(task_doc)

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "tasks.create")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    try:
        db = await get_db()
        user_id = str(user["_id"])

        query = {"user_id": user_id}
        if status_filter:
            query["status"] = status_filter.value

        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = datetime.combine(date_from, time.min)
            if date_to:
                date_query["$lte"] = datetime.combine(date_to, time.max)
            query["scheduled_date"] = date_query

        total = await db.tasks.count_documents(query)
        cursor = db.tasks.find(query).sort("created_at", -1).skip(skip).limit(limit)
        tasks = [_task_to_response(t) async for t in cursor]

        return TaskListResponse(tasks=tasks, total=total)

    except Exception as e:
        await log_error(e, "tasks.list")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tasks",
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        oid = _validate_object_id(task_id)

        task = await db.tasks.find_one({"_id": oid, "user_id": str(user["_id"])})
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return _task_to_response(task)

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "tasks.get")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch task",
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str, req: TaskUpdate, user: dict = Depends(get_current_user)
):
    try:
        db = await get_db()
        oid = _validate_object_id(task_id)

        update_data = req.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        if "status" in update_data:
            update_data["status"] = update_data["status"].value

        if "scheduled_date" in update_data:
            update_data["scheduled_date"] = datetime.combine(
                update_data["scheduled_date"], time.min
            )

        update_data["updated_at"] = datetime.now(UTC)

        result = await db.tasks.find_one_and_update(
            {"_id": oid, "user_id": str(user["_id"])},
            {"$set": update_data},
            return_document=True,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return _task_to_response(result)

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "tasks.update")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task",
        )


@router.delete("/{task_id}")
async def delete_task(task_id: str, user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        oid = _validate_object_id(task_id)

        result = await db.tasks.delete_one({"_id": oid, "user_id": str(user["_id"])})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return {"message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "tasks.delete")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task",
        )
