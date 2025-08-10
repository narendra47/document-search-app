from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Document:
    """Document model representing a file from Google Drive"""
    id: str
    name: str
    content: str
    file_path: str
    web_view_link: str
    created_time: datetime
    modified_time: datetime
    size: Optional[int] = None
    mime_type: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert document to dictionary for Elasticsearch indexing"""
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'file_path': self.file_path,
            'web_view_link': self.web_view_link,
            'created_time': self.created_time.isoformat(),
            'modified_time': self.modified_time.isoformat(),
            'size': self.size,
            'mime_type': self.mime_type
        }