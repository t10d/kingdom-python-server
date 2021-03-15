from sqlalchemy import MetaData
import craftship.auth.adapters.orm
import craftship.management.adapters.orm


def start_mappers() -> MetaData:
    """
    Updates metadata reference and run sqlalchemy's mappers
    Classical way
    """
    metadata = MetaData()
    craftship.auth.adapters.orm.start_mappers(metadata)
    craftship.management.adapters.orm.start_mappers(metadata)

    return metadata
