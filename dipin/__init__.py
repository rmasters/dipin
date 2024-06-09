__version__ = "0.0.3"

from .container import Container
from .interface import FastAPIContainer
from .resolver import CircularDependencyError

__all__ = ["DI", "Container", "CircularDependencyError"]


DI = FastAPIContainer()
