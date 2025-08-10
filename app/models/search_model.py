from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.document import Document


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