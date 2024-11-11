from src.core.Queue.event import Event


class EventQueue:
    def __init__(self):
        self.queue: list[Event] = []

    def enqueue(self, event: Event):
        """Adding event to the queue, sorted by timestamp"""
        self.queue.append(event)
        self.queue.sort(key=lambda event: event.time)

    def dequeue(self) -> Event | None:
        """Get next event from queue"""
        if self.queue:
            return self.queue.pop(0)
        return None

    def peek(self) -> Event | None:
        """Look at next event without removing it"""
        if self.queue:
            return self.queue[0]
        return None

    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self.queue) == 0

    def clear(self) -> None:
        """Clear all events from queue"""
        self.queue.clear()
