"""
Notes API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from typing import Optional, List
from datetime import datetime
import uuid
import os

from api.models.note import (
    NoteCreate, NoteUpdate, NoteResponse, NoteListResponse,
    NoteStatsResponse, TagListResponse, CategoryListResponse, AttachmentResponse
)
from api.database import execute_query, execute_insert, execute_update, get_record_by_id
from api.config import DEFAULT_USER_ID, UPLOADS_DIR, MAX_FILE_SIZE, ALLOWED_FILE_TYPES
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/notes", tags=["notes"])


# ============== Helper Functions ==============

def get_note_tags(note_id: int) -> List[str]:
    """Get tags for a note."""
    results = execute_query(
        "SELECT tag FROM gen_note_tags WHERE note_id = ?",
        (note_id,)
    )
    return [r['tag'] for r in results]


def get_note_attachments(note_id: int) -> List[dict]:
    """Get attachments for a note."""
    results = execute_query(
        "SELECT id, file_path, file_type, upload_date FROM gen_note_attachments WHERE note_id = ?",
        (note_id,)
    )
    return results


def set_note_tags(note_id: int, tags: List[str]):
    """Set tags for a note (replace existing)."""
    # Delete existing tags
    execute_update("DELETE FROM gen_note_tags WHERE note_id = ?", (note_id,))

    # Add new tags
    for tag in tags:
        tag_lower = tag.lower().strip()
        if tag_lower:
            try:
                execute_insert(
                    "INSERT INTO gen_note_tags (note_id, tag) VALUES (?, ?)",
                    (note_id, tag_lower)
                )
            except Exception:
                pass  # Ignore duplicate tags


def note_to_response(note: dict) -> NoteResponse:
    """Convert database note to response model."""
    tags = get_note_tags(note['id'])
    attachments = get_note_attachments(note['id'])

    return NoteResponse(
        id=note['id'],
        user_id=note['user_id'],
        title=note['title'],
        content=note['content'] or '',
        category=note.get('category'),
        importance=note.get('importance', 3),
        color=note.get('color'),
        created_date=note.get('created_date'),
        last_updated=note.get('last_updated'),
        archived=note.get('archived', 0),
        pinned=note.get('pinned', 0),
        tags=tags,
        attachments=[AttachmentResponse(**a) for a in attachments]
    )


# ============== API Endpoints ==============

@router.get("", response_model=NoteListResponse)
async def list_notes(
    query: Optional[str] = Query(None, description="Search text"),
    category: Optional[str] = Query(None, description="Filter by category"),
    importance: Optional[int] = Query(None, ge=1, le=5, description="Filter by importance"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    archived: bool = Query(False, description="Include archived notes"),
    pinned_only: bool = Query(False, description="Only pinned notes"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user)
):
    """List notes with optional filters."""
    user_id = current_user['id']

    sql = "SELECT * FROM gen_notes WHERE user_id = ?"
    params = [user_id]

    # Text search
    if query:
        sql += " AND (title LIKE ? OR content LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])

    # Category filter
    if category:
        sql += " AND category = ?"
        params.append(category)

    # Importance filter
    if importance:
        sql += " AND importance = ?"
        params.append(importance)

    # Archive filter - when archived=True, show ONLY archived; when False, show ONLY non-archived
    if archived:
        sql += " AND archived = 1"
    else:
        sql += " AND archived = 0"

    # Pinned only (for favorites)
    if pinned_only:
        sql += " AND pinned = 1"

    # Order and pagination
    sql += " ORDER BY pinned DESC, last_updated DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    results = execute_query(sql, tuple(params))

    # Filter by tag if specified
    notes = []
    for note in results:
        if tag:
            note_tags = get_note_tags(note['id'])
            if tag.lower() not in note_tags:
                continue
        notes.append(note_to_response(note))

    # Get total count
    count_sql = "SELECT COUNT(*) as count FROM gen_notes WHERE user_id = ?"
    count_params = [user_id]
    if archived:
        count_sql += " AND archived = 1"
    else:
        count_sql += " AND archived = 0"
    total = execute_query(count_sql, tuple(count_params))[0]['count']

    return NoteListResponse(notes=notes, total=total)


@router.get("/tags", response_model=TagListResponse)
async def get_tags(current_user: dict = Depends(get_current_user)):
    """Get all tags used in notes."""
    user_id = current_user['id']

    results = execute_query(
        """SELECT DISTINCT tag FROM gen_note_tags
           WHERE note_id IN (SELECT id FROM gen_notes WHERE user_id = ?)
           ORDER BY tag""",
        (user_id,)
    )

    return TagListResponse(tags=[r['tag'] for r in results])


@router.get("/categories", response_model=CategoryListResponse)
async def get_categories(current_user: dict = Depends(get_current_user)):
    """Get all categories used in notes."""
    user_id = current_user['id']

    results = execute_query(
        """SELECT DISTINCT category FROM gen_notes
           WHERE user_id = ? AND category IS NOT NULL
           ORDER BY category""",
        (user_id,)
    )

    return CategoryListResponse(categories=[r['category'] for r in results])


@router.get("/stats", response_model=NoteStatsResponse)
async def get_stats(current_user: dict = Depends(get_current_user)):
    """Get note statistics."""
    user_id = current_user['id']

    total = execute_query(
        "SELECT COUNT(*) as count FROM gen_notes WHERE user_id = ?",
        (user_id,)
    )[0]['count']

    pinned = execute_query(
        "SELECT COUNT(*) as count FROM gen_notes WHERE user_id = ? AND pinned = 1",
        (user_id,)
    )[0]['count']

    archived = execute_query(
        "SELECT COUNT(*) as count FROM gen_notes WHERE user_id = ? AND archived = 1",
        (user_id,)
    )[0]['count']

    by_category = execute_query(
        """SELECT category, COUNT(*) as count FROM gen_notes
           WHERE user_id = ? AND archived = 0
           GROUP BY category""",
        (user_id,)
    )

    return NoteStatsResponse(
        total=total,
        pinned=pinned,
        archived=archived,
        active=total - archived,
        by_category={r['category'] or 'uncategorized': r['count'] for r in by_category}
    )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """Get a single note by ID."""
    user_id = current_user['id']

    note = get_record_by_id('gen_notes', note_id)

    if not note or note['user_id'] != user_id:
        raise HTTPException(status_code=404, detail="Note not found")

    return note_to_response(note)


@router.post("", response_model=NoteResponse, status_code=201)
async def create_note(note_data: NoteCreate, current_user: dict = Depends(get_current_user)):
    """Create a new note."""
    user_id = current_user['id']

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    note_id = execute_insert(
        """INSERT INTO gen_notes
           (user_id, title, content, category, importance, color, created_date, last_updated, archived, pinned)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0)""",
        (user_id, note_data.title, note_data.content, note_data.category,
         note_data.importance, note_data.color, now, now)
    )

    # Add tags
    if note_data.tags:
        set_note_tags(note_id, note_data.tags)

    note = get_record_by_id('gen_notes', note_id)
    return note_to_response(note)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: int, note_data: NoteUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing note."""
    user_id = current_user['id']

    note = get_record_by_id('gen_notes', note_id)
    if not note or note['user_id'] != user_id:
        raise HTTPException(status_code=404, detail="Note not found")

    # Build update query
    updates = []
    params = []

    if note_data.title is not None:
        updates.append("title = ?")
        params.append(note_data.title)

    if note_data.content is not None:
        updates.append("content = ?")
        params.append(note_data.content)

    if note_data.category is not None:
        updates.append("category = ?")
        params.append(note_data.category)

    if note_data.importance is not None:
        updates.append("importance = ?")
        params.append(note_data.importance)

    if note_data.color is not None:
        updates.append("color = ?")
        params.append(note_data.color)

    if updates:
        updates.append("last_updated = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        params.append(note_id)

        sql = f"UPDATE gen_notes SET {', '.join(updates)} WHERE id = ?"
        execute_update(sql, tuple(params))

    # Update tags if provided
    if note_data.tags is not None:
        set_note_tags(note_id, note_data.tags)

    note = get_record_by_id('gen_notes', note_id)
    return note_to_response(note)


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """Delete (archive) a note."""
    user_id = current_user['id']

    note = get_record_by_id('gen_notes', note_id)
    if not note or note['user_id'] != user_id:
        raise HTTPException(status_code=404, detail="Note not found")

    # Soft delete - archive the note
    execute_update(
        "UPDATE gen_notes SET archived = 1, last_updated = ? WHERE id = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), note_id)
    )


@router.delete("/{note_id}/permanent", status_code=204)
async def permanent_delete_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """Permanently delete a note and all its attachments."""
    user_id = current_user['id']

    note = get_record_by_id('gen_notes', note_id)
    if not note or note['user_id'] != user_id:
        raise HTTPException(status_code=404, detail="Note not found")

    # Delete attachments from disk
    attachments = execute_query(
        "SELECT file_path FROM gen_note_attachments WHERE note_id = ?",
        (note_id,)
    )
    for attachment in attachments:
        file_path = UPLOADS_DIR / attachment['file_path']
        if file_path.exists():
            import os
            os.remove(file_path)

    # Delete from database
    execute_update("DELETE FROM gen_note_attachments WHERE note_id = ?", (note_id,))
    execute_update("DELETE FROM gen_note_tags WHERE note_id = ?", (note_id,))
    execute_update("DELETE FROM gen_notes WHERE id = ?", (note_id,))


@router.post("/{note_id}/pin", response_model=NoteResponse)
async def toggle_pin(note_id: int, pin: bool = Query(True), current_user: dict = Depends(get_current_user)):
    """Pin or unpin a note."""
    user_id = current_user['id']

    note = get_record_by_id('gen_notes', note_id)
    if not note or note['user_id'] != user_id:
        raise HTTPException(status_code=404, detail="Note not found")

    execute_update(
        "UPDATE gen_notes SET pinned = ?, last_updated = ? WHERE id = ?",
        (1 if pin else 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), note_id)
    )

    note = get_record_by_id('gen_notes', note_id)
    return note_to_response(note)


