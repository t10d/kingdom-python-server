from sqlalchemy import MetaData
import src.auth.adapters.orm


def start_mappers() -> MetaData:
    """
    Updates metadata reference and run sqlalchemy's mappers
    Classical way
    """
    metadata = MetaData()
    src.auth.adapters.orm.start_mappers(metadata)

    return metadata
