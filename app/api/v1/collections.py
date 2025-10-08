"""
Collections API endpoints.
Handles CRUD operations for organizing sources into collections.
"""
import structlog
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.auth import CurrentUser
from app.core.errors import handle_api_error
from app.models.collection import (
    AddSourceToCollectionRequest,
    CollectionResponse,
    CollectionsListResponse,
    CollectionWithSourcesResponse,
    CreateCollectionRequest,
    UpdateCollectionRequest,
)
from app.services.supabase_service import supabase_service

router = APIRouter()
logger = structlog.get_logger()


@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    request: CreateCollectionRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """Create a new collection."""
    try:
        user_id = current_user["user_id"]
        supabase = supabase_service.get_client()

        collection_data = {
            "user_id": user_id,
            "name": request.name,
            "description": request.description,
            "is_public": request.is_public,
        }

        result = supabase.table("collections").insert(collection_data).execute()
        collection = result.data[0]

        logger.info("collection_created", collection_id=collection["id"], user_id=user_id)

        return JSONResponse(content=collection, status_code=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error("create_collection_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)


@router.get("/collections", response_model=CollectionsListResponse)
async def list_collections(
    current_user: CurrentUser,
) -> JSONResponse:
    """List all collections for authenticated user."""
    try:
        user_id = current_user["user_id"]
        supabase = supabase_service.get_client()

        result = supabase.table("collections").select("*").eq("user_id", user_id).order(
            "created_at", desc=True
        ).execute()

        return JSONResponse(content={"data": result.data, "total": len(result.data)})

    except Exception as e:
        logger.error("list_collections_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)


@router.get("/collections/{collection_id}", response_model=CollectionWithSourcesResponse)
async def get_collection(
    collection_id: str,
    current_user: CurrentUser,
) -> JSONResponse:
    """Get a collection with its sources."""
    try:
        user_id = current_user["user_id"]
        supabase = supabase_service.get_client()

        # Get collection
        collection_result = supabase.table("collections").select("*").eq(
            "id", collection_id
        ).eq("user_id", user_id).single().execute()

        if not collection_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )

        # Get sources in collection
        sources_result = supabase.rpc(
            "get_sources_by_collection",
            {"p_user_id": user_id, "p_collection_id": collection_id, "p_limit": 100, "p_offset": 0}
        ).execute()

        return JSONResponse(
            content={
                "collection": collection_result.data,
                "sources": sources_result.data or [],
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_collection_error", error=str(e), collection_id=collection_id)
        return handle_api_error(e)


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: str,
    current_user: CurrentUser,
) -> None:
    """Delete a collection."""
    try:
        user_id = current_user["user_id"]
        supabase = supabase_service.get_client()

        result = supabase.table("collections").delete().eq("id", collection_id).eq(
            "user_id", user_id
        ).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )

        logger.info("collection_deleted", collection_id=collection_id, user_id=user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_collection_error", error=str(e), collection_id=collection_id)
        raise


@router.post("/collections/{collection_id}/sources", status_code=status.HTTP_201_CREATED)
async def add_source_to_collection(
    collection_id: str,
    request: AddSourceToCollectionRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """Add a source to a collection."""
    try:
        user_id = current_user["user_id"]
        supabase = supabase_service.get_client()

        # Verify collection ownership
        collection_check = supabase.table("collections").select("id").eq(
            "id", collection_id
        ).eq("user_id", user_id).single().execute()

        if not collection_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )

        # Verify source ownership
        source_check = supabase.table("sources").select("id").eq(
            "id", request.source_id
        ).eq("user_id", user_id).single().execute()

        if not source_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found"
            )

        # Add to collection_sources junction table
        result = supabase.table("collection_sources").insert({
            "collection_id": collection_id,
            "source_id": request.source_id,
        }).execute()

        logger.info(
            "source_added_to_collection",
            collection_id=collection_id,
            source_id=request.source_id,
            user_id=user_id,
        )

        return JSONResponse(content={"message": "Source added to collection"}, status_code=status.HTTP_201_CREATED)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "add_source_to_collection_error",
            error=str(e),
            collection_id=collection_id,
        )
        return handle_api_error(e)
