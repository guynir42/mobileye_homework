import os.path

import sqlalchemy as sa
from sqlalchemy import func, orm
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy_utils import database_exists, create_database

from contextlib import contextmanager

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

utcnow = func.timezone("UTC", func.current_timestamp())

_Session = None
_engine = None


def Session():
    """
    Make a session if it doesn't already exist.
    Use this in interactive sessions where you don't
    want to open the session as a context manager.
    If you want to use it in a context manager
    (the "with" statement where it closes at the
    end of the context) use SmartSession() instead.

    Returns
    -------
    sqlalchemy.orm.session.Session
        A session object that doesn't automatically close.
    """
    global _Session, _engine

    if _Session is None:
        # TODO: user must create an empty database named 'mobileye_hw' in postgresql
        url = "postgresql://postgres:postgres@localhost:5432/mobileye_hw"
        _engine = sa.create_engine(url, future=True, poolclass=sa.pool.NullPool)

        _Session = sessionmaker(bind=_engine, expire_on_commit=False)

        if not database_exists(_engine.url):
            create_database(_engine.url)
            Base.metadata.create_all(_engine)

    session = _Session()

    return session


@contextmanager
def SmartSession(*args):
    """
    Return a Session() instance that may or may not
    be inside a context manager.

    If a given input is already a session, just return that.
    If all inputs are None, create a session that would
    close at the end of the life of the calling scope.
    """
    global _Session, _engine

    for arg in args:
        if isinstance(arg, sa.orm.session.Session):
            yield arg
            return
        if arg is None:
            continue
        else:
            raise TypeError(
                "All inputs must be sqlalchemy sessions or None. "
                f"Instead, got {args}"
            )

    # none of the given inputs managed to satisfy any of the conditions...
    # open a new session and close it when outer scope is done
    with Session() as session:
        yield session


class MyBase:
    created_at = sa.Column(
        sa.DateTime,
        nullable=False,
        default=utcnow,
        index=True,
        doc="UTC time of insertion of object's row into the database.",
    )

    modified = sa.Column(
        sa.DateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
        doc="UTC time the object's row was last modified in the database.",
    )


# all models must inherit from this class
Base = declarative_base(cls=MyBase)


if __name__ == "__main__":
    from alembic import command
    from alembic.config import Config

    session = Session()
