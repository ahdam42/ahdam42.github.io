import logging
from pathlib import Path

from DAO.ResearchState import ResearchState
from DAO.DocumentLinks import DocumentLinks
from prompt.LLMService import LLMService
from prompt.PromptService import PromptService
from utils.PDFUtils import PDFUtils
from utils.utils import normalize_arxiv_id, setup_signal_handler

def check_relevance(candidate_summary, arxiv_id):
    try:
        prompt = PromptService.create_relevance_prompt(candidate_summary)
        response = LLMService.get_llm_response(prompt, 0.8)
        if response.strip().lower() in ['да', 'yes']:
            return True
        
        return False
    except Exception as e:
        logging.error(f"Relevance check failed for {arxiv_id}: {str(e)}")
        return False

def process_pdfs(state, links):
    state.load()
    links.load()

    initial_files = list(Path("to research").glob("*.pdf"))
    for pdf_path in initial_files:
        try:
            text = PDFUtils.read_and_clean_pdf(pdf_path)
            if not text:
                continue

            summary = LLMService.get_llm_response(PromptService.create_summary_prompt(text), 0.8)
            state.data['main_summaries'].append(summary)
            
            arxiv_id_from_filename = pdf_path.stem 
            normalized_id = normalize_arxiv_id(arxiv_id_from_filename)
            
            doc_links = PDFUtils.extract_links_from_pdf(pdf_path)
            links.add_document(normalized_id, doc_links, summary)
            
            for arxiv_id in doc_links.get('arxiv', []):
                norm_id = normalize_arxiv_id(arxiv_id)
                if norm_id not in state.data['queue'] + state.data['processed']:
                    state.data['queue'].append(norm_id)
        except Exception as e:
            logging.error(f"Initial processing failed: {str(e)}")

    state.save()
    links.save()

    while state.data['queue']:
        current_id = state.data['queue'].pop(0)
        
        try:
            if current_id in state.data['processed']:
                continue

            logging.info(f"Processing: {current_id}")
            
            if PDFUtils.download_arxiv_pdf(current_id):
                pdf_path = Path("research") / f"{current_id}.pdf"
                doc_links = PDFUtils.extract_links_from_pdf(pdf_path)
                text = PDFUtils.read_and_clean_pdf(pdf_path)
                summary = LLMService.get_llm_response(PromptService.create_summary_prompt(text), 0.8)
                new_ids = [normalize_arxiv_id(id) for id in doc_links.get('arxiv', [])]
                
                if check_relevance(summary, current_id):
                    state.data['queue'].extend(new_ids)
                    links.add_document(current_id, doc_links, summary)
                    logging.info(f"Added relevant paper: {current_id}")
                else:
                    logging.info(f"Skipped irrelevant paper: {current_id}")

                state.data['processed'].append(current_id)
                
            state.save()
            links.save()

        except Exception as e:
            logging.error(f"Failed processing {current_id}: {str(e)}")
            state.data['queue'].insert(0, current_id)
            state.save()
            break

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('research.log'),
            logging.StreamHandler()
        ]
    )

    Path("to research").mkdir(exist_ok=True)
    Path("research").mkdir(exist_ok=True)

    state = ResearchState()
    links = DocumentLinks()
    setup_signal_handler(state, links)

    try:
        process_pdfs(state, links)
        logging.info("Processing completed successfully")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
    finally:
        state.save()
        links.save()
