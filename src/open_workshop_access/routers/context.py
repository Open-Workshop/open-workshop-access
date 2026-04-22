from __future__ import annotations

from fastapi import APIRouter, Request

from open_workshop_access import manager_client
from open_workshop_access.contracts.state import AccessContext


router = APIRouter()


@router.post(
    "/context",
    summary="Get current access context from active cookies",
    response_model=AccessContext,
    response_model_exclude_none=True,
)
async def context(
    request: Request,
) -> AccessContext:
    return await manager_client.fetch_manager_context(request)
