"""Binds and bootstraps services"""
from typing import Tuple, Optional, Dict
from sqlalchemy import MetaData

from apolo import orm, config
import craftship.auth.bootstrap
import craftship.auth.entrypoint
import craftship.management.bootstrap
import craftship.management.entrypoint
import craftship.management.entrypoint.lambda_worker


def federation(
    start_orm: bool = True, **dependencies
) -> Tuple[Optional[MetaData], Dict]:
    """Starts-up as a monothilic service federating all aggregated-services
    Injecting dependencies as expected"""

    lambda_resolver = {
        "management": craftship.management.entrypoint.lambda_worker.RESOLVER
    }

    auth_uow, auth_email_sender = craftship.auth.bootstrap.create(**dependencies)
    craftship.auth.entrypoint.uow = auth_uow
    craftship.auth.entrypoint.email_sender = auth_email_sender
    management_bus = craftship.management.bootstrap.create(**dependencies)
    craftship.management.entrypoint.messagebus = management_bus

    if start_orm:
        metadata = orm.start_mappers()
        return metadata, lambda_resolver

    return None, lambda_resolver
