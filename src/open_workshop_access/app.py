from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from open_workshop_access import manager_client
from open_workshop_access.routers.catalog import router as catalog_router
from open_workshop_access.routers.context import router as context_router
from open_workshop_access.routers.mods import router as mods_router
from open_workshop_access.routers.profile import router as profile_router


app = FastAPI(
    title="Open Workshop Access",
    contact={
        "name": "GitHub",
        "url": "https://github.com/Open-Workshop",
    },
    license_info={
        "name": "GPL-3.0 license",
        "identifier": "GPL-3.0",
    },
    docs_url="/",
)


@app.exception_handler(manager_client.ManagerCallbackError)
async def manager_callback_error_handler(request, exc):
    _ = request
    status_code = exc.status_code or 502
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


app.include_router(context_router)
app.include_router(mods_router)
app.include_router(catalog_router)
app.include_router(profile_router)
