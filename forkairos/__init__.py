# forkairos/__init__.py
from forkairos.domain import Domain
from forkairos.pipeline import run, get_provider

__version__ = "0.1.0"
__all__ = ["Domain", "run", "get_provider"]
