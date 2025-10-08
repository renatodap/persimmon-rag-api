"""
Content processing service for URL fetching and PDF processing.
"""
from typing import Dict

import httpx
import structlog
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader

from app.core.errors import ValidationError

logger = structlog.get_logger()


class ContentProcessor:
    """Process various content types (URLs, PDFs)."""

    async def fetch_url(self, url: str) -> Dict[str, any]:
        """
        Fetch and extract content from URL.

        Args:
            url: URL to fetch

        Returns:
            dict: {url, title, content, word_count}

        Raises:
            ValidationError: If URL fetch fails
        """
        try:
            logger.info("url_fetch_request", url=url)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string.strip()
            elif soup.h1:
                title = soup.h1.get_text().strip()

            # Extract main content
            # Try article, main, or body
            main_content = soup.find("article") or soup.find("main") or soup.find("body")

            if main_content:
                # Get text content
                text = main_content.get_text(separator="\n", strip=True)
                # Clean up extra whitespace
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                content = "\n".join(lines)
            else:
                content = soup.get_text(separator="\n", strip=True)

            word_count = len(content.split())

            logger.info(
                "url_fetch_success",
                url=url,
                title=title,
                word_count=word_count,
            )

            return {
                "url": url,
                "title": title or "Untitled",
                "content": content,
                "word_count": word_count,
                "content_type": "url",
            }

        except httpx.HTTPStatusError as e:
            logger.error("url_fetch_http_error", url=url, status=e.response.status_code)
            raise ValidationError(f"Failed to fetch URL: HTTP {e.response.status_code}")
        except Exception as e:
            logger.error("url_fetch_error", url=url, error=str(e))
            raise ValidationError(f"Failed to fetch URL: {str(e)}")

    async def process_pdf(self, file_content: bytes, filename: str) -> Dict[str, any]:
        """
        Extract text from PDF file.

        Args:
            file_content: PDF file bytes
            filename: Original filename

        Returns:
            dict: {filename, content, word_count, page_count}

        Raises:
            ValidationError: If PDF processing fails
        """
        try:
            logger.info("pdf_process_request", filename=filename)

            # Read PDF
            from io import BytesIO

            pdf_file = BytesIO(file_content)
            reader = PdfReader(pdf_file)

            # Extract text from all pages
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            content = "\n\n".join(text_parts)
            word_count = len(content.split())
            page_count = len(reader.pages)

            logger.info(
                "pdf_process_success",
                filename=filename,
                pages=page_count,
                word_count=word_count,
            )

            return {
                "filename": filename,
                "content": content,
                "word_count": word_count,
                "page_count": page_count,
                "content_type": "pdf",
            }

        except Exception as e:
            logger.error("pdf_process_error", filename=filename, error=str(e))
            raise ValidationError(f"Failed to process PDF: {str(e)}")


# Global content processor instance
content_processor = ContentProcessor()
