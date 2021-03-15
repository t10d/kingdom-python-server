from typing import Dict

from src.core import messagebus, utils
from src.core.ports.unit_of_work import AbstractUnitOfWork


def create(
    dependencies: Dict,
    command_handlers: Dict,
    event_handlers: Dict,
    uow: AbstractUnitOfWork,
) -> messagebus.MessageBus:
    """
    Creates a message bus with its handlers dependencies set programmatically
    Default dependencies do matter and are used on production environments
    """
    command_injected = {
        command_type: utils.inject_dependencies(command_handler, dependencies)
        for command_type, command_handler in command_handlers.items()
    }
    event_injected = {
        event_type: [
            utils.inject_dependencies(handler, dependencies)
            for handler in event_handlers
        ]
        for event_type, event_handlers in event_handlers.items()
    }
    return messagebus.MessageBus(
        uow=uow,
        event_handlers=event_injected,
        command_handlers=command_injected,
        dependencies=dependencies,
    )
