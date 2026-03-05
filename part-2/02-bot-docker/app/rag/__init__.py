from __future__ import annotations

from importlib import import_module

__all__ = ["load_knowledge", "search"]


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module("app.rag.pipeline")
    return getattr(module, name)
