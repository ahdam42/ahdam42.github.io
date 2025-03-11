import json
import logging
from pathlib import Path

class ResearchState:
    def __init__(self):
        self.state_file = Path("research_state.json")
        self.data = {
            'queue': [],
            'processed': [],
            'main_summaries': []
        }

    def load(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.data = json.load(f)
                logging.info("State loaded successfully")
            except Exception as e:
                logging.error(f"Error loading state: {str(e)}")

    def save(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving state: {str(e)}")