from src.core.Queue.event import Event

class EventQueue: 
    def __init__(self):
        self.queue : list[Event]= []

    def enqueue(self, event: Event): 
        """Adding event to the queue, sorted by timestamp"""
        self.queue.append(event)
        self.queue.sort(key=lambda event: event.time)


    def dequeue(self) -> Event | None:
        if self.queue:
            return self.queue.pop(0)
        return None

    def peek(self) -> Event | None:
        if self.queue:
            return self.queue[0]
        return None
    
    def is_empty(self) -> bool:
        return len(self.queue) == 0

