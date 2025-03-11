import logging
from pathlib import Path

from typing import List, Callable

from src.DAO import ProcessingState
from src.prompt import LLMService, PromptService
from src.utils import PDFUtils
from src.utils.utils import batched, sanitize_text, setup_signal_handler

GROUP_SIZE = 10  # Items per aggregation group

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('processing.log'), logging.StreamHandler()]
)

def hierarchical_aggregation(
        content: List[str],
        prompt_creator: Callable[[List[str], int], str],
        level_name: str
) -> str:
    """Recursive aggregation with error handling"""
    aggregated = []
    for group_number, group in enumerate(batched(content, GROUP_SIZE), 1):
        try:
            group_prompt = prompt_creator(group, group_number)
            response = LLMService.get_llm_response(group_prompt)
            if response:
                aggregated.append(response)
                logging.info(f"Aggregated {level_name} group {group_number}")
            else:
                logging.warning(f"Empty response for group {group_number}")
        except Exception as e:
            logging.error(f"Error processing group {group_number}: {str(e)}")

    if len(aggregated) > 1:
        return hierarchical_aggregation(aggregated, prompt_creator, f"{level_name}-groups")
    return aggregated[0] if aggregated else ""

def process_article(pdf_path: Path, question: str, state: ProcessingState):
    """Process single article with validation"""
    article_id = pdf_path.stem
    if article_id in state.data["processed_articles"]:
        logging.info(f"Skipping processed article: {article_id}")
        return

    try:
        chunks = PDFUtils.read_pdf_chunks(pdf_path)
        if not chunks:
            logging.warning(f"No readable content in {article_id}")
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
                "chunks"
            )
            state.data["article_outputs"][article_id] = article_response
            state.data["processed_articles"].append(article_id)
            state.save()
            logging.info(f"Processed article: {article_id}")
        else:
            logging.warning(f"No valid responses for {article_id}")

    except Exception as e:
        logging.error(f"Failed processing {article_id}: {str(e)}")

def main(question: str):
    """Main workflow with enhanced validation"""
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
        (id, text) for id, text in state.data["article_outputs"].items()
        if text.strip()
    ]

    if valid_articles:
        final_answer = hierarchical_aggregation(
            valid_articles,
            PromptService.create_article_aggregation_prompt,
            "articles"
        )

        with open("final_answer.md", "w", encoding="utf-8") as f:
            f.write(f"# Research Synthesis\n\n**Question**: {question}\n\n## Final Analysis\n{final_answer}")
    else:
        logging.error("No valid articles processed")

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
