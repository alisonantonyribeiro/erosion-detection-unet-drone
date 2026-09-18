from collections.abc import Iterator

from sqlalchemy.orm import Session

from erosion.repositories.db import get_db


def get_db_session() -> Iterator[Session]:
    yield from get_db()
