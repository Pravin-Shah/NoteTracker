"""
Prompt management for TradeVault App.
Reusable analysis prompts with versioning support.
"""

from typing import List, Dict, Optional
from datetime import datetime
from core.db import (
    create_record, update_record, get_record, search_records,
    execute_query, delete_record
)
from core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


def create_prompt(user_id: int, prompt_data: Dict, db_path: str = None) -> int:
    """
    Create new prompt template.

    Args:
        user_id: User ID
        prompt_data: {
            'title': str,
            'category': str ('analysis', 'debugging', 'hypothesis', 'research'),
            'content': str,
            'use_case': str (optional),
            'expected_output': str (optional),
            'version': str (default: '1.0'),
            'status': str ('active', 'archived', default: 'active'),
        }

    Returns:
        Prompt ID

    Raises:
        ValidationError: If validation fails
    """
    if not prompt_data.get('title') or len(prompt_data['title']) < 3:
        raise ValidationError("Prompt title is required (min 3 chars)")

    if not prompt_data.get('content') or len(prompt_data['content']) < 10:
        raise ValidationError("Prompt content is required (min 10 chars)")

    if not prompt_data.get('category'):
        raise ValidationError("Category is required")

    prompt_data['user_id'] = user_id
    prompt_data.setdefault('version', '1.0')
    prompt_data.setdefault('status', 'active')
    prompt_data.setdefault('usage_count', 0)
    prompt_data.setdefault('is_favorite', 0)

    prompt_id = create_record('tv_prompts', prompt_data, db_path)

    # Create version entry
    create_record('tv_prompt_versions', {
        'prompt_id': prompt_id,
        'version': prompt_data['version'],
        'content': prompt_data['content']
    }, db_path)

    logger.info(f"Prompt created: {prompt_id} by user {user_id}")
    return prompt_id


def get_prompt(user_id: int, prompt_id: int, db_path: str = None) -> Optional[Dict]:
    """
    Get single prompt with tags and version history.

    Args:
        user_id: User ID (for verification)
        prompt_id: Prompt ID

    Returns:
        Prompt dict with tags and versions
    """
    prompt = get_record('tv_prompts', prompt_id, db_path)

    if not prompt or prompt['user_id'] != user_id:
        return None

    prompt = dict(prompt)

    # Get tags
    tags = execute_query(
        "SELECT tag FROM tv_prompt_tags WHERE prompt_id = ?",
        (prompt_id,),
        db_path
    )
    prompt['tags'] = [t['tag'] for t in tags]

    # Get version history
    versions = execute_query(
        "SELECT version, modified_date FROM tv_prompt_versions WHERE prompt_id = ? ORDER BY modified_date DESC",
        (prompt_id,),
        db_path
    )
    prompt['version_history'] = [dict(v) for v in versions]

    return prompt


def update_prompt(user_id: int, prompt_id: int, updates: Dict, create_version: bool = False, db_path: str = None) -> None:
    """
    Update prompt.

    Args:
        user_id: User ID
        prompt_id: Prompt ID
        updates: Fields to update
        create_version: If True, creates a new version when content changes
    """
    prompt = get_record('tv_prompts', prompt_id, db_path)
    if not prompt or prompt['user_id'] != user_id:
        raise ValidationError("Prompt not found")

    # If content is being updated, create new version
    if create_version and 'content' in updates:
        new_version = updates.get('version', prompt['version'])

        # Create version entry
        create_record('tv_prompt_versions', {
            'prompt_id': prompt_id,
            'version': new_version,
            'content': updates['content']
        }, db_path)

    update_record('tv_prompts', prompt_id, updates, db_path)
    logger.info(f"Prompt updated: {prompt_id}")


def delete_prompt(user_id: int, prompt_id: int, db_path: str = None) -> None:
    """
    Delete prompt.

    Args:
        user_id: User ID
        prompt_id: Prompt ID
    """
    prompt = get_record('tv_prompts', prompt_id, db_path)
    if not prompt or prompt['user_id'] != user_id:
        raise ValidationError("Prompt not found")

    # Archive instead of delete
    update_record('tv_prompts', prompt_id, {'status': 'archived'}, db_path)
    logger.info(f"Prompt archived: {prompt_id}")


