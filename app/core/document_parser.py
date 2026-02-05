import os
import logging
from typing import Dict, Any, Optional
from pypdf import PdfReader
from docx import Document

logger = logging.getLogger(__name__)

class DocumentParser:
    """
    generic parser for pdf and docx
    extracts raw text
    """
    
    @staticmethod
    def parse(file_path: str) -> Dict[str, Any]:
        """
        parse based on extension
        returns dict with content and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == ".pdf":
                return DocumentParser._parse_pdf(file_path)
            elif ext in [".docx", ".doc"]:
                return DocumentParser._parse_docx(file_path)
            elif ext == ".txt":
                 with open(file_path, 'r', encoding='utf-8') as f:
                     return {"content": f.read(), "metadata": {"type": "text"}}
            else:
                raise ValueError(f"Unsupported file format: {ext}")
                
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return {"content": "", "metadata": {"error": str(e)}}

    @staticmethod
    def _parse_pdf(file_path: str) -> Dict[str, Any]:
        reader = PdfReader(file_path)
        text = ""
        meta = {}
        
        if reader.metadata:
            meta = {k: str(v) for k, v in reader.metadata.items()}
            
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        return {
            "content": text.strip(),
            "metadata": {**meta, "type": "pdf", "pages": len(reader.pages)}
        }

    @staticmethod
    def _parse_docx(file_path: str) -> Dict[str, Any]:
        doc = Document(file_path)
        text = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        return {
            "content": "\n".join(text),
            "metadata": {"type": "docx"}
        }
