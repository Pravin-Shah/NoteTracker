"""
Note-specific database operations for General App.
CRUD operations, tagging, search, and management.
"""

from typing import List, Dict, Optional
from datetime import datetime
from core.db import (
    create_record, update_record, get_record, search_records,
    execute_query, delete_record
)
from core.validators import validate_note_title, validate_importance
from core.exceptions import ValidationError, DatabaseError
import logging

logger = logging.getLogger(__name__)


def create_note(user_id: int, note_data: Dict, db_path: str = None) -> int:
    """
    Create new note.

    Args:
        user_id: User ID
        note_data: {
            'title': str,
            'content': str,
            'category': str ('personal', 'work', 'financial', 'health', 'ideas'),
            'importance': int (1-5, optional),
            'color': str (optional),
        }
        db_path: Path to database (for testing)

    Returns:
        Note ID

    Raises:
        ValidationError: If validation fails
    """
    if not validate_note_title(note_data.get('title', '')):
        raise ValidationError("Invalid note title (3-100 chars)")

    if note_data.get('importance') and not validate_importance(note_data['importance']):
        raise ValidationError("Invalid importance (1-5)")

    note_data['user_id'] = user_id
    note_data.setdefault('importance', 3)  # Default to medium

    note_id = create_record('gen_notes', note_data, db_path)
    logger.info(f"Note created: {note_id} by user {user_id}")
    return note_id


def get_note(user_id: int, note_id: int, db_path: str = None) -> Optional[Dict]:
    """
    Get single note with tags.

    Args:
        user_id: User ID (for verification)
        note_id: Note ID
        db_path: Path to database (for testing)

    Returns:
        Note dict with tags, or None if not found
    """
    note = get_record('gen_notes', note_id, db_path)

    if not note or note['user_id'] != user_id:
        return None

    # Get tags
    tags = execute_query(
        "SELECT tag FROM gen_note_tags WHERE note_id = ?",
        (note_id,),
        db_path
    )
    note['tags'] = [t['tag'] for t in tags]

    # Get attachments
    attachments = execute_query(
        "SELECT id, file_path, file_type FROM gen_note_attachments WHERE note_id = ?",
        (note_id,),
        db_path
    )
    note['attachments'] = [dict(a) for a in attachments]

    return dict(note)


def update_note(user_id: int, note_id: int, updates: Dict, db_path: str = None) -> None:
    """
    Update note.

    Args:
        user_id: User ID (for verification)
        note_id: Note ID
        updates: Fields to update
        db_path: Path to database (for testing)
    """
    note = get_record('gen_notes', note_id, db_path)
    if not note or note['user_id'] != user_id:
        raise ValidationError("Note not found")

    # Validate if title is being updated
    if 'title' in updates and not validate_note_title(updates['title']):
        raise ValidationError("Invalid note title (3-100 chars)")

    if 'importance' in updates and not validate_importance(updates['importance']):
        raise ValidationError("Invalid importance (1-5)")

    update_record('gen_notes', note_id, updates, db_path)
    logger.info(f"Note updated: {note_id}")


def delete_note(user_id: int, note_id: int, db_path: str = None) -> None:
    """
    Delete note (soft delete - archives).

    Args:
        user_id: User ID (for verification)
        note_id: Note ID
        db_path: Path to database (for testing)
    """
    note = get_record('gen_notes', note_id, db_path)
    if not note or note['user_id'] != user_id:
        raise ValidationError("Note not found")

    delete_record('gen_notes', note_id, db_path)
    logger.info(f"Note deleted: {note_id}")


def search_notes(
    user_id: int,
    query: str = "",
    category: str = None,
    importance: int = None,
    tags: List[str] = None,
    archived: bool = False,
    limit: int = 100,
    db_path: str = None
) -> List[Dict]:
    """
    Search notes by text and filters.

    Args:
        user_id: User ID
        query: Search text
        category: Filter by category
        importance: Filter by importance level
        tags: Filter by tags (match any)
        archived: Include archived notes
        limit: Max results
        db_path: Path to database (for testing)

    Returns:
        List of matching notes with tags
    """
    sql = "SELECT * FROM gen_notes WHERE user_id = ?"
    params = [user_id]

    # Search text in title and content
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

    # Archive filter
    if not archived:
        sql += " AND archived = 0"

    # Order by pinned first, then recent
    sql += " ORDER BY pinned DESC, last_updated DESC LIMIT ?"
    params.append(limit)

    results = execute_query(sql, tuple(params), db_path)
    notes = [dict(row) for row in results]

    # Add tags to each note
    if tags:
        # Filter by tags (match any)
        filtered_notes = []
        for note in notes:
            note_tags = execute_query(
                "SELECT tag FROM gen_note_tags WHERE note_id = ?",
                (note['id'],),
                db_path
            )
            note_tag_list = [t['tag'] for t in note_tags]

            # Check if note has any of the requested tags
            if any(tag in note_tag_list for tag in tags):
                note['tags'] = note_tag_list
                filtered_notes.append(note)

        notes = filtered_notes
    else:
        # Add all tags
        for note in notes:
            note_tags = execute_query(
                "SELECT tag FROM gen_note_tags WHERE note_id = ?",
                (note['id'],),
                db_path
            )
            note['tags'] = [t['tag'] for t in note_tags]

    return notes


