"""
Provides the ProcessingState class for maintaining hierarchical processing state.

The ProcessingState class manages the state of processed articles and groups,
including their outputs and the main question. It provides methods to load and save
the state to a JSON file.
"""

import json
import logging
from pathlib import Path

# Create a custom logger
logger = logging.getLogger(__name__)

class ProcessingState:
    """Class for maintaining hierarchical processing state."""

    def __init__(self) -> None:
        """Initialize the ProcessingState with default values."""
        self.state_file = Path("processing_state.json")
        self.data = {
            "processed_articles": [],
            "processed_groups": [],
            "article_outputs": {},
            "group_outputs": {},
            "main_question": "",
        }
        self.load()

    def load(self) -> None:
        """Load the processing state from a file."""
        if self.state_file.exists():
            try:
                with self.state_file.open() as f:
                    self.data = json.load(f)
            except Exception:
                logger.exception("Error loading state")

    def save(self) -> None:
        """Save the processing state to a file."""
        try:
            with self.state_file.open("w") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            logger.exception("Error saving state")
