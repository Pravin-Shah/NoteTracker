"""
FastAPI Router for Second Brain.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from api.database import execute_query, get_record_by_id
from api.dependencies import get_current_user
from apps.general.utils.brain_ops import list_wiki_pages, get_wiki_page, get_links

router = APIRouter(prefix="/api/brain", tags=["brain"])

@router.get("/wiki", response_model=List[dict])
async def get_all_wiki_pages(
    category: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """List all wiki pages."""
    return list_wiki_pages(current_user['id'], category)

@router.get("/wiki/{title}", response_model=dict)
async def get_single_wiki_page(
    title: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific wiki page by title."""
    page = get_wiki_page(current_user['id'], title)
    if not page:
        raise HTTPException(status_code=404, detail="Wiki page not found")
    
    # Also fetch links
    links = get_links(page['id'])
    page['links'] = links
    return page

@router.get("/raw", response_model=List[dict])
async def get_raw_dumps(
    processed: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get raw dumps."""
    user_id = current_user['id']
    sql = "SELECT * FROM brain_raw WHERE user_id = ?"
    params = [user_id]
    
    if processed is not None:
        sql += " AND processed = ?"
        params.append(1 if processed else 0)
    
    sql += " ORDER BY created_date DESC"
    return execute_query(sql, tuple(params))

@router.get("/stats")
async def get_brain_stats(current_user: dict = Depends(get_current_user)):
    """Get brain statistics."""
    user_id = current_user['id']
    
    wiki_count = execute_query("SELECT COUNT(*) as count FROM brain_wiki WHERE user_id = ?", (user_id,))[0]['count']
    raw_count = execute_query("SELECT COUNT(*) as count FROM brain_raw WHERE user_id = ?", (user_id,))[0]['count']
    link_count = execute_query("SELECT COUNT(*) as count FROM brain_links WHERE wiki_id_1 IN (SELECT id FROM brain_wiki WHERE user_id = ?)", (user_id,))[0]['count']
    
    return {
        "wiki_pages": wiki_count,
        "raw_dumps": raw_count,
        "links": link_count
    }
