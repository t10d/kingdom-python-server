from sqlalchemy.orm import Session
from sqlalchemy import create_engine, orm, MetaData

from src import config
import src.auth.adapters.orm

DEFAULT_SESSION_FACTORY: Session = orm.sessionmaker(
    bind=create_engine(
        # ISOLATION LEVEL ENSURES aggregate's version IS RESPECTED
        # That is, if version differs it will raise an exception
        config.get_postgres_uri(),
        isolation_level="REPEATABLE_READ",
    ),
    autoflush=False,
)

def start_mappers() -> MetaData:
    """
    Updates metadata reference and run sqlalchemy's mappers
    Classical way
    """
    metadata = MetaData()
    src.auth.adapters.orm.start_mappers(metadata)

    return metadata
