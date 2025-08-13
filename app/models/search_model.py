from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.models.document import Document
from pydantic import BaseModel, Field
from enum import Enum


class SearchModel(ABC):
    """Abstract base class for search engines"""

    @abstractmethod
    def index_document(self, document: Document) -> bool:
        """Index a document"""
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """Delete a document from index"""
        pass

    @abstractmethod
    def search(self, query: str, size: int = 10) -> List[Dict[str, Any]]:
        """Search for documents"""
        pass

    @abstractmethod
    def document_exists(self, document_id: str) -> bool:
        """Check if document exists in index"""
        pass

# Request Models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    size: Optional[int] = Field(10, ge=1, le=100, description="Number of results to return")

# Response Models
class SearchResult(BaseModel):
    file_path: str
    name: str
    web_view_link: str
    score: float


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResult]

class IndexStatus(str, Enum):
    idle = "idle"
    running = "running"
    completed = "completed"
    failed = "failed"