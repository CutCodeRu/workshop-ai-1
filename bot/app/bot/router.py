from __future__ import annotations

from aiogram import Router

from app.handlers import (
    fallback_router,
    knowledge_router,
    lead_router,
    start_router,
)


def setup_routers() -> Router:
    router = Router(name="root")
    router.include_router(start_router)
    router.include_router(lead_router)
    router.include_router(knowledge_router)
    router.include_router(fallback_router)
    return router
