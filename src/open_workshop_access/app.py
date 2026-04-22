from __future__ import annotations

from fastapi import FastAPI

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

app.include_router(context_router)
app.include_router(mods_router)
app.include_router(catalog_router)
app.include_router(profile_router)
