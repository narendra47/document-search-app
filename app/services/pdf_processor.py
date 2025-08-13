import io
from typing import Optional, List, Dict
from app.utils.logger import setup_logger
import fitz


class PDFProcessor:
    """Service for processing PDF files"""

    def __init__(self):
        self.logger = setup_logger(__name__)

    def extract_text(self, file_content: bytes) -> Optional[str]:
        """Extract text content from PDF bytes"""
        try:
            pdf_stream = io.BytesIO(file_content)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")

            text_content = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                if page_text.strip():
                    text_content += page_text + "\n"

            doc.close()

            final_text = text_content.strip()
            if final_text:
                self.logger.debug(f"Successfully extracted {len(final_text)} characters from PDF")
                return final_text
            else:
                self.logger.warning("No text content found in PDF")
                return None

        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {str(e)}")
            return None

    def extract_text_with_pages(self, file_content: bytes) -> List[Dict]:
        """
        Extract text from PDF with page number information
        Returns list of dictionaries with page details
        """
        pages_content = []

        try:
            pdf_stream = io.BytesIO(file_content)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")

            total_pages = len(doc)
            self.logger.info(f"Processing PDF with {total_pages} pages")

            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                text = page.get_text().strip()

                # Only include pages with meaningful content
                if text and len(text) > 10:  # Skip pages with minimal content
                    page_info = {
                        'page_number': page_num + 1,  # 1-indexed for user display
                        'text': self._clean_text(text),
                        'raw_text': text,  # Keep original for debugging
                        'word_count': len(text.split()),
                        'char_count': len(text),
                        'page_dimensions': {
                            'width': round(page.rect.width, 2),
                            'height': round(page.rect.height, 2)
                        }
                    }
                    pages_content.append(page_info)

                    self.logger.debug(f"Page {page_num + 1}: {len(text)} chars, {len(text.split())} words")
                else:
                    self.logger.debug(f"Skipping page {page_num + 1} - insufficient content")

            doc.close()
            self.logger.info(f"Successfully processed {len(pages_content)} pages with content")
            return pages_content

        except Exception as e:
            self.logger.error(f"Error extracting text with pages from PDF: {str(e)}")
            return []

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        import re

        # Remove excessive whitespace while preserving paragraph breaks
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
        text = re.sub(r'\n ', '\n', text)  # Remove space at beginning of lines

        # Fix common spacing issues around punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)

        return text.strip()

    def search_in_pages(self, pages_content: List[Dict], search_term: str) -> List[Dict]:
        """
        Search for term in pages and return matching pages with highlighted context
        """
        if not search_term or not pages_content:
            return []

        matching_pages = []
        search_term_lower = search_term.lower()

        for page_info in pages_content:
            text_lower = page_info['text'].lower()

            if search_term_lower in text_lower:
                # Find all occurrences
                occurrences = []
                start_pos = 0

                while True:
                    pos = text_lower.find(search_term_lower, start_pos)
                    if pos == -1:
                        break

                    # Extract context around the match
                    context_start = max(0, pos - 150)
                    context_end = min(len(page_info['text']), pos + len(search_term) + 150)
                    context = page_info['text'][context_start:context_end]

                    # Clean up context
                    context = ' '.join(context.split())

                    # Highlight the search term
                    highlighted_context = self._highlight_term(context, search_term)

                    occurrences.append({
                        'position': pos,
                        'context': highlighted_context,
                        'snippet_length': len(context)
                    })

                    start_pos = pos + 1

                matching_page = {
                    'page_number': page_info['page_number'],
                    'occurrences_count': len(occurrences),
                    'contexts': occurrences[:3],  # Limit to first 3 occurrences per page
                    'word_count': page_info['word_count'],
                    'char_count': page_info['char_count'],
                    'page_dimensions': page_info.get('page_dimensions', {})
                }

                matching_pages.append(matching_page)

        # Sort by page number
        matching_pages.sort(key=lambda x: x['page_number'])

        self.logger.info(f"Found '{search_term}' in {len(matching_pages)} pages")
        return matching_pages

    def _highlight_term(self, text: str, term: str) -> str:
        """Highlight search term in text (case-insensitive)"""
        import re

        # Create pattern that matches the term case-insensitively
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        # Replace with highlighted version, preserving original case
        return pattern.sub(lambda m: f"**{m.group()}**", text)

    def get_page_text(self, file_content: bytes, page_number: int) -> Optional[str]:
        """
        Get text from a specific page number (1-indexed)
        Useful for retrieving specific page content
        """
        try:
            pdf_stream = io.BytesIO(file_content)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")

            if page_number < 1 or page_number > len(doc):
                self.logger.warning(f"Page number {page_number} out of range (1-{len(doc)})")
                doc.close()
                return None

            page = doc.load_page(page_number - 1)  # Convert to 0-indexed
            text = page.get_text().strip()
            doc.close()

            return self._clean_text(text) if text else None

        except Exception as e:
            self.logger.error(f"Error extracting text from page {page_number}: {str(e)}")
            return None

    def get_pdf_info(self, file_content: bytes) -> Dict:
        """
        Get comprehensive PDF information including metadata and page count
        """
        try:
            pdf_stream = io.BytesIO(file_content)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")

            # Extract metadata
            metadata = doc.metadata or {}

            # Calculate total text statistics
            total_text_length = 0
            total_words = 0
            pages_with_content = 0

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():
                    total_text_length += len(text)
                    total_words += len(text.split())
                    pages_with_content += 1

            pdf_info = {
                'total_pages': len(doc),
                'pages_with_content': pages_with_content,
                'total_text_length': total_text_length,
                'total_words': total_words,
                'metadata': {
                    'title': metadata.get('title', '').strip(),
                    'author': metadata.get('author', '').strip(),
                    'subject': metadata.get('subject', '').strip(),
                    'creator': metadata.get('creator', '').strip(),
                    'producer': metadata.get('producer', '').strip(),
                    'creation_date': metadata.get('creationDate', ''),
                    'modification_date': metadata.get('modDate', '')
                },
                'is_encrypted': doc.needs_pass,
                'is_pdf': doc.is_pdf
            }

            doc.close()

            self.logger.info(f"PDF info: {pdf_info['total_pages']} pages, "
                             f"{pdf_info['pages_with_content']} with content, "
                             f"{pdf_info['total_words']} words")

            return pdf_info

        except Exception as e:
            self.logger.error(f"Error getting PDF info: {str(e)}")
            return {
                'total_pages': 0,
                'pages_with_content': 0,
                'total_text_length': 0,
                'total_words': 0,
                'metadata': {},
                'is_encrypted': False,
                'is_pdf': False,
                'error': str(e)
            }

    def validate_pdf(self, file_content: bytes) -> bool:
        """
        Validate if the file content is a valid PDF
        """
        try:
            pdf_stream = io.BytesIO(file_content)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")

            # Basic validation
            is_valid = doc.is_pdf and len(doc) > 0

            doc.close()
            return is_valid

        except Exception as e:
            self.logger.warning(f"PDF validation failed: {str(e)}")
            return False

    def extract_first_page_preview(self, file_content: bytes, max_chars: int = 500) -> Optional[str]:
        """
        Extract a preview from the first page for quick document identification
        """
        try:
            pdf_stream = io.BytesIO(file_content)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")

            if len(doc) == 0:
                doc.close()
                return None

            # Get first page
            first_page = doc.load_page(0)
            text = first_page.get_text().strip()
            doc.close()

            if not text:
                return None

            # Clean and truncate
            cleaned_text = self._clean_text(text)
            if len(cleaned_text) > max_chars:
                # Find a good breaking point near the limit
                truncated = cleaned_text[:max_chars]
                last_sentence = max(
                    truncated.rfind('.'),
                    truncated.rfind('!'),
                    truncated.rfind('?')
                )

                if last_sentence > max_chars * 0.7:  # If we find a sentence end in the last 30%
                    truncated = truncated[:last_sentence + 1]
                else:
                    truncated = truncated + "..."

                return truncated

            return cleaned_text

        except Exception as e:
            self.logger.error(f"Error extracting first page preview: {str(e)}")
            return None