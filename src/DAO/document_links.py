"""Handle storage and retrieval of document links and summaries."""

import json
import logging
from pathlib import Path
from typing import Any

from utils.utils import normalize_arxiv_id

logger = logging.getLogger(__name__)


class DocumentLinks:
    """Manage storage and retrieval of document links and summaries in a JSON file."""

    def __init__(self) -> None:
        """Initialize instance with path to links file and load existing data."""
        self.links_file = Path("document_links.json")
        self.links_data: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load document links from JSON file into memory."""
        if self.links_file.exists():
            try:
                with self.links_file.open() as f:
                    self.links_data = json.load(f)
            except Exception:
                logger.exception("Error loading links")

    def save(self) -> None:
        """Save current document links to JSON file."""
        try:
            with self.links_file.open("w") as f:
                json.dump(self.links_data, f, indent=2)
        except Exception:
            logger.exception("Error saving links")

    def add_document(self, arxiv_id: str, links: dict[str, Any], summary: str) -> None:
        """
        Add or update document's links and summary in storage.

        Args:
            arxiv_id: The arXiv identifier of the document
            links: Dictionary of links associated with the document
            summary: Summary text of the document

        """
        normalized_id = normalize_arxiv_id(arxiv_id)
        self.links_data[normalized_id] = {
            "links": self._normalize_links(links),
            "summary": summary,
        }
        self.save()

    def _normalize_links(self, links: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize link formats for consistent storage.

        Args:
            links: Dictionary of links to normalize

        Returns:
            Dictionary with normalized link values

        """
        normalized: dict[str, Any] = {}
        for key, values in links.items():
            if key == "arxiv":
                normalized[key] = [normalize_arxiv_id(v) for v in values]
            else:
                normalized[key] = [v.lower().strip() for v in values]
        return normalized
