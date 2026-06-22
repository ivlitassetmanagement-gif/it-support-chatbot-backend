"""Document upload and management routes"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from app.services.chromadb_service import ChromaDBService
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
chroma_service = ChromaDBService()

DOCS_DIR = "./storage/docs"
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx', '.doc', '.md'}

@router.post('/documents/upload')
async def upload_document(file: UploadFile, request: Request):
    """Upload a document for knowledge base"""
    try:
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else 'unknown'

        # Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Create docs directory if not exists
        os.makedirs(DOCS_DIR, exist_ok=True)

        # Save file
        file_path = os.path.join(DOCS_DIR, file.filename)
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Document uploaded: {file.filename} by user {user_id}")

        return {
            "status": "success",
            "filename": file.filename,
            "message": f"Document '{file.filename}' uploaded successfully. It will be indexed shortly.",
            "path": file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get('/documents/list')
async def list_documents(request: Request):
    """List all uploaded documents"""
    try:
        if not os.path.exists(DOCS_DIR):
            return {"documents": [], "count": 0}

        documents = []
        for file in os.listdir(DOCS_DIR):
            file_path = os.path.join(DOCS_DIR, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                documents.append({
                    "filename": file,
                    "size": size,
                    "size_kb": round(size / 1024, 2)
                })

        logger.info(f"Listed {len(documents)} documents")
        return {
            "documents": documents,
            "count": len(documents)
        }

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/documents/index')
async def index_documents(request: Request):
    """Index all documents in ChromaDB"""
    try:
        if not os.path.exists(DOCS_DIR):
            raise HTTPException(status_code=404, detail="No documents directory found")

        indexed_count = 0
        for file in os.listdir(DOCS_DIR):
            file_path = os.path.join(DOCS_DIR, file)
            if os.path.isfile(file_path) and os.path.splitext(file)[1].lower() in ALLOWED_EXTENSIONS:
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Index in ChromaDB
                    if content.strip():
                        chroma_service.add_document(
                            doc_id=file,
                            content=content,
                            metadata={"filename": file}
                        )
                        indexed_count += 1
                        logger.info(f"Indexed document: {file}")
                except Exception as e:
                    logger.warning(f"Failed to index {file}: {e}")

        return {
            "status": "success",
            "indexed_count": indexed_count,
            "message": f"Successfully indexed {indexed_count} documents"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/documents/{filename}')
async def delete_document(filename: str, request: Request):
    """Delete a document"""
    try:
        file_path = os.path.join(DOCS_DIR, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document not found")

        os.remove(file_path)
        logger.info(f"Document deleted: {filename}")

        return {
            "status": "success",
            "message": f"Document '{filename}' deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
