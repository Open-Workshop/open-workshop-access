from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from open_workshop_access import manager_client
from open_workshop_access.auth import require_service_token
from open_workshop_access.contracts.state import AccessState


router = APIRouter(dependencies=[Depends(require_service_token)])


@router.post(
    "/context",
    summary="Get current access context from active cookies",
    response_model=AccessState,
    response_model_exclude_none=True,
)
async def context(
    request: Request,
) -> AccessState:
    return await manager_client.fetch_manager_context(request)
