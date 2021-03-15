"""Binds and bootstraps services"""
from typing import Tuple, Optional, Dict
from sqlalchemy import MetaData

from src import orm, config
import src.auth.bootstrap
import src.auth.entrypoint


def init(
    start_orm: bool = True, **dependencies
) -> Tuple[Optional[MetaData], Dict]:
    """Starts-up as a monothilic service federating all aggregated-services
    Injecting dependencies as expected"""

    lambda_resolver = {}

    auth_uow, auth_email_sender = src.auth.bootstrap.create(**dependencies)
    src.auth.entrypoint.uow = auth_uow
    src.auth.entrypoint.email_sender = auth_email_sender

    if start_orm:
        metadata = orm.start_mappers()
        return metadata, lambda_resolver

    return None, lambda_resolver
