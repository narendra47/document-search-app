import io
from typing import Optional
import PyPDF2
from app.utils.logger import setup_logger


class PDFProcessor:
    """Service for processing PDF files"""

    def __init__(self):
        self.logger = setup_logger(__name__)

    def extract_text(self, file_content: bytes) -> Optional[str]:
        """Extract text content from PDF bytes"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"

            return text_content.strip()

        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {str(e)}")
            return None