def search_prompts(
    user_id: int,
    query: str = "",
    category: str = None,
    status: str = None,
    tags: List[str] = None,
    limit: int = 100, db_path: str = None) -> List[Dict]:
    """
    Search prompts by text and filters.

    Args:
        user_id: User ID
        query: Search text
        category: Filter by category
        status: Filter by status
        tags: Filter by tags
        limit: Max results

    Returns:
        List of matching prompts
    """
    sql = "SELECT * FROM tv_prompts WHERE user_id = ?"
    params = [user_id]

    if query:
        sql += " AND (title LIKE ? OR content LIKE ? OR use_case LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

    if category:
        sql += " AND category = ?"
        params.append(category)

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY is_favorite DESC, last_used_date DESC, created_date DESC LIMIT ?"
    params.append(limit)

    results = execute_query(sql, tuple(params, db_path))
    prompts = [dict(row) for row in results]

    # Add tags if filtering
    if tags:
        filtered_prompts = []
        for prompt in prompts:
            prompt_tags = execute_query(
                "SELECT tag FROM tv_prompt_tags WHERE prompt_id = ?",
                (prompt['id'], db_path)
            )
            prompt_tag_list = [t['tag'] for t in prompt_tags]

            if any(tag in prompt_tag_list for tag in tags):
                prompt['tags'] = prompt_tag_list
                filtered_prompts.append(prompt)

        prompts = filtered_prompts
    else:
        for prompt in prompts:
            prompt_tags = execute_query(
                "SELECT tag FROM tv_prompt_tags WHERE prompt_id = ?",
                (prompt['id'], db_path)
            )
            prompt['tags'] = [t['tag'] for t in prompt_tags]

    return prompts


