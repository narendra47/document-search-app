from typing import Dict, Any, List
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.search_model import SearchResponse, SearchRequest, SearchResult
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
        async def index_documents(background_tasks: BackgroundTasks):
            background_tasks.add_task(self._index_documents)
            return {"message": "Indexing started asynchronously..."}

        @self.app.post("/search", response_model=SearchResponse)
        async def search_documents(search_request: SearchRequest):
            q = search_request.query.strip()
            size = search_request.size

            if not q:
                raise HTTPException(status_code=400, detail="Search query cannot be empty")

            try:
                results = self.search_engine.search(q, size)
                formatted = [
                    SearchResult(
                        file_path=r["file_path"],
                        name=r["name"],
                        web_view_link=r["web_view_link"],
                        score=r["score"]
                    )
                    for r in results
                ]
                return SearchResponse(query=q, total_results=len(formatted), results=formatted)

            except Exception as e:
                self.logger.error(f"Search error for query='{q}': {str(e)}")
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

    def _index_documents(self):
        try:
            documents = self.drive_service.get_all_documents()
            indexed_count = 0
            for doc in documents:
                if self.search_engine.index_document(doc):
                    indexed_count += 1
            self.search_engine.refresh_index()
            self.logger.info(f"Indexed {indexed_count} out of {len(documents)} documents")
        except Exception as e:
            self.logger.error(f"Indexing failed: {str(e)}")

    def get_app(self):
        return self.app