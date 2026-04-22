from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from open_workshop_access import manager_client
from open_workshop_access.auth import require_service_token
from open_workshop_access.contracts.requests import ContextRequest
from open_workshop_access.contracts.state import AccessState


router = APIRouter(dependencies=[Depends(require_service_token)])


@router.post(
    "/context",
    summary="Get current static access context",
    response_model=AccessState,
    response_model_exclude_none=True,
)
async def context(
    request: Request,
    payload: ContextRequest,
) -> AccessState:
    return await manager_client.fetch_manager_context(request, user_id=payload.user_id)