def pin_note(user_id: int, note_id: int, db_path: str = None) -> None:
    """
    Pin note to top.

    Args:
        user_id: User ID
        note_id: Note ID
        db_path: Path to database (for testing)
    """
    note = get_record('gen_notes', note_id, db_path)
    if not note or note['user_id'] != user_id:
        raise ValidationError("Note not found")

    update_record('gen_notes', note_id, {'pinned': 1}, db_path)
    logger.info(f"Note pinned: {note_id}")


def unpin_note(user_id: int, note_id: int, db_path: str = None) -> None:
    """
    Unpin note.

    Args:
        user_id: User ID
        note_id: Note ID
        db_path: Path to database (for testing)
    """
    note = get_record('gen_notes', note_id, db_path)
    if not note or note['user_id'] != user_id:
        raise ValidationError("Note not found")

    update_record('gen_notes', note_id, {'pinned': 0}, db_path)
    logger.info(f"Note unpinned: {note_id}")


def archive_note(user_id: int, note_id: int, db_path: str = None) -> None:
    """
    Archive note.

    Args:
        user_id: User ID
        note_id: Note ID
        db_path: Path to database (for testing)
    """
    note = get_record('gen_notes', note_id, db_path)
    if not note or note['user_id'] != user_id:
        raise ValidationError("Note not found")

    update_record('gen_notes', note_id, {'archived': 1}, db_path)
    logger.info(f"Note archived: {note_id}")


def unarchive_note(user_id: int, note_id: int, db_path: str = None) -> None:
    """
    Unarchive note.

    Args:
        user_id: User ID
        note_id: Note ID
        db_path: Path to database (for testing)
    """
    note = get_record('gen_notes', note_id, db_path)
    if not note or note['user_id'] != user_id:
        raise ValidationError("Note not found")

    update_record('gen_notes', note_id, {'archived': 0}, db_path)
    logger.info(f"Note unarchived: {note_id}")


