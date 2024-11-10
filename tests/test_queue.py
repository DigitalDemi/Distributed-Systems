from core.Queue.event_queue import EventQueue
from core.Queue.event_type import EventType
from core.Queue.event import Event
import random


def test_queue():

    queue = EventQueue()

    assert queue.is_empty()

    events = []

    for i in range(10):
        event = Event(
            type=random.choice(list(EventType)),
            time=random.uniform(0, 100),
            data={"buyer_id": str(i)},
            sender_id=f"TEST_{i}",
        )
        events.append(event)
        print("\nCreated event:", event)

    random.shuffle(events)

    for event in events:
        queue.enqueue(event)

    print("\nInitial queue state:", queue.queue)

    dequeued_event = []
    while not queue.is_empty():
        print("\nDequeued event:", queue.peek())
        dequeued_event.append(queue.dequeue())

    timestamp = [e.time for e in dequeued_event]
    assert timestamp == sorted(timestamp)
