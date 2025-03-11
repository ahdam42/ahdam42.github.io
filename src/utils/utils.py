import logging
import re
import signal
from itertools import islice

def normalize_arxiv_id(arxiv_id):
    return re.sub(r'v\d+$', '', arxiv_id, flags=re.IGNORECASE).lower().strip()

def setup_signal_handler(state, links):
    def handler(signum, frame):
        logging.info("Received interrupt signal. Saving state...")
        state.save()
        links.save()
        exit(0)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

def sanitize_text(text: str) -> str:
    """Clean text from problematic characters"""
    return re.sub(r'[\x00-\x1F\\]', ' ', text).strip()

def batched(iterable, n):
    """Batch data into tuples of size n"""
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch