import json
from pathlib import Path
import logging

class ProcessingState:
    """Class for maintaining hierarchical processing state"""

    def __init__(self):
        self.state_file = Path("processing_state.json")
        self.data = {
            "processed_articles": [],
            "processed_groups": [],
            "article_outputs": {},
            "group_outputs": {},
            "main_question": ""
        }
        self.load()

    def load(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.data = json.load(f)
            except Exception as e:
                logging.error(f"Error loading state: {e}")

    def save(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving state: {e}")