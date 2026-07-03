from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """
    A lightweight, synchronous Event Bus for decoupling services.
    Services can publish events (e.g. 'ticket-created') and other modules
    (like notification_service) can subscribe to them without tight coupling.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str) -> Callable:
        """
        Decorator to register a function as a handler for a specific event.
        Example:
            @event_bus.subscribe("ticket-created")
            def on_ticket_created(db, ticket_id, ...):
                ...
        """
        def decorator(func: Callable) -> Callable:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            self._subscribers[event_name].append(func)
            return func
        return decorator

    def publish(self, event_name: str, **kwargs: Any):
        """
        Publish an event to all registered subscribers.
        Example:
            event_bus.publish("ticket-created", db=db, ticket_id=1)
        """
        if event_name not in self._subscribers:
            logger.debug(f"EventBus: No subscribers for event '{event_name}'")
            return
            
        for handler in self._subscribers[event_name]:
            try:
                handler(**kwargs)
            except Exception as e:
                logger.error(f"EventBus: Error in handler {handler.__name__} for event '{event_name}': {e}")

# Global singleton event bus
event_bus = EventBus()