def get_pinned_notes(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Get all pinned notes.

    Args:
        user_id: User ID
        db_path: Path to database (for testing)

    Returns:
        List of pinned notes
    """
    results = search_records('gen_notes', {
        'user_id': user_id,
        'pinned': 1,
        'archived': 0
    }, db_path)

    notes = [dict(row) for row in results]

    # Add tags
    for note in notes:
        note_tags = execute_query(
            "SELECT tag FROM gen_note_tags WHERE note_id = ?",
            (note['id'],),
            db_path
        )
        note['tags'] = [t['tag'] for t in note_tags]

    return notes


def add_note_tag(note_id: int, tag: str, db_path: str = None) -> None:
    """
    Add tag to note.

    Args:
        note_id: Note ID
        tag: Tag name
        db_path: Path to database (for testing)
    """
    try:
        create_record('gen_note_tags', {
            'note_id': note_id,
            'tag': tag.lower()  # Normalize to lowercase
        }, db_path)
        logger.info(f"Tag added to note {note_id}: {tag}")
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            logger.debug(f"Tag already exists on note {note_id}: {tag}")
        else:
            raise


def remove_note_tag(note_id: int, tag: str, db_path: str = None) -> None:
    """
    Remove tag from note.

    Args:
        note_id: Note ID
        tag: Tag name
        db_path: Path to database (for testing)
    """
    from core.db import execute_update
    execute_update(
        "DELETE FROM gen_note_tags WHERE note_id = ? AND tag = ?",
        (note_id, tag.lower()),
        db_path
    )
    logger.info(f"Tag removed from note {note_id}: {tag}")


def add_note_attachment(note_id: int, file_path: str, file_type: str = None, db_path: str = None) -> int:
    """
    Add attachment to note.

    Args:
        note_id: Note ID
        file_path: Path to file
        file_type: File type ('image', 'document', 'pdf')
        db_path: Path to database (for testing)

    Returns:
        Attachment ID
    """
    attachment_id = create_record('gen_note_attachments', {
        'note_id': note_id,
        'file_path': file_path,
        'file_type': file_type
    }, db_path)
    logger.info(f"Attachment added to note {note_id}: {file_path}")
    return attachment_id


def remove_note_attachment(attachment_id: int, db_path: str = None) -> None:
    """
    Remove attachment from note.

    Args:
        attachment_id: Attachment ID
        db_path: Path to database (for testing)
    """
    from core.db import execute_update
    execute_update(
        "DELETE FROM gen_note_attachments WHERE id = ?",
        (attachment_id,),
        db_path
    )
    logger.info(f"Attachment removed: {attachment_id}")


def get_note_categories(user_id: int, db_path: str = None) -> List[str]:
    """
    Get all categories used by user's notes.

    Args:
        user_id: User ID
        db_path: Path to database (for testing)

    Returns:
        List of categories
    """
    results = execute_query(
        "SELECT DISTINCT category FROM gen_notes WHERE user_id = ? AND category IS NOT NULL ORDER BY category",
        (user_id,),
        db_path
    )
    return [row['category'] for row in results]


def get_note_tags(user_id: int, db_path: str = None) -> List[str]:
    """
    Get all tags used in user's notes.

    Args:
        user_id: User ID
        db_path: Path to database (for testing)

    Returns:
        List of tags (alphabetically sorted)
    """
    results = execute_query(
        """SELECT DISTINCT tag FROM gen_note_tags
           WHERE note_id IN (SELECT id FROM gen_notes WHERE user_id = ?)
           ORDER BY tag""",
        (user_id,),
        db_path
    )
    return [row['tag'] for row in results]


def get_note_stats(user_id: int, db_path: str = None) -> Dict:
    """
    Get note statistics for user.

    Args:
        user_id: User ID
        db_path: Path to database (for testing)

    Returns:
        Stats dict
    """
    total = execute_query(
        "SELECT COUNT(*) as count FROM gen_notes WHERE user_id = ?",
        (user_id,),
        db_path
    )

    pinned = execute_query(
        "SELECT COUNT(*) as count FROM gen_notes WHERE user_id = ? AND pinned = 1",
        (user_id,),
        db_path
    )

    archived = execute_query(
        "SELECT COUNT(*) as count FROM gen_notes WHERE user_id = ? AND archived = 1",
        (user_id,),
        db_path
    )

    by_category = execute_query(
        "SELECT category, COUNT(*) as count FROM gen_notes WHERE user_id = ? AND archived = 0 GROUP BY category",
        (user_id,),
        db_path
    )

    return {
        'total': total[0]['count'] if total else 0,
        'pinned': pinned[0]['count'] if pinned else 0,
        'archived': archived[0]['count'] if archived else 0,
        'active': (total[0]['count'] if total else 0) - (archived[0]['count'] if archived else 0),
        'by_category': {row['category']: row['count'] for row in by_category} if by_category else {}
    }


def bulk_add_tags(note_ids: List[int], tags: List[str], db_path: str = None) -> None:
    """
    Add tags to multiple notes.

    Args:
        note_ids: List of note IDs
        tags: List of tags to add
        db_path: Path to database (for testing)
    """
    for note_id in note_ids:
        for tag in tags:
            add_note_tag(note_id, tag, db_path)

    logger.info(f"Bulk tags added to {len(note_ids)} notes")


def bulk_delete_notes(user_id: int, note_ids: List[int], db_path: str = None) -> None:
    """
    Delete multiple notes.

    Args:
        user_id: User ID
        note_ids: List of note IDs to delete
        db_path: Path to database (for testing)
    """
    for note_id in note_ids:
        try:
            delete_note(user_id, note_id, db_path)
        except Exception as e:
            logger.warning(f"Failed to delete note {note_id}: {e}")

    logger.info(f"Bulk deleted {len(note_ids)} notes")


def export_notes(user_id: int, format: str = 'json', db_path: str = None) -> List[Dict]:
    """
    Export all notes for user.

    Args:
        user_id: User ID
        format: Export format ('json', 'csv')
        db_path: Path to database (for testing)

    Returns:
        List of note dicts ready for export
    """
    notes = search_notes(user_id, limit=10000, db_path=db_path)

    # Add full details
    for note in notes:
        # Already has tags from search
        attachments = execute_query(
            "SELECT id, file_path, file_type FROM gen_note_attachments WHERE note_id = ?",
            (note['id'],),
            db_path
        )
        note['attachments'] = [dict(a) for a in attachments]

    logger.info(f"Exported {len(notes)} notes for user {user_id}")
    return notes
