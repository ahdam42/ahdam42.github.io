"""
PDFUtils Module.

Module provides utility functions for handling PDF operations, including reading, cleaning,
extracting links, and downloading arXiv PDFs.

Classes:
    PDFUtils: A class containing static methods for PDF operations.

Functions:
    read_and_clean_pdf: Read and clean text from a PDF file.
    read_pdf_chunks: Read PDF in chunks with error handling.
    extract_links_from_pdf: Extract links from a PDF file.
    download_arxiv_pdf: Download an arXiv PDF.
"""

import logging
import re
import sys
from pathlib import Path

import fitz
import requests

from utils.utils import normalize_arxiv_id, sanitize_text

MAX_PAGES_FOR_SUMMARY = 5
CHUNK_SIZE = 5

# Set up a logger for the module
logger = logging.getLogger(__name__)

class PDFUtils:
    """Utility class for handling PDF operations."""

    @staticmethod
    def read_and_clean_pdf(pdf_path: str, num_pages: int = MAX_PAGES_FOR_SUMMARY) -> str:
        """
        Read and clean text from a PDF file.

        Args:
            pdf_path (str): The path to the PDF file.
            num_pages (int): The number of pages to read.

        Returns:
            str: The cleaned text from the PDF.

        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(min(num_pages, len(doc))):
                page = doc[page_num]
                text += page.get_text().replace("-\n", "").replace("\n", " ")
            return text
        except Exception:
            logger.exception("Error reading PDF %s", pdf_path)
            return ""

    @staticmethod
    def read_pdf_chunks(pdf_path: Path, chunk_size: int = CHUNK_SIZE) -> list[str]:
        """
        Read PDF in chunks with error handling.

        Args:
            pdf_path (Path): The path to the PDF file.
            chunk_size (int): The number of pages per chunk.

        Returns:
            list[str]: A list of text chunks from the PDF.

        """
        try:
            doc = fitz.open(pdf_path)
            chunks = []
            for i in range(0, len(doc), chunk_size):
                chunk_text = ""
                for page_num in range(i, min(i + chunk_size, len(doc))):
                    page = doc[page_num]
                    text = page.get_text().replace("-\n", "").replace("\n", " ")
                    chunk_text += f"PAGE {page_num + 1}:\n{sanitize_text(text)}\n"
                chunks.append(chunk_text)
            return chunks
        except Exception:
            logger.exception("Error reading %s", pdf_path)
            return []

    @staticmethod
    def extract_links_from_pdf(pdf_path: str) -> dict[str, list[str]]:
        """
        Extract links from a PDF file.

        Args:
            pdf_path (str): The path to the PDF file.

        Returns:
            dict[str, list[str]]: A dictionary of extracted links.

        """
        try:
            doc = fitz.open(pdf_path)
            text = "".join([page.get_text().replace("\n", " ") for page in doc])

            patterns = {
                "arxiv": re.compile(r"arxiv:\s*(\d{4}\.\d{4,}(?:v\d+)?)\b", re.IGNORECASE),
                "doi": re.compile(r"\b(10\.\d{4,}/[\S]+)\b", re.IGNORECASE),
                "url": re.compile(r"https?://\S+"),
                "pubmed": re.compile(r"pmid:\s?(\d+)"),
                "isbn": re.compile(r"\bISBN(?:-1[0-9]{3}(?:-[0-9]{3}){2}-[0-9X])?\b", re.IGNORECASE),
            }

            results = {}
            for key, pattern in patterns.items():
                matches = pattern.findall(text)
                clean_matches = [m[0].lower().strip() if isinstance(m, tuple) else m.lower().strip() for m in matches]
                if clean_matches:
                    results[key] = list(set(clean_matches))

            if "arxiv" in results:
                results["arxiv"] = [normalize_arxiv_id(arxiv_id) for arxiv_id in results["arxiv"]]

            return results
        except Exception:
            logger.exception("Error extracting links from %s", pdf_path)
            return {}

    @staticmethod
    def download_arxiv_pdf(arxiv_id: str, save_dir: str = "research") -> bool:
        """
        Download an arXiv PDF.

        Args:
            arxiv_id (str): The arXiv ID.
            save_dir (str): The directory to save the PDF.

        Returns:
            bool: True if the download was successful, False otherwise.

        """
        normalized_id = normalize_arxiv_id(arxiv_id)
        Path(save_dir).mkdir(exist_ok=True)
        filename = Path(save_dir) / f"{normalized_id}.pdf"

        if filename.exists():
            logger.info("File %s already exists. Skipping download.", filename)
            return True

        url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()

            if "application/pdf" not in response.headers.get("Content-Type", ""):
                logger.error("Invalid content type for %s", arxiv_id)
                sys.exit(1)

            with filename.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger.info("Successfully downloaded %s", normalized_id)
            return True
        except Exception:
            logger.exception("Failed to download %s", arxiv_id)
            return False
