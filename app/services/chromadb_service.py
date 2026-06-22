import chromadb
import os
import logging
from pathlib import Path
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class ChromaDBService:
    '''Vector database for semantic search'''

    def __init__(self):
        try:
            chroma_dir = "./storage/chromadb"
            os.makedirs(chroma_dir, exist_ok=True)

            # New ChromaDB client initialization (v0.5+)
            self.client = chromadb.PersistentClient(path=chroma_dir)

            self.collection = self.client.get_or_create_collection(
                name="it_documents",
                metadata={"description": "IT Policy Documents"}
            )

            # Load embedding service lazily (on first use)
            self._embedding_service = None
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise

    @property
    def embedding_service(self):
        """Lazy load embedding service on first use"""
        if self._embedding_service is None:
            logger.info("Loading embedding model (this may take a minute on first run)...")
            self._embedding_service = EmbeddingService()
        return self._embedding_service
    
    def add_document(self, doc_id: str, text: str, metadata: dict = None) -> bool:
        '''Add document to ChromaDB'''
        try:
            embedding = self.embedding_service.embed_text(text)
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}]
            )
            logger.info(f"Document added: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    def search(self, query: str, top_k: int = 4) -> list:
        '''Search for documents by semantic similarity'''
        try:
            query_embedding = self.embedding_service.embed_text(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            documents = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i]
                    similarity = 1 - (distance / 2)
                    
                    documents.append({
                        'content': doc,
                        'similarity': similarity,
                        'source': results['metadatas'][0][i].get('source', 'unknown')
                    })
            
            logger.info(f"Search found {len(documents)} documents")
            return documents
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
