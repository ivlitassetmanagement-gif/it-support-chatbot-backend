from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    '''Convert text to embeddings (meaning signatures)'''
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded: all-MiniLM-L6-v2")
    
    def embed_text(self, text: str) -> list:
        '''Convert text to embedding'''
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise
    
    def embed_multiple(self, texts: list) -> list:
        '''Convert multiple texts to embeddings'''
        try:
            embeddings = self.model.encode(texts)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error embedding multiple texts: {e}")
            raise
