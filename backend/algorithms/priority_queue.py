"""
Priority queue for dispatching orders. Backed by Python's heapq (a real
binary min-heap), not by sorting in the frontend. Lower priority number =
dispatched first (1=Emergency ... 4=Low). Insertion order is used as a
tiebreaker so equal-priority orders stay FIFO.
"""
import heapq
import itertools
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(order=True)
class _HeapItem:
    priority: int
    seq: int
    order_id: Any = field(compare=False)


class OrderPriorityQueue:
    def __init__(self):
        self._heap: List[_HeapItem] = []
        self._counter = itertools.count()
        self._entry_map = {}  # order_id -> _HeapItem (for removal/lookup)

    def push(self, order_id, priority: int):
        item = _HeapItem(priority=priority, seq=next(self._counter), order_id=order_id)
        heapq.heappush(self._heap, item)
        self._entry_map[order_id] = item

    def pop(self) -> Optional[Any]:
        """Pop the highest-priority (lowest number) order id."""
        while self._heap:
            item = heapq.heappop(self._heap)
            if self._entry_map.get(item.order_id) is item:
                del self._entry_map[item.order_id]
                return item.order_id
        return None

    def remove(self, order_id):
        """Lazily invalidate an entry (e.g., order was cancelled)."""
        self._entry_map.pop(order_id, None)

    def peek_all(self) -> List[dict]:
        """Return all currently valid entries sorted by dispatch priority."""
        valid = [i for i in self._heap if self._entry_map.get(i.order_id) is i]
        valid.sort()
        return [{"order_id": i.order_id, "priority": i.priority} for i in valid]

    def __len__(self):
        return len(self._entry_map)
