"""
Manages the state of research data, including a queue of tasks, a list of processed tasks, and main summaries.

The state can be saved to and loaded from a JSON file.
"""

import json
import logging
from pathlib import Path

# Set up a dedicated logger
logger = logging.getLogger(__name__)

class ResearchState:
    """A class to manage the state of research data."""

    def __init__(self) -> None:
        """Initialize the ResearchState with default data."""
        self.state_file = Path("research_state.json")
        self.data = {
            "queue": [],
            "processed": [],
            "main_summaries": [],
        }

    def load(self) -> None:
        """Load the state from a JSON file."""
        if self.state_file.exists():
            try:
                with self.state_file.open() as f:
                    self.data = json.load(f)
                logger.info("State loaded successfully")
            except Exception:
                logger.exception("Error loading state")

    def save(self) -> None:
        """Save the state to a JSON file."""
        try:
            with self.state_file.open("w") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            logger.exception("Error saving state")
