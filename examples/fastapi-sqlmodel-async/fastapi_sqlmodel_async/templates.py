from datetime import datetime, timezone
from pathlib import Path

from .di import DI
from fastapi.templating import Jinja2Templates
import humanize
import nltk

from .settings import Settings


templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

templates.env.globals["blog_title"] = DI.get(Settings).blog_title


def first_n_sentences(text: str, num_sentences: int = 5) -> str:
    sentences = nltk.sent_text(text)
    return " ".join(sentences[:num_sentences])


templates.env.filters["excerpt"] = first_n_sentences


def date_ago(occurrence: datetime) -> str:
    delta = datetime.now(timezone.utc) - occurrence

    twelve_hours = 12 * 60 * 60
    if delta.total_seconds() < twelve_hours:
        return humanize.naturaltime(delta)

    return humanize.naturalday(occurrence)


templates.env.filters["date_ago"] = date_ago
