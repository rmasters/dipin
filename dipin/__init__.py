__version__ = "0.0.1"

from .container import Container
from .interface import FastAPIContainer
from .resolver import CircularDependencyError

__all__ = ["Container", "CircularDependencyError"]


DI = FastAPIContainer()
