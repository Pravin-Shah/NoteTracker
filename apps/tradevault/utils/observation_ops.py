"""
Observation-specific database operations for TradeVault App.
Manage trading observations, screenshots, and tags.
"""

from typing import List, Dict, Optional
from core.db import (
    create_record, get_record, execute_query, execute_update
)
import logging

logger = logging.getLogger(__name__)

def create_observation(user_id: int, observation_data: Dict) -> int:
    """
    Create a new observation.
    
    Args:
        user_id: User ID
        observation_data: {
            'stock_name': str,
            'observation_text': str
        }
    """
    observation_data['user_id'] = user_id
    obs_id = create_record('tv_observations', observation_data)
    logger.info(f"Observation created: {obs_id}")
    return obs_id

def get_observation(observation_id: int) -> Optional[Dict]:
    """Get observation by ID with tags and screenshots."""
    obs = get_record('tv_observations', observation_id)
    if not obs:
        return None
        
    obs = dict(obs)
    
    # Tags
    tags = execute_query(
        "SELECT tag FROM tv_observation_tags WHERE observation_id = ?",
        (observation_id,)
    )
    obs['tags'] = [t['tag'] for t in tags]
    
    # Screenshots
    screenshots = execute_query(
        "SELECT * FROM tv_observation_screenshots WHERE observation_id = ?",
        (observation_id,)
    )
    obs['screenshots'] = [dict(s) for s in screenshots]
    
    return obs

def search_observations(user_id: int, query: str = "", stock_name: str = None, limit: int = 50) -> List[Dict]:
    """Search observations by text or filter by stock name."""
    sql = "SELECT * FROM tv_observations WHERE user_id = ?"
    params = [user_id]
    
    if query:
        sql += " AND (observation_text LIKE ? OR stock_name LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
        
    if stock_name and stock_name != "All":
        sql += " AND stock_name = ?"
        params.append(stock_name)
        
    sql += " ORDER BY created_date DESC LIMIT ?"
    params.append(limit)
    
    results = execute_query(sql, tuple(params))
    
    observations = [dict(row) for row in results]
    for obs in observations:
        # Load tags
        tags = execute_query("SELECT tag FROM tv_observation_tags WHERE observation_id = ?", (obs['id'],))
        obs['tags'] = [t['tag'] for t in tags]
        
        # Load screenshots eagerly for the feed view
        screenshots = execute_query(
            "SELECT * FROM tv_observation_screenshots WHERE observation_id = ?",
            (obs['id'],)
        )
        obs['screenshots'] = [dict(s) for s in screenshots]
        
    return observations

def add_observation_tag(observation_id: int, tag: str) -> None:
    """Add a tag to an observation."""
    try:
        create_record('tv_observation_tags', {'observation_id': observation_id, 'tag': tag.lower()})
    except Exception:
        pass # Ignore duplicates

def add_observation_screenshot(observation_id: int, file_path: str, caption: str = "") -> None:
    """Add a screenshot record."""
    create_record('tv_observation_screenshots', {
        'observation_id': observation_id,
        'file_path': file_path,
        'caption': caption
    })

def delete_observation(user_id: int, observation_id: int) -> None:
    """Delete an observation."""
    execute_update("DELETE FROM tv_observations WHERE id = ? AND user_id = ?", (observation_id, user_id))
