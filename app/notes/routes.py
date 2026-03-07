from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, date, time, UTC
from bson import ObjectId
from bson.errors import InvalidId
from app.core.database import get_db, log_error
from app.auth.dependencies import get_current_user
from app.notes.schemas import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
)

router = APIRouter()


def _note_to_response(note: dict) -> NoteResponse:
    week_start = note["week_start"]
    if isinstance(week_start, datetime):
        week_start = week_start.date()
    return NoteResponse(
        id=str(note["_id"]),
        content=note["content"],
        is_completed=note["is_completed"],
        week_start=week_start,
        user_id=note["user_id"],
        created_at=note["created_at"],
        updated_at=note["updated_at"],
    )


def _validate_object_id(note_id: str) -> ObjectId:
    try:
        return ObjectId(note_id)
    except (InvalidId, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format",
        )


@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(req: NoteCreate, user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        now = datetime.now(UTC)

        note_doc = {
            "content": req.content,
            "is_completed": req.is_completed,
            "week_start": datetime.combine(req.week_start, time.min),
            "user_id": str(user["_id"]),
            "created_at": now,
            "updated_at": now,
        }

        result = await db.notes.insert_one(note_doc)
        note_doc["_id"] = result.inserted_id
        return _note_to_response(note_doc)

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "notes.create")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create note",
        )


@router.get("/", response_model=NoteListResponse)
async def list_notes(
    week_start: date = Query(..., description="Monday date (YYYY-MM-DD)"),
    user: dict = Depends(get_current_user),
):
    try:
        if week_start.weekday() != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="week_start must be a Monday",
            )

        db = await get_db()
        user_id = str(user["_id"])

        query = {
            "user_id": user_id,
            "week_start": datetime.combine(week_start, time.min),
        }

        total = await db.notes.count_documents(query)
        cursor = db.notes.find(query).sort("created_at", 1)
        notes = [_note_to_response(n) async for n in cursor]

        return NoteListResponse(notes=notes, total=total)

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "notes.list")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notes",
        )


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str, req: NoteUpdate, user: dict = Depends(get_current_user)
):
    try:
        db = await get_db()
        oid = _validate_object_id(note_id)

        update_data = req.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        update_data["updated_at"] = datetime.now(UTC)

        result = await db.notes.find_one_and_update(
            {"_id": oid, "user_id": str(user["_id"])},
            {"$set": update_data},
            return_document=True,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )

        return _note_to_response(result)

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "notes.update")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update note",
        )


@router.delete("/{note_id}")
async def delete_note(note_id: str, user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        oid = _validate_object_id(note_id)

        result = await db.notes.delete_one({"_id": oid, "user_id": str(user["_id"])})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )

        return {"message": "Note deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await log_error(e, "notes.delete")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete note",
        )
