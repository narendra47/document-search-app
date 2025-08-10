import os
from typing import List


class Config:
    # Google Drive API
    GOOGLE_DRIVE_FOLDER: str = "document-search"
    SCOPES: List[str] = ['https://www.googleapis.com/auth/drive.readonly']
    CREDENTIALS_FILE: str = 'credentials.json'
    TOKEN_FILE: str = 'token.json'

    # Elasticsearch
    ELASTICSEARCH_HOST: str = os.getenv('ELASTICSEARCH_HOST', 'localhost')
    ELASTICSEARCH_PORT: int = int(os.getenv('ELASTICSEARCH_PORT', '9200'))
    ELASTICSEARCH_INDEX: str = 'documents'

    # Application
    API_HOST: str = '127.0.0.1'
    API_PORT: int = 8000

    # Supported file types
    SUPPORTED_EXTENSIONS: List[str] = ['.pdf']

    # Logging
    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'