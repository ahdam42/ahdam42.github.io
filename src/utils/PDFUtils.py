import logging
import fitz
from pathlib import Path
import re
import requests
from typing import List
from src.utils.utils import normalize_arxiv_id, sanitize_text

MAX_PAGES_FOR_SUMMARY = 5
CHUNK_SIZE = 5 

class PDFUtils:
    @staticmethod
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

    @staticmethod
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
    
    @staticmethod
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
                exit(1)
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logging.info(f"Successfully downloaded {normalized_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to download {arxiv_id}: {str(e)}")
            return False