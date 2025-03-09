import re
import fitz
import json
import logging
import signal
import httpx
from pathlib import Path

LLM_URL = "http://localhost:1234/v1/chat/completions"
CHUNK_SIZE = 5  # Number of pages per chunk

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('processing.log'), logging.StreamHandler()]
)


class ProcessingState:
    """Class for maintaining processing state"""

    def __init__(self):
        self.state_file = Path("processing_state.json")
        self.data = {
            "processed": [],  # Processed articles
            "output": {},  # Processing results
            "main_question": ""  # Main research question
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
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving state: {e}")


def setup_signal_handler(state):
    """Signal handling for state preservation"""

    def handler(signum, frame):
        logging.info("Saving state before exit...")
        state.save()
        exit(0)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def read_pdf_chunks(pdf_path, chunk_size=CHUNK_SIZE):
    """Read PDF in chunks"""
    try:
        doc = fitz.open(pdf_path)
        chunks = []
        for i in range(0, len(doc), chunk_size):
            chunk_text = ""
            for page_num in range(i, min(i + chunk_size, len(doc))):
                page = doc[page_num]
                text = page.get_text().replace('-\n', '').replace('\n', ' ')
                chunk_text += f"PAGE {page_num + 1}:\n{text}\n"
            chunks.append(chunk_text)
        return chunks
    except Exception as e:
        logging.error(f"Error reading {pdf_path}: {e}")
        return []


def create_partial_prompt(question, chunk_text, part, total):
    """Prompt for partial document analysis"""
    return f"""Analyze the following section from a research document (Part {part} of {total}). 
Answer the question based ONLY on the provided content. If information is insufficient, 
state that clearly while providing available insights.

Research Question: {question}

Document Section (Pages {(part - 1) * CHUNK_SIZE + 1}-{part * CHUNK_SIZE}):
{chunk_text}

Guidelines:
1. Focus on concrete facts from the text
2. Highlight key findings relevant to the question
3. Note any limitations of the presented data
4. Use technical terminology from the document
5. Avoid speculation beyond provided information
6. Keep summary under 500 words

Analysis:"""


def create_aggregate_prompt(question, partials):
    """Prompt for document-level synthesis"""
    return f"""Synthesize partial analyses into a comprehensive answer. Resolve contradictions 
and maintain scientific accuracy. Follow this structure:

1. Key Findings Summary
2. Methodology Overview
3. Supporting Evidence
4. Limitations and Uncertainties
5. Conclusion

Research Question: {question}

Partial Analyses:
{"".join([f"--- PART {i + 1} ---{p}" for i, p in enumerate(partials)])}

Final Synthesis Guidelines:
- Prioritize conclusions supported by multiple sections
- Clearly indicate speculative elements
- Maintain original technical terminology
- If sections contradict, explain possible reasons
- Keep summary under 500 words

Comprehensive Answer:"""


def get_llm_response(prompt):
    """Get response from LLM"""
    try:
        data = {
            "model": "mistral-nemo-instruct-2407",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": -1
        }
        response = httpx.post(LLM_URL, json=data, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"LLM Error: {e}")
        return ""


def process_article(pdf_path, question, state):
    """Process single article"""
    article_id = pdf_path.stem
    if article_id in state.data["processed"]:
        logging.info(f"Skipping processed article: {article_id}")
        return

    chunks = read_pdf_chunks(pdf_path)
    if not chunks:
        return

    partials = []
    for i, chunk in enumerate(chunks):
        prompt = create_partial_prompt(question, chunk, i + 1, len(chunks))
        response = get_llm_response(prompt)
        partials.append(response)
        logging.info(f"Processed chunk {i + 1}/{len(chunks)} of {article_id}")

    aggregate_prompt = create_aggregate_prompt(question, partials)
    final_response = get_llm_response(aggregate_prompt)

    state.data["output"][article_id] = final_response
    state.data["processed"].append(article_id)
    state.save()
    logging.info(f"Completed processing: {article_id}")


def main(question):
    """Main processing workflow"""
    pdf_dir = Path("research")
    pdf_files = list(pdf_dir.glob("*.pdf"))

    state = ProcessingState()
    if not state.data["main_question"]:
        state.data["main_question"] = question
        state.save()

    setup_signal_handler(state)

    for pdf_path in pdf_files:
        process_article(pdf_path, question, state)

    # Save final results
    with open("answers.json", "w") as f:
        json.dump(state.data["output"], f, indent=2, ensure_ascii=False)
    logging.info("Results saved to answers.json")

    # Final aggregation
    aggregated = "\n".join([f"ARTICLE {id}:\n{resp}" for id, resp in state.data["output"].items()])
    final_prompt = f"""Generate a research-quality answer by synthesizing all article responses. 
Follow this structure:

1. **Consensus Findings** (Key points supported by multiple sources)
2. **Divergent Perspectives** (Conflicting evidence or interpretations)
3. **Methodological Comparison** (Strengths/weaknesses of approaches)
4. **Knowledge Gaps** (Unanswered questions needing research)
5. **Synthesis Conclusion** (Evidence-based final answer)

Original Question: {question}

Article Responses:
{aggregated}

Guidelines:
- Cite articles using their IDs (e.g., 'ARTICLE XYZ123')
- Maintain scientific precision
- Differentiate between strong and weak evidence

Final Synthesis:"""

    final_answer = get_llm_response(final_prompt)
    print("\nFINAL ANSWER:\n", final_answer)
    with open("final_answer.md", "w") as f:
        f.write(f"# Research Synthesis\n\n**Question**: {question}\n\n## Final Answer\n{final_answer}")


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