def get_favorite_prompts(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Get user's favorite prompts.

    Args:
        user_id: User ID

    Returns:
        List of favorite prompts
    """
    results = execute_query("""
        SELECT * FROM tv_prompts
        WHERE user_id = ? AND is_favorite = 1 AND status = 'active'
        ORDER BY last_used_date DESC
    """, (user_id, db_path))

    prompts = [dict(row) for row in results]

    for prompt in prompts:
        tags = execute_query(
            "SELECT tag FROM tv_prompt_tags WHERE prompt_id = ?",
            (prompt['id'], db_path)
        )
        prompt['tags'] = [t['tag'] for t in tags]

    return prompts


def use_prompt(prompt_id: int, db_path: str = None) -> None:
    """
    Record prompt usage.

    Args:
        prompt_id: Prompt ID
    """
    prompt = get_record('tv_prompts', prompt_id, db_path)
    if prompt:
        update_record('tv_prompts', prompt_id, {
            'last_used_date': datetime.now().isoformat(),
            'usage_count': (prompt['usage_count'] or 0) + 1
        }, db_path)


def toggle_favorite(user_id: int, prompt_id: int, db_path: str = None) -> bool:
    """
    Toggle favorite status for prompt.

    Args:
        user_id: User ID
        prompt_id: Prompt ID

    Returns:
        New favorite status
    """
    prompt = get_record('tv_prompts', prompt_id, db_path)
    if not prompt or prompt['user_id'] != user_id:
        raise ValidationError("Prompt not found")

    new_status = 1 - prompt['is_favorite']
    update_record('tv_prompts', prompt_id, {'is_favorite': new_status}, db_path)
    logger.info(f"Prompt favorite toggled: {prompt_id} -> {new_status}")
    return bool(new_status)


def add_prompt_tag(prompt_id: int, tag: str, db_path: str = None) -> None:
    """
    Add tag to prompt.

    Args:
        prompt_id: Prompt ID
        tag: Tag name
    """
    try:
        create_record('tv_prompt_tags', {
            'prompt_id': prompt_id,
            'tag': tag.lower()
        }, db_path)
        logger.info(f"Tag added to prompt {prompt_id}: {tag}")
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            logger.debug(f"Tag already exists on prompt {prompt_id}: {tag}")
        else:
            raise


def remove_prompt_tag(prompt_id: int, tag: str, db_path: str = None) -> None:
    """
    Remove tag from prompt.

    Args:
        prompt_id: Prompt ID
        tag: Tag name
    """
    from core.db import execute_update
    execute_update(
        "DELETE FROM tv_prompt_tags WHERE prompt_id = ? AND tag = ?",
        (prompt_id, tag.lower()),
        db_path
    )


def get_prompt_version(prompt_id: int, version: str, db_path: str = None) -> Optional[Dict]:
    """
    Get specific version of prompt.

    Args:
        prompt_id: Prompt ID
        version: Version string

    Returns:
        Prompt version dict or None
    """
    results = execute_query(
        "SELECT * FROM tv_prompt_versions WHERE prompt_id = ? AND version = ? LIMIT 1",
        (prompt_id, version, db_path)
    )
    return dict(results[0]) if results else None


def get_prompt_version_history(prompt_id: int, db_path: str = None) -> List[Dict]:
    """
    Get version history for prompt.

    Args:
        prompt_id: Prompt ID

    Returns:
        List of versions with timestamps
    """
    results = execute_query("""
        SELECT version, modified_date FROM tv_prompt_versions
        WHERE prompt_id = ?
        ORDER BY modified_date DESC
    """, (prompt_id, db_path))

    return [dict(row) for row in results]


def restore_prompt_version(user_id: int, prompt_id: int, version: str, db_path: str = None) -> None:
    """
    Restore prompt to previous version.

    Args:
        user_id: User ID
        prompt_id: Prompt ID
        version: Version to restore
    """
    prompt = get_record('tv_prompts', prompt_id, db_path)
    if not prompt or prompt['user_id'] != user_id:
        raise ValidationError("Prompt not found")

    version_data = get_prompt_version(prompt_id, version)
    if not version_data:
        raise ValidationError(f"Version {version} not found")

    # Update prompt with old content
    update_record('tv_prompts', prompt_id, {
        'content': version_data['content'],
        'version': version
    }, db_path)

    logger.info(f"Prompt restored to version {version}: {prompt_id}")


def get_prompt_categories(user_id: int, db_path: str = None) -> List[str]:
    """
    Get all prompt categories used by user.

    Args:
        user_id: User ID

    Returns:
        List of categories
    """
    results = execute_query(
        "SELECT DISTINCT category FROM tv_prompts WHERE user_id = ? ORDER BY category",
        (user_id, db_path)
    )
    return [row['category'] for row in results]


def get_prompt_tags(user_id: int, db_path: str = None) -> List[str]:
    """
    Get all tags used in user's prompts.

    Args:
        user_id: User ID

    Returns:
        List of tags
    """
    results = execute_query(
        """SELECT DISTINCT tag FROM tv_prompt_tags
           WHERE prompt_id IN (SELECT id FROM tv_prompts WHERE user_id = ?, db_path)
           ORDER BY tag""",
        (user_id,)
    )
    return [row['tag'] for row in results]


def get_prompt_stats(user_id: int, db_path: str = None) -> Dict:
    """
    Get prompt statistics for user.

    Args:
        user_id: User ID

    Returns:
        Stats dict
    """
    total = execute_query(
        "SELECT COUNT(*) as count FROM tv_prompts WHERE user_id = ?",
        (user_id,),
        db_path
    )

    active = execute_query(
        "SELECT COUNT(*) as count FROM tv_prompts WHERE user_id = ? AND status = 'active'",
        (user_id,),
        db_path
    )

    favorites = execute_query(
        "SELECT COUNT(*) as count FROM tv_prompts WHERE user_id = ? AND is_favorite = 1",
        (user_id,),
        db_path
    )

    by_category = execute_query(
        "SELECT category, COUNT(*) as count FROM tv_prompts WHERE user_id = ? GROUP BY category",
        (user_id,),
        db_path
    )

    most_used = execute_query(
        "SELECT MAX(usage_count) as max_used FROM tv_prompts WHERE user_id = ?",
        (user_id,),
        db_path
    )

    return {
        'total': total[0]['count'] if total else 0,
        'active': active[0]['count'] if active else 0,
        'favorites': favorites[0]['count'] if favorites else 0,
        'by_category': {row['category']: row['count'] for row in by_category} if by_category else {},
        'most_used': most_used[0]['max_used'] if most_used else 0
    }


def export_prompts(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Export all user's prompts.

    Args:
        user_id: User ID

    Returns:
        List of all prompts ready for export
    """
    results = execute_query(
        "SELECT * FROM tv_prompts WHERE user_id = ? ORDER BY created_date DESC",
        (user_id, db_path)
    )

    prompts = [dict(row) for row in results]

    for prompt in prompts:
        tags = execute_query(
            "SELECT tag FROM tv_prompt_tags WHERE prompt_id = ?",
            (prompt['id'], db_path)
        )
        prompt['tags'] = [t['tag'] for t in tags]

    logger.info(f"Exported {len(prompts)} prompts for user {user_id}")
    return prompts
