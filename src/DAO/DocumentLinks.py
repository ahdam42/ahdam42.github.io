import json
from pathlib import Path
import logging

from src.utils.utils import normalize_arxiv_id

class DocumentLinks:
    def __init__(self):
        self.links_file = Path("document_links.json")
        self.links_data = {}

    def load(self):
        if self.links_file.exists():
            try:
                with open(self.links_file, 'r') as f:
                    self.links_data = json.load(f)
            except Exception as e:
                logging.error(f"Error loading links: {str(e)}")

    def save(self):
        try:
            with open(self.links_file, 'w') as f:
                json.dump(self.links_data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving links: {str(e)}")

    def add_document(self, arxiv_id, links, summary):
        normalized_id = normalize_arxiv_id(arxiv_id)
        self.links_data[normalized_id] = {
            'links': self._normalize_links(links),
            'summary': summary
        }
        self.save()

    def _normalize_links(self, links):
        normalized = {}
        for key, values in links.items():
            if key == 'arxiv':
                normalized[key] = [normalize_arxiv_id(v) for v in values]
            else:
                normalized[key] = [v.lower().strip() for v in values]
        return normalized