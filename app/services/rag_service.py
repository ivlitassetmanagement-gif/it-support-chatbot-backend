import os
import uuid
from pathlib import Path
from pypdf import PdfReader
from docx import Document
from app.services.chromadb_service import ChromaDBService
import logging

logger = logging.getLogger(__name__)

class RAGService:
    '''Retrieval-Augmented Generation using ChromaDB'''
    
    def __init__(self):
        os.makedirs("./storage/docs", exist_ok=True)
        self.chromadb = ChromaDBService()
        self.documents_dir = "./storage/docs"
    
    def extract_text(self, file_path: str) -> str:
        '''Extract text from PDF, DOCX, or TXT'''
        path = Path(file_path)
        
        if path.suffix.lower() == ".pdf":
            reader = PdfReader(file_path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text
        
        if path.suffix.lower() == ".docx":
            doc = Document(file_path)
            text = "\n".join(p.text for p in doc.paragraphs)
            return text
        
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")
    
    def chunk_text(self, text: str, size: int = 900, overlap: int = 120) -> list:
        '''Split text into chunks for embedding'''
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    def index_file(self, file_path: str) -> dict:
        '''Index document: extract, chunk, embed, store'''
        try:
            text = self.extract_text(file_path)
            chunks = self.chunk_text(text)
            file_name = Path(file_path).name
            
            indexed_count = 0
            for i, chunk in enumerate(chunks):
                doc_id = f"{file_name}_chunk_{i}_{uuid.uuid4()}"
                
                success = self.chromadb.add_document(
                    doc_id=doc_id,
                    text=chunk,
                    metadata={
                        'source': file_name,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                )
                
                if success:
                    indexed_count += 1
            
            logger.info(f"Indexed {file_name}: {indexed_count}/{len(chunks)} chunks")
            
            return {
                "file": file_name,
                "chunks_indexed": indexed_count,
                "total_chunks": len(chunks),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error indexing file: {e}")
            return {"file": file_path, "status": "error", "error": str(e)}
    
    def retrieve(self, query: str, top_k: int = 4) -> tuple:
        '''Retrieve documents using semantic search'''
        try:
            results = self.chromadb.search(query, top_k=top_k)
            
            if results:
                docs_text = "\n\n---\n\n".join([
                    f"[Source: {r['source']} | Similarity: {r['similarity']:.2%}]\n{r['content']}"
                    for r in results
                ])
                sources = sorted(set(r['source'] for r in results))
                logger.info(f"Retrieved {len(results)} documents")
            else:
                docs_text = "No matching documents found."
                sources = []
                logger.warning(f"No documents found for query: {query[:50]}")
            
            return docs_text, sources
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return f"Error: {str(e)}", []
