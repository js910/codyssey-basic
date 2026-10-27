"""배열 기반 최소 힙. 튜플의 사전식 비교로 만료 시각을 정렬한다."""
class MinHeap:
    def __init__(self):
        """힙 항목을 담을 빈 배열을 만든다."""
        self._items = []

    def size(self):
        """현재 힙에 저장된 항목 수를 반환한다."""
        return len(self._items)

    def peek(self):
        """가장 작은 항목을 삭제하지 않고 확인하며 비어 있으면 None을 반환한다."""
        return self._items[0] if self._items else None

    def push(self, item):
        """새 항목을 배열 끝에 넣고 부모와 비교하며 올바른 위치로 올린다."""
        self._items.append(item)
        self._heapify_up(len(self._items) - 1)

    def pop(self):
        """가장 작은 항목을 꺼내고 남은 항목의 힙 순서를 복구한다."""
        if not self._items:
            return None
        first = self._items[0]
        last = self._items.pop()
        if self._items:
            self._items[0] = last
            self._heapify_down(0)
        return first

    def _heapify_up(self, index):
        """항목을 부모와 비교하며 위로 이동시켜 최소 힙 순서를 맞춘다."""
        while index:
            parent = (index - 1) // 2
            if self._items[parent] <= self._items[index]:
                break
            self._items[parent], self._items[index] = self._items[index], self._items[parent]
            index = parent

    def _heapify_down(self, index):
        """항목을 더 작은 자식과 비교하며 아래로 이동시켜 최소 힙 순서를 맞춘다."""
        length = len(self._items)
        while index * 2 + 1 < length:
            child = index * 2 + 1
            if child + 1 < length and self._items[child + 1] < self._items[child]:
                child += 1
            if self._items[index] <= self._items[child]:
                break
            self._items[index], self._items[child] = self._items[child], self._items[index]
            index = child
