from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.rag.embedding_service import (
    EmbeddingConfigurationError,
    EmbeddingServiceError,
)
from app.rag.rag_pipeline import RAGPipeline
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse

router = APIRouter()


def get_rag_pipeline() -> RAGPipeline:
    """Dependency provider for RAGPipeline so tests can override or inject mock services."""
    return RAGPipeline()


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="AI-powered natural-language fashion discovery (RAG)",
)
def query_rag(
    payload: RAGQueryRequest,
    db: Session = Depends(get_db),
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
):
    """
    Execute hybrid semantic + structured retrieval over PostgreSQL products
    and generate a grounded explanation using Gemini.
    """
    try:
        return pipeline.run(
            db=db,
            query=payload.query,
            top_k=payload.top_k,
        )
    except EmbeddingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except EmbeddingServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
