from typing import Dict, Any, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse

from app.services.google_drive_service import GoogleDriveService
from app.services.elastic_search_service import ElasticsearchService
from app.utils.logger import setup_logger


class DocumentSearchAPI:
    """FastAPI application for document search"""

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.app = FastAPI(title="Document Search API", version="1.0.0")
        self.drive_service = GoogleDriveService()
        self.search_engine = ElasticsearchService()
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/")
        async def root():
            return {"message": "Document Search API is running"}

        @self.app.post("/index")
        async def index_documents():
            """Index all documents from Google Drive"""
            try:
                documents = self.drive_service.get_all_documents()
                indexed_count = 0

                for document in documents:
                    if self.search_engine.index_document(document):
                        indexed_count += 1

                self.search_engine.refresh_index()

                return {
                    "message": f"Indexed {indexed_count} out of {len(documents)} documents",
                    "total_documents": len(documents),
                    "indexed_documents": indexed_count
                }

            except Exception as e:
                self.logger.error(f"Error indexing documents: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to index documents")

        @self.app.get("/search")
        async def search_documents(
                q: str = Query(..., description="Search query"),
                size: int = Query(10, description="Number of results to return")
        ):
            """Search for documents"""
            try:
                if not q.strip():
                    raise HTTPException(status_code=400, detail="Search query cannot be empty")

                results = self.search_engine.search(q, size)

                # Format results for API response
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "file_path": result['file_path'],
                        "name": result['name'],
                        "web_view_link": result['web_view_link'],
                        "score": result['score']
                    })

                return {
                    "query": q,
                    "total_results": len(formatted_results),
                    "results": formatted_results
                }

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error searching for '{q}': {str(e)}")
                raise HTTPException(status_code=500, detail="Search failed")

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                # Test Elasticsearch connection
                es_healthy = self.search_engine.es.ping()

                return {
                    "status": "healthy" if es_healthy else "unhealthy",
                    "elasticsearch": "connected" if es_healthy else "disconnected"
                }

            except Exception as e:
                self.logger.error(f"Health check failed: {str(e)}")
                return JSONResponse(
                    status_code=503,
                    content={"status": "unhealthy", "error": str(e)}
                )

    def get_app(self):
        """Get FastAPI application instance"""
        return self.app