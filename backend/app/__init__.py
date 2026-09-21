# AI Startup Radar - Backend
import importlib

__version__ = "1.0.0"


def __getattr__(name):
    if name == "app":
        return importlib.import_module("app.main").app
    if name == "celery_app":
        return importlib.import_module("app.core.celery_app").celery_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")