"""Main file."""
import logging
from collections.abc import Callable
from pathlib import Path

from DAO.processing_state import ProcessingState
from prompt.llm_service import LLMService
from prompt.prompt_service import PromptService
from utils.pdf_utils import PDFUtils
from utils.utils import batched, sanitize_text, setup_signal_handler

GROUP_SIZE = 10  # Items per aggregation group

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("processing.log"), logging.StreamHandler()],
)

def hierarchical_aggregation(
        content: list[str],
        prompt_creator: Callable[[list[str], int], str],
        level_name: str,
) -> str:
    """Recursive aggregation with error handling."""
    aggregated = []
    try:
        for group_number, group in enumerate(batched(content, GROUP_SIZE), 1):
            group_prompt = prompt_creator(group, group_number)
            response = LLMService.get_llm_response(group_prompt)
            if response:
                aggregated.append(response)
                logger.info("Aggregated %s group %d", level_name, group_number)
            else:
                logger.warning("Empty response for group %d", group_number)
    except Exception:
        logger.exception("Error processing group" )

    if len(aggregated) > 1:
        return hierarchical_aggregation(aggregated, prompt_creator, f"{level_name}-groups")
    return aggregated[0] if aggregated else ""

def process_article(pdf_path: Path, question: str, state: ProcessingState) -> None:
    """Process single article with validation."""
    article_id = pdf_path.stem
    if article_id in state.data["processed_articles"]:
        logger.info("Skipping processed article: %s", article_id)
        return

    try:
        chunks = PDFUtils.read_pdf_chunks(pdf_path)
        if not chunks:
            logger.warning("No readable content in %s", article_id)
            return

        processed_chunks = []
        for chunk in chunks:
            prompt = PromptService.create_partial_prompt(question, chunk, 1, 1)
            response = LLMService.get_llm_response(prompt)
            if response:
                processed_chunks.append(response)

        if processed_chunks:
            article_response = hierarchical_aggregation(
                processed_chunks,
                PromptService.create_chunk_aggregation_prompt,
                "chunks",
            )
            state.data["article_outputs"][article_id] = article_response
            state.data["processed_articles"].append(article_id)
            state.save()
            logger.info("Processed article: %s", article_id)
        else:
            logger.warning("No valid responses for %s", article_id)

    except Exception:
        logger.exception("Failed processing %s", article_id)

def main(question: str) -> None:
    """Runner."""
    pdf_dir = Path("research")
    pdf_files = list(pdf_dir.glob("*.pdf"))

    state = ProcessingState()
    if not state.data["main_question"]:
        state.data["main_question"] = sanitize_text(question)
        state.save()

    setup_signal_handler(state)

    for pdf_path in pdf_files:
        if pdf_path.stem not in state.data["processed_articles"]:
            process_article(pdf_path, question, state)

    valid_articles = [
        (article_id, text) for article_id, text in state.data["article_outputs"].items()
        if text.strip()
    ]

    if valid_articles:
        final_answer = hierarchical_aggregation(
            valid_articles,
            PromptService.create_article_aggregation_prompt,
            "articles",
        )

        with Path("final_answer.md").open("w", encoding="utf-8") as f:
            f.write(f"# Research Synthesis\n\n**Question**: {question}\n\n## Final Analysis\n{final_answer}")
    else:
        logger.error("No valid articles processed")

if __name__ == "__main__":
    user_question = """
    Analyze the provided research articles to identify and categorize the mathematical methods used. For each article:
    List specific mathematical techniques, theorems, or frameworks employed
    Classify them by mathematical discipline (e.g., statistical analysis, linear algebra, differential equations)
    Provide context about their application in the research
    Highlight any novel mathematical contributions
    Mention equations or formulas that are central to the methodology

    Where possible, include:
    Page numbers where key mathematical elements appear
    Relationships between different mathematical tools used
    Comparisons with standard approaches in the field"""

    main(user_question)
