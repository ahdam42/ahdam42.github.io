import fitz
import json
import logging
import signal
import httpx
import re
from pathlib import Path
from itertools import islice
from typing import List, Tuple, Callable

LLM_URL = "http://localhost:1234/v1/chat/completions"
CHUNK_SIZE = 5  # Pages per chunk
GROUP_SIZE = 10  # Items per aggregation group
MAX_RETRIES = 3  # Max retries for LLM requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('processing.log'), logging.StreamHandler()]
)

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

def sanitize_text(text: str) -> str:
    """Clean text from problematic characters"""
    return re.sub(r'[\x00-\x1F\\]', ' ', text).strip()

def read_pdf_chunks(pdf_path: Path, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Read PDF in chunks with error handling"""
    try:
        doc = fitz.open(pdf_path)
        chunks = []
        for i in range(0, len(doc), chunk_size):
            chunk_text = ""
            for page_num in range(i, min(i + chunk_size, len(doc))):
                page = doc[page_num]
                text = page.get_text().replace('-\n', '').replace('\n', ' ')
                chunk_text += f"PAGE {page_num + 1}:\n{sanitize_text(text)}\n"
            chunks.append(chunk_text)
        return chunks
    except Exception as e:
        logging.error(f"Error reading {pdf_path}: {e}")
        return []

def get_llm_response(prompt: str) -> str:
    """Get response from LLM with enhanced error handling"""
    clean_prompt = sanitize_text(prompt)
    for attempt in range(MAX_RETRIES):
        try:
            response = httpx.post(
                LLM_URL,
                json={
                    "model": "mistral-nemo-instruct-2407",
                    "messages": [{"role": "user", "content": clean_prompt}],
                    "temperature": 0.8,
                    "max_tokens": -1
                },
                timeout=None
            )
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"].strip()
            return sanitize_text(result)
        except KeyError:
            logging.error("Invalid response structure from LLM")
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e.response.status_code}")
        except Exception as e:
            logging.error(f"LLM request failed: {str(e)}")

        if attempt == MAX_RETRIES - 1:
            return ""
    return ""

def setup_signal_handler(state: ProcessingState):
    """Signal handling for state preservation"""

    def handler(signum, frame):
        logging.info("Saving state before exit...")
        state.save()
        exit(0)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

def batched(iterable, n):
    """Batch data into tuples of size n"""
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch

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
            response = get_llm_response(group_prompt)
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

def create_partial_prompt(question: str, chunk_text: str, part: int, total: int) -> str:
    """General-purpose chunk analysis prompt"""
    return f"""Analyze this document section (Part {part} of {total}).
Focus on key elements relevant to: {question}

Document Excerpt:
{chunk_text}

Guidelines:
1. Identify main concepts and relationships
2. Note methodological approaches
3. Highlight unique findings
4. Mention limitations or gaps

Structured Analysis:"""

def create_chunk_aggregation_prompt(group: List[str], group_number: int) -> str:
    """Generic chunk group aggregation prompt"""
    return f"""Synthesize key points from {len(group)} document sections:

Sections Group {group_number}:
{"".join([f"--- Section {i + 1} ---{text}" for i, text in enumerate(group)])}

Synthesis Guidelines:
1. Remove redundant information
2. Preserve unique findings
3. Highlight patterns and contradictions
4. Maintain page references

Consolidated Analysis:"""

def create_article_aggregation_prompt(group: List[Tuple[str, str]], group_number: int) -> str:
    """Generic article group aggregation prompt"""
    return f"""Integrate findings from {len(group)} research documents:

Documents Group {group_number}:
{"".join([f"--- Document {doc_id} --- {content}" for doc_id, content in group])}

Integration Guidelines:
1. Compare methodologies
2. Identify common patterns
3. Note divergent results
4. Highlight innovations
5. Maintain document references

Integrated Analysis:"""

def process_article(pdf_path: Path, question: str, state: ProcessingState):
    """Process single article with validation"""
    article_id = pdf_path.stem
    if article_id in state.data["processed_articles"]:
        logging.info(f"Skipping processed article: {article_id}")
        return

    try:
        chunks = read_pdf_chunks(pdf_path)
        if not chunks:
            logging.warning(f"No readable content in {article_id}")
            return

        # Process chunks
        processed_chunks = []
        for chunk in chunks:
            prompt = create_partial_prompt(question, chunk, 1, 1)
            response = get_llm_response(prompt)
            if response:
                processed_chunks.append(response)

        # Aggregate chunks
        if processed_chunks:
            article_response = hierarchical_aggregation(
                processed_chunks,
                create_chunk_aggregation_prompt,
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

    # Process articles
    for pdf_path in pdf_files:
        if pdf_path.stem not in state.data["processed_articles"]:
            process_article(pdf_path, question, state)

    # Final aggregation
    valid_articles = [
        (id, text) for id, text in state.data["article_outputs"].items()
        if text.strip()
    ]

    if valid_articles:
        final_answer = hierarchical_aggregation(
            valid_articles,
            create_article_aggregation_prompt,
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
