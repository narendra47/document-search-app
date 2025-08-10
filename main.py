import uvicorn
from app.config import Config
from app.apis.search import DocumentSearchAPI
from app.utils.logger import setup_logger


def main():
    """Main application entry point"""
    logger = setup_logger(__name__)

    try:
        # Create API instance
        api = DocumentSearchAPI()
        app = api.get_app()

        logger.info("Starting Document Search API server...")

        # Run the server
        uvicorn.run(
            app,
            host=Config.API_HOST,
            port=Config.API_PORT,
            log_level=Config.LOG_LEVEL.lower()
        )

    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise


if __name__ == "__main__":
    main()