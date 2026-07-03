import asyncio
from typing import Dict, List

class NotificationPubSub:
    """
    In-memory Pub/Sub for real-time Server-Sent Events (SSE) notifications.
    This avoids polling the database in a loop. When a notification is created,
    it is instantly pushed to the relevant connected user's queue.
    """
    def __init__(self):
        # Maps user_id to a list of active asyncio Queues (for multiple tabs/devices)
        self.connections: Dict[int, List[asyncio.Queue]] = {}

    def connect(self, user_id: int) -> asyncio.Queue:
        q = asyncio.Queue()
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(q)
        return q

    def disconnect(self, user_id: int, q: asyncio.Queue):
        if user_id in self.connections:
            if q in self.connections[user_id]:
                self.connections[user_id].remove(q)
            if not self.connections[user_id]:
                del self.connections[user_id]

    def notify_user(self, user_id: int, payload: dict):
        """Push a payload to a specific user's active SSE connections instantly."""
        if user_id in self.connections:
            for q in self.connections[user_id]:
                # put_nowait is safe to call from synchronous code since it doesn't block
                q.put_nowait(payload)

# Global pubsub instance
pubsub = NotificationPubSub()
