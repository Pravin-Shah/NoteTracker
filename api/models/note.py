"""
Pydantic models for Notes.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class AttachmentResponse(BaseModel):
    """Attachment data."""
    id: int
    file_path: str
    file_type: Optional[str] = None
    upload_date: Optional[datetime] = None


class NoteCreate(BaseModel):
    """Request model for creating a note."""
    title: str = Field(..., min_length=3, max_length=100)
    content: str = Field(default="")
    category: Optional[str] = None
    importance: int = Field(default=3, ge=1, le=5)
    color: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    """Request model for updating a note."""
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    content: Optional[str] = None
    category: Optional[str] = None
    importance: Optional[int] = Field(None, ge=1, le=5)
    color: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteResponse(BaseModel):
    """Response model for a single note."""
    id: int
    user_id: int
    title: str
    content: str
    category: Optional[str] = None
    importance: int = 3
    color: Optional[str] = None
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    archived: int = 0
    pinned: int = 0
    tags: List[str] = Field(default_factory=list)
    attachments: List[AttachmentResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """Response model for list of notes."""
    notes: List[NoteResponse]
    total: int


class NoteStatsResponse(BaseModel):
    """Response model for note statistics."""
    total: int
    pinned: int
    archived: int
    active: int
    by_category: Dict[str, int] = Field(default_factory=dict)


class TagListResponse(BaseModel):
    """Response model for list of tags."""
    tags: List[str]


class CategoryListResponse(BaseModel):
    """Response model for list of categories."""
    categories: List[str]
