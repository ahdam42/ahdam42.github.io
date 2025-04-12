"""Module for downloading documents."""
import logging
from pathlib import Path

from DAO.document_links import DocumentLinks
from DAO.research_state import ResearchState
from prompt.llm_service import LLMService
from prompt.prompt_service import PromptService
from utils.pdf_utils import PDFUtils
from utils.utils import normalize_arxiv_id, setup_signal_handler

# Set up a dedicated logger
logger = logging.getLogger(__name__)

def check_relevance(candidate_summary: str, arxiv_id: str) -> bool:
    """
    Check the relevance of a candidate summary.

    Args:
        candidate_summary (str): The summary to check.
        arxiv_id (str): The arXiv ID of the document.

    Returns:
        bool: True if relevant, False otherwise.

    """
    try:
        prompt = PromptService.create_relevance_prompt(candidate_summary)
        response = LLMService.get_llm_response(prompt, 0.8)
        return response.strip().lower() in ["да", "yes"]
    except Exception:
        logger.exception("Relevance check failed for %s", arxiv_id)
        return False

def process_initial_pdfs(state: ResearchState, links: DocumentLinks, initial_files: list[Path]) -> None:
    """
    Process the initial set of PDFs.

    Args:
        state (ResearchState): The research state.
        links (DocumentLinks): The document links.
        initial_files (List[Path]): The list of initial PDF files.

    """
    for pdf_path in initial_files:
        try:
            text = PDFUtils.read_and_clean_pdf(pdf_path)
            if not text:
                continue

            summary = LLMService.get_llm_response(PromptService.create_summary_prompt(text), 0.8)
            state.data["main_summaries"].append(summary)

            arxiv_id_from_filename = pdf_path.stem
            normalized_id = normalize_arxiv_id(arxiv_id_from_filename)

            doc_links = PDFUtils.extract_links_from_pdf(pdf_path)
            links.add_document(normalized_id, doc_links, summary)

            for arxiv_id in doc_links.get("arxiv", []):
                norm_id = normalize_arxiv_id(arxiv_id)
                if norm_id not in state.data["queue"] + state.data["processed"]:
                    state.data["queue"].append(norm_id)
        except Exception:
            logger.exception("Initial processing failed")

def process_queue(state: ResearchState, links: DocumentLinks) -> None:
    """
    Process the queue of arXiv IDs.

    Args:
        state (ResearchState): The research state.
        links (DocumentLinks): The document links.

    """
    while state.data["queue"]:
        current_id = state.data["queue"].pop(0)

        try:
            if current_id in state.data["processed"]:
                continue

            logger.info("Processing: %s", current_id)

            if PDFUtils.download_arxiv_pdf(current_id):
                pdf_path = Path("research") / f"{current_id}.pdf"
                doc_links = PDFUtils.extract_links_from_pdf(pdf_path)
                text = PDFUtils.read_and_clean_pdf(pdf_path)
                summary = LLMService.get_llm_response(PromptService.create_summary_prompt(text), 0.8)
                new_ids = [normalize_arxiv_id(arxiv_id) for arxiv_id in doc_links.get("arxiv", [])]

                if check_relevance(summary, current_id):
                    state.data["queue"].extend(new_ids)
                    links.add_document(current_id, doc_links, summary)
                    logger.info("Added relevant paper: %s", current_id)
                else:
                    logger.info("Skipped irrelevant paper: %s", current_id)

                state.data["processed"].append(current_id)

            state.save()
            links.save()

        except Exception:
            logger.exception("Failed processing %s", current_id)
            state.data["queue"].insert(0, current_id)
            state.save()
            break

def process_pdfs(state: ResearchState, links: DocumentLinks) -> None:
    """
    Process PDFs and update the research state and document links.

    Args:
        state (ResearchState): The research state.
        links (DocumentLinks): The document links.

    """
    state.load()
    links.load()

    initial_files = list(Path("to research").glob("*.pdf"))
    process_initial_pdfs(state, links, initial_files)

    state.save()
    links.save()

    process_queue(state, links)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("research.log"),
            logging.StreamHandler(),
        ],
    )

    Path("to research").mkdir(exist_ok=True)
    Path("research").mkdir(exist_ok=True)

    state = ResearchState()
    links = DocumentLinks()
    setup_signal_handler(state, links)

    try:
        process_pdfs(state, links)
        logger.info("Processing completed successfully")
    except Exception:
        logger.exception("Fatal error")
    finally:
        state.save()
        links.save()
