import re
import fitz
import requests
import json
import logging
import signal
import httpx
from pathlib import Path

LLM_URL = "http://localhost:1234/v1/chat/completions"
MAX_PAGES_FOR_SUMMARY = 5

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

def setup_signal_handler(state, links):
    def handler(signum, frame):
        logging.info("Received interrupt signal. Saving state...")
        state.save()
        links.save()
        exit(0)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

def normalize_arxiv_id(arxiv_id):
    return re.sub(r'v\d+$', '', arxiv_id, flags=re.IGNORECASE).lower().strip()

def read_and_clean_pdf(pdf_path, num_pages=MAX_PAGES_FOR_SUMMARY):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(min(num_pages, len(doc))):
            page = doc[page_num]
            text += page.get_text().replace('-\n', '').replace('\n', ' ')
        return text
    except Exception as e:
        logging.error(f"Error reading PDF {pdf_path}: {str(e)}")
        return ""

def create_prompt(main_summary, related_summary):
    return f"""Question: Does the Related Article supplement the Main Article by providing additional information, context, or supporting ideas, even indirectly?  

    ### MAIN ARTICLE START ###
    {main_summary}
    ### MAIN ARTICLE END ###

    ### RELATED ARTICLE START ###
	{related_summary}
    ### RELATED ARTICLE END ###

    Please provide a clear and concise answer: 'Yes' or 'No'. Only 'yes' or 'no' text in answer is accepted."""

def create_summary_prompt(text):
    return f"""Provide a comprehensive, structured summary of the article that addresses the following elements:  
1. **Title**: State the exact title of the article (if available).  
2. **Scope and Field**: Identify the article’s domain, research field, and overarching focus.  
3. **Methodology**: Explain *what* was investigated and *how* (methods, approaches, or frameworks used).  
4. **Key Results**: Summarize the findings, including quantitative/qualitative outcomes.  
5. **Critical Analysis**: Highlight limitations, uncertainties, or potential biases in the results.  
6. **Broader Context**: Discuss the article’s implications for its field or real-world applications.  

Ensure clarity and conciseness while covering all critical aspects. Avoid unnecessary details.  

### ARTICLE START ###  
{text}  
### ARTICLE END ###  

Summary:"""

def get_llm_response(prompt, temperature=0.8):
    try:
        data = {
            "model": "dolphin-2.9.3-mistral-nemo-12b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": -1
        }
        response = httpx.post(LLM_URL, json=data, timeout=None)
        response_data = response.json()
        
        if "choices" in response_data and len(response_data["choices"]) > 0:
            return response_data["choices"][0]["message"]["content"].strip()
        
        logging.error(f"Unexpected response structure: {response_data}")
        return ""
    except Exception as e:
        logging.error(f"LLM request failed: {str(e)}")
        return ""

def check_relevance(main_summaries, arxiv_id):
    normalized_id = normalize_arxiv_id(arxiv_id)
    pdf_path = Path("research") / f"{normalized_id}.pdf"
    
    if not pdf_path.exists():
        if not download_arxiv_pdf(normalized_id):
            return False

    try:
        text = read_and_clean_pdf(pdf_path)
        if not text:
            return False
            
        summary_prompt = create_summary_prompt(text)
        candidate_summary = get_llm_response(summary_prompt, 0.8)
        
        for main_summary in main_summaries:
            prompt = create_prompt(main_summary, candidate_summary)
            response = get_llm_response(prompt, 0.8)
            if response.strip().lower() in ['да', 'yes']:
                return True
        return False
    except Exception as e:
        logging.error(f"Relevance check failed for {arxiv_id}: {str(e)}")
        return False

def extract_links_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "".join([page.get_text().replace('\n', ' ') for page in doc])
        
        patterns = {
            'arxiv': re.compile(r'arxiv:\s*(\d{4}\.\d{4,}(?:v\d+)?)\b', re.I),
            'doi': re.compile(r'\b(10\.\d{4,}/[\S]+)\b', re.I),
            'url': re.compile(r'https?://\S+'),
            'pubmed': re.compile(r'pmid:\s?(\d+)'),
            'isbn': re.compile(r'\bISBN(?:-1[0-9]{3}(?:-[0-9]{3}){2}-[0-9X])?\b', re.I)
        }
        
        results = {}
        for key, pattern in patterns.items():
            matches = pattern.findall(text)
            clean_matches = [m[0].lower().strip() if isinstance(m, tuple) else m.lower().strip() for m in matches]
            if clean_matches:
                results[key] = list(set(clean_matches))
        
        if 'arxiv' in results:
            results['arxiv'] = [normalize_arxiv_id(id) for id in results['arxiv']]
        
        return results
    except Exception as e:
        logging.error(f"Error extracting links from {pdf_path}: {str(e)}")
        return {}

def download_arxiv_pdf(arxiv_id, save_dir="research"):
    normalized_id = normalize_arxiv_id(arxiv_id)
    Path(save_dir).mkdir(exist_ok=True)
    filename = Path(save_dir) / f"{normalized_id}.pdf"
    
    if filename.exists():
        logging.info(f"File {filename} already exists. Skipping download.")
        return True
    
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        if 'application/pdf' not in response.headers.get('Content-Type', ''):
            logging.error(f"Invalid content type for {arxiv_id}")
            return False
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logging.info(f"Successfully downloaded {normalized_id}")
        return True
    except Exception as e:
        logging.error(f"Failed to download {arxiv_id}: {str(e)}")
        return False

def process_pdfs(state, links):
    state.load()
    links.load()

    # Обработка начальных PDF
    initial_files = list(Path("to research").glob("*.pdf"))
    for pdf_path in initial_files:
        try:
            text = read_and_clean_pdf(pdf_path)
            if not text:
                continue
                
            # Создание summary для исходного файла
            summary = get_llm_response(create_summary_prompt(text), 0.8)
            state.data['main_summaries'].append(summary)
            
            # Извлечение arxiv_id из имени файла
            arxiv_id_from_filename = pdf_path.stem  # Пример: "1234.5678v2.pdf" → "1234.5678v2"
            normalized_id = normalize_arxiv_id(arxiv_id_from_filename)
            
            # Добавление в document_links
            doc_links = extract_links_from_pdf(pdf_path)
            links.add_document(normalized_id, doc_links, summary)
            
            # Добавление ссылок в очередь
            for arxiv_id in doc_links.get('arxiv', []):
                norm_id = normalize_arxiv_id(arxiv_id)
                if norm_id not in state.data['queue'] + state.data['processed']:
                    state.data['queue'].append(norm_id)
        except Exception as e:
            logging.error(f"Initial processing failed: {str(e)}")
    
    # Сохранение состояния после обработки начальных файлов
    state.save()
    links.save()

    # Обработка очереди
    while state.data['queue']:
        current_id = state.data['queue'].pop(0)
        
        try:
            if current_id in state.data['processed']:
                continue

            logging.info(f"Processing: {current_id}")
            
            if download_arxiv_pdf(current_id):
                pdf_path = Path("research") / f"{current_id}.pdf"
                doc_links = extract_links_from_pdf(pdf_path)
                text = read_and_clean_pdf(pdf_path)
                summary = get_llm_response(create_summary_prompt(text), 0.8)
                new_ids = [normalize_arxiv_id(id) for id in doc_links.get('arxiv', [])]
                
                if check_relevance(state.data['main_summaries'], current_id):
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
