from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, date, time, UTC
from bson import ObjectId
from bson.errors import InvalidId
from app.core.database import get_db, log_error
from app.auth.dependencies import get_current_user
from app.habits.schemas import (
    HabitCreate,
    HabitUpdate,
    HabitResponse,
    HabitListResponse,
    EntryUpsert,
    EntryResponse,
    EntryListResponse,
)

router = APIRouter()


def _habit_to_response(habit: dict) -> HabitResponse:
    return HabitResponse(
        id=str(habit["_id"]),
        name=habit["name"],
        is_active=habit["is_active"],
        user_id=habit["user_id"],
        created_at=habit["created_at"],
        updated_at=habit["updated_at"],
    )


def _entry_to_response(entry: dict) -> EntryResponse:
    entry_date = entry["date"]
    if isinstance(entry_date, datetime):
        entry_date = entry_date.date()
    return EntryResponse(
        habit_id=entry["habit_id"],
        date=entry_date,
        completed=entry["completed"],
    )


def _validate_object_id(id_str: str, label: str = "ID") -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {label} format",
        )


# GET /entries must be defined before /{habit_id} routes to avoid path collision
@router.get("/entries", response_model=EntryListResponse)
async def list_entries(
    date_from: date = Query(...),
    date_to: date = Query(...),
    user: dict = Depends(get_current_user),
):
    try:
        db = await get_db()
        user_id = str(user["_id"])

        query = {
            "user_id": user_id,
            "date": {
                "$gte": datetime.combine(date_from, time.min),
                "$lte": datetime.combine(date_to, time.max),
            },
        }

        cursor = db.habit_entries.find(query).sort("date", 1)
        entries = [_entry_to_response(e) async for e in cursor]

        return EntryListResponse(entries=entries)

    except Exception as e:
        await log_error(e, "habits.list_entries")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch habit entries",
        )


@router.post("/", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
async def create_habit(req: HabitCreate, user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        now = datetime.now(UTC)

        habit_doc = {
            "name": req.name,
            "is_active": True,
            "user_id": str(user["_id"]),
            "created_at": now,
            "updated_at": now,
        }

        result = await db.habits.insert_one(habit_doc)
        habit_doc["_id"] = result.inserted_id
        return _habit_to_response(habit_doc)

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "habits.create")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create habit",
        )


@router.get("/", response_model=HabitListResponse)
async def list_habits(user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        user_id = str(user["_id"])

        query = {"user_id": user_id, "is_active": True}
        total = await db.habits.count_documents(query)
        cursor = db.habits.find(query).sort("created_at", 1)
        habits = [_habit_to_response(h) async for h in cursor]

        return HabitListResponse(habits=habits, total=total)

    except Exception as e:
        await log_error(e, "habits.list")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch habits",
        )


@router.put("/{habit_id}", response_model=HabitResponse)
async def update_habit(
    habit_id: str, req: HabitUpdate, user: dict = Depends(get_current_user)
):
    try:
        db = await get_db()
        oid = _validate_object_id(habit_id, "habit ID")

        update_data = req.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        update_data["updated_at"] = datetime.now(UTC)

        result = await db.habits.find_one_and_update(
            {"_id": oid, "user_id": str(user["_id"])},
            {"$set": update_data},
            return_document=True,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Habit not found",
            )

        return _habit_to_response(result)

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "habits.update")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update habit",
        )


@router.delete("/{habit_id}")
async def delete_habit(habit_id: str, user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        oid = _validate_object_id(habit_id, "habit ID")
        user_id = str(user["_id"])

        result = await db.habits.delete_one({"_id": oid, "user_id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Habit not found",
            )

        # Cascade delete all entries for this habit
        await db.habit_entries.delete_many({
            "habit_id": str(oid),
            "user_id": user_id,
        })

        return {"message": "Habit deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "habits.delete")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete habit",
        )


@router.put("/{habit_id}/entries/{entry_date}", response_model=EntryResponse)
async def upsert_entry(
    habit_id: str,
    entry_date: date,
    req: EntryUpsert,
    user: dict = Depends(get_current_user),
):
    try:
        db = await get_db()
        oid = _validate_object_id(habit_id, "habit ID")
        user_id = str(user["_id"])

        # Verify habit exists and belongs to user
        habit = await db.habits.find_one({"_id": oid, "user_id": user_id})
        if not habit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Habit not found",
            )

        await db.habit_entries.update_one(
            {
                "habit_id": str(oid),
                "date": datetime.combine(entry_date, time.min),
                "user_id": user_id,
            },
            {
                "$set": {"completed": req.completed},
                "$setOnInsert": {
                    "habit_id": str(oid),
                    "date": datetime.combine(entry_date, time.min),
                    "user_id": user_id,
                },
            },
            upsert=True,
        )

        return EntryResponse(
            habit_id=str(oid),
            date=entry_date,
            completed=req.completed,
        )

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "habits.upsert_entry")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update habit entry",
        )
