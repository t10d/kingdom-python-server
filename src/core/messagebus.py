import logging
from typing import Any, Callable, Dict, List, Type

from craftship.core.ports import unit_of_work
from craftship.core.domain import Command, Event, Message

logger = logging.getLogger("__internal_messagebus__")


class UnknownMessage(Exception):
    pass


class MessageBus:
    def __init__(
        self,
        uow: unit_of_work.AbstractUnitOfWork,
        event_handlers: Dict[Type[Event], List[Callable]],
        command_handlers: Dict[Type[Command], Callable],
        dependencies: Dict[str, Any],
    ):
        self.uow = uow
        self.dependencies = dependencies
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.queue = []

    async def handle_event(self, event: Event) -> None:
        for handler in self.event_handlers[type(event)]:
            logger.info(
                "Handling event %s with handler %s", event, handler.__name__
            )
            try:
                handler(event)
                self.queue.extend(self.uow.collect_new_events())
            except Exception as ex:
                logger.exception("Exception handling event %s: %s", event, ex)
                # raise

    async def handle_command(self, command: Command) -> None:
        logger.info("Handling command %s", command)
        try:
            handler = self.command_handlers[type(command)]
            handler(command)
            self.queue.extend(self.uow.collect_new_events())
        except Exception as ex:
            logger.exception("Exception handling command %s: %s", command, ex)
            raise

    def handle_map(self, message) -> Callable:
        if isinstance(message, Event):
            return self.handle_event
        elif isinstance(message, Command):
            return self.handle_command
        else:
            raise UnknownMessage()

    async def handle(self, message: Message) -> Any:
        self.queue: List[Message] = [message]
        while self.queue:
            # ever consuming queue
            current_msg = self.queue.pop(0)
            handle = self.handle_map(current_msg)
            await handle(current_msg)

        if self.queue:
            logger.warning(f"Not awaitable tasks: {self.queue}")
