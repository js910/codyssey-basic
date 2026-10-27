"""배열 기반 최소 힙. 튜플의 사전식 비교로 만료 시각을 정렬한다."""
class MinHeap:
    def __init__(self):
        self._items = []

    def size(self):
        return len(self._items)

    def peek(self):
        return self._items[0] if self._items else None

    def push(self, item):
        self._items.append(item)
        self._heapify_up(len(self._items) - 1)

    def pop(self):
        if not self._items:
            return None
        first = self._items[0]
        last = self._items.pop()
        if self._items:
            self._items[0] = last
            self._heapify_down(0)
        return first

    def _heapify_up(self, index):
        while index:
            parent = (index - 1) // 2
            if self._items[parent] <= self._items[index]:
                break
            self._items[parent], self._items[index] = self._items[index], self._items[parent]
            index = parent

    def _heapify_down(self, index):
        length = len(self._items)
        while index * 2 + 1 < length:
            child = index * 2 + 1
            if child + 1 < length and self._items[child + 1] < self._items[child]:
                child += 1
            if self._items[index] <= self._items[child]:
                break
            self._items[index], self._items[child] = self._items[child], self._items[index]
            index = child