@router.post("/{note_id}/archive", response_model=NoteResponse)
async def toggle_archive(note_id: int, archive: bool = Query(True), current_user: dict = Depends(get_current_user)):
    """Archive or restore a note."""
    user_id = current_user['id']

    note = get_record_by_id('gen_notes', note_id)
    if not note or note['user_id'] != user_id:
        raise HTTPException(status_code=404, detail="Note not found")

    execute_update(
        "UPDATE gen_notes SET archived = ?, last_updated = ? WHERE id = ?",
        (1 if archive else 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), note_id)
    )

    note = get_record_by_id('gen_notes', note_id)
    return note_to_response(note)


@router.post("/{note_id}/attachments", response_model=AttachmentResponse)
async def upload_attachment(note_id: int, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload an image/file attachment to a note."""
    user_id = current_user['id']

    # Verify note exists and belongs to user
    note = get_record_by_id('gen_notes', note_id)
    if not note or note['user_id'] != user_id:
        raise HTTPException(status_code=404, detail="Note not found")

    # Validate file type
    if file.filename:
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    else:
        # For pasted images, default to png
        ext = 'png'

    if ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {ALLOWED_FILE_TYPES}")

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB")

    # Generate unique filename
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = UPLOADS_DIR / unique_name

    # Ensure uploads directory exists
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Save file
    with open(file_path, 'wb') as f:
        f.write(content)

    # Determine file type
    file_type = 'image' if ext in {'jpg', 'jpeg', 'png', 'gif', 'webp'} else 'document'

    # Save to database
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    attachment_id = execute_insert(
        "INSERT INTO gen_note_attachments (note_id, file_path, file_type, upload_date) VALUES (?, ?, ?, ?)",
        (note_id, unique_name, file_type, now)
    )

    return AttachmentResponse(
        id=attachment_id,
        file_path=unique_name,
        file_type=file_type,
        upload_date=now
    )


@router.delete("/{note_id}/attachments/{attachment_id}", status_code=204)
async def delete_attachment(note_id: int, attachment_id: int, current_user: dict = Depends(get_current_user)):
    """Delete an attachment from a note."""
    user_id = current_user['id']

    # Verify note exists and belongs to user
    note = get_record_by_id('gen_notes', note_id)
    if not note or note['user_id'] != user_id:
        raise HTTPException(status_code=404, detail="Note not found")

    # Get attachment
    attachments = execute_query(
        "SELECT * FROM gen_note_attachments WHERE id = ? AND note_id = ?",
        (attachment_id, note_id)
    )
    if not attachments:
        raise HTTPException(status_code=404, detail="Attachment not found")

    attachment = attachments[0]

    # Delete file from disk
    file_path = UPLOADS_DIR / attachment['file_path']
    if file_path.exists():
        os.remove(file_path)

    # Delete from database
    execute_update("DELETE FROM gen_note_attachments WHERE id = ?", (attachment_id,))
