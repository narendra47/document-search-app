from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch, exceptions
from app.config import Config
from app.models.document import Document
from app.models.search_model import SearchModel
from app.utils.logger import setup_logger


class ElasticsearchService(SearchModel):
    """Elasticsearch implementation of SearchModel"""

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.es = Elasticsearch(
            [{'host': Config.ELASTICSEARCH_HOST, 'port': Config.ELASTICSEARCH_PORT, 'scheme': 'http'}],
            verify_certs=False
        )
        self.index_name = Config.ELASTICSEARCH_INDEX
        self._create_index()

    def _create_index(self):
        """Create Elasticsearch index if it doesn't exist"""
        try:
            if not self.es.indices.exists(index=self.index_name):
                index_body = {
                    "mappings": {
                        "properties": {
                            "id": {"type": "keyword"},
                            "name": {"type": "text", "analyzer": "standard"},
                            "content": {"type": "text", "analyzer": "standard"},
                            "file_path": {"type": "keyword"},
                            "web_view_link": {"type": "keyword"},
                            "created_time": {"type": "date"},
                            "modified_time": {"type": "date"},
                            "size": {"type": "long"},
                            "mime_type": {"type": "keyword"}
                        }
                    }
                }

                self.es.indices.create(index=self.index_name, body=index_body)
                self.logger.info(f"Created Elasticsearch index: {self.index_name}")

        except exceptions.RequestError as e:
            self.logger.error(f"Error creating index: {str(e)}")

    def index_document(self, document: Document) -> bool:
        """Index a document in Elasticsearch"""
        try:
            response = self.es.index(
                index=self.index_name,
                id=document.id,
                body=document.to_dict()
            )

            success = response['result'] in ['created', 'updated']
            if success:
                self.logger.debug(f"Indexed document: {document.name}")

            return success

        except Exception as e:
            self.logger.error(f"Error indexing document {document.name}: {str(e)}")
            return False

    def delete_document(self, document_id: str) -> bool:
        """Delete a document from Elasticsearch"""
        try:
            response = self.es.delete(
                index=self.index_name,
                id=document_id
            )

            success = response['result'] == 'deleted'
            if success:
                self.logger.debug(f"Deleted document: {document_id}")

            return success

        except exceptions.NotFoundError:
            self.logger.warning(f"Document not found for deletion: {document_id}")
            return False
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False

    def document_exists(self, document_id: str) -> bool:
        """Check if document exists in Elasticsearch"""
        try:
            return self.es.exists(index=self.index_name, id=document_id)
        except Exception as e:
            self.logger.error(f"Error checking document existence {document_id}: {str(e)}")
            return False

    def search(self, query: str, size: int = 10) -> List[Dict[str, Any]]:
        """Search for documents in Elasticsearch"""
        try:
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^2", "content", "file_path"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "highlight": {
                    "fields": {
                        "content": {},
                        "name": {}
                    }
                },
                "size": size
            }

            response = self.es.search(
                index=self.index_name,
                body=search_body
            )

            results = []
            for hit in response['hits']['hits']:
                result = {
                    'id': hit['_source']['id'],
                    'name': hit['_source']['name'],
                    'file_path': hit['_source']['file_path'],
                    'web_view_link': hit['_source']['web_view_link'],
                    'score': hit['_score']
                }

                # Add highlights if available
                if 'highlight' in hit:
                    result['highlights'] = hit['highlight']

                results.append(result)

            self.logger.info(f"Search query '{query}' returned {len(results)} results")
            return results

        except Exception as e:
            self.logger.error(f"Error searching for '{query}': {str(e)}")
            return []

    def refresh_index(self):
        """Refresh the Elasticsearch index"""
        try:
            self.es.indices.refresh(index=self.index_name)
            self.logger.info("Refreshed Elasticsearch index")
        except Exception as e:
            self.logger.error(f"Error refreshing index: {str(e)}")