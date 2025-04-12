"""Utilities for normalizing arXiv IDs, setting up signal handlers, sanitizing text, and batching data."""

import logging
import re
import signal
import sys
from collections.abc import Iterable
from itertools import islice

# Create a logger for this module
logger = logging.getLogger(__name__)


def normalize_arxiv_id(arxiv_id: str) -> str:
    """
    Normalize the arXiv ID by removing the version number and converting to lowercase.

    Args:
        arxiv_id (str): The arXiv ID to normalize.

    Returns:
        str: The normalized arXiv ID.

    """
    return re.sub(r"v\d+$", "", arxiv_id, flags=re.IGNORECASE).lower().strip()

def setup_signal_handler(state: object, links: object) -> None:
    """
    Set up signal handlers to save state and links on interrupt signals.

    Args:
        state (object): The state object to save.
        links (object): The links object to save.

    """
    def handler() -> None:
        logger.info("Received interrupt signal. Saving state...")
        state.save()
        links.save()
        sys.exit(0)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

def sanitize_text(text: str) -> str:
    """
    Clean text from problematic characters.

    Args:
        text (str): The text to sanitize.

    Returns:
        str: The sanitized text.

    """
    return re.sub(r"[\x00-\x1F\\]", " ", text).strip()

def batched(iterable: Iterable, n: int) -> Iterable[tuple]:
    """
    Batch data into tuples of size n.

    Args:
        iterable (Iterable): The iterable to batch.
        n (int): The size of each batch.

    Returns:
        Iterable[Tuple]: An iterable of batched tuples.

    """
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch
