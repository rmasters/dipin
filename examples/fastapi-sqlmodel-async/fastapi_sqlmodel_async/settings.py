from pathlib import Path
from typing import Annotated

from pydantic_settings import BaseSettings
from pydantic_core import Url
from pydantic.networks import UrlConstraints


SqliteDsn = Annotated[
    Url,
    UrlConstraints(
        host_required=False,
        allowed_schemes=[
            "sqlite+aiosqlite",
        ],
    ),
]


class Settings(BaseSettings):
    db_dsn: SqliteDsn = (
        f"sqlite+aiosqlite:///{Path(__file__).parent.parent / "db.sqlite"}"
    )
    blog_title: str = "My FastAPI Blog"
