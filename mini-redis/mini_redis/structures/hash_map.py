"""UTF-8 다항식 해시와 연결 리스트 체이닝을 사용하는 해시맵."""
from .linked_list import DoublyLinkedList

class HashMap:
    def __init__(self, capacity=8):
        if capacity < 1:
            raise ValueError('capacity must be positive')
        self._buckets = [None] * capacity
        self._size = 0

    def _index(self, key):
        value = 0
        for byte in key.encode('utf-8'):
            value = (value * 31 + byte) & 0xffffffffffffffff
        return value % len(self._buckets)

    def _find(self, key):
        bucket = self._buckets[self._index(key)]
        node = None if bucket is None else bucket.head
        while node is not None:
            if node.data[0] == key:
                return node
            node = node.next
        return None

    def put(self, key, value):
        node = self._find(key)
        if node is not None:
            node.data = (key, value)
            return
        index = self._index(key)
        if self._buckets[index] is None:
            self._buckets[index] = DoublyLinkedList()
        self._buckets[index].insert_back((key, value))
        self._size += 1
        if self._size > len(self._buckets) * 0.75:
            old = self._buckets
            self._buckets = [None] * (len(old) * 2)
            self._size = 0
            for bucket in old:
                node = None if bucket is None else bucket.head
                while node is not None:
                    self.put(*node.data)
                    node = node.next

    def get(self, key, default=None):
        node = self._find(key)
        return default if node is None else node.data[1]

    def contains(self, key):
        return self._find(key) is not None

    def remove(self, key):
        node = self._find(key)
        if node is None:
            return None
        self._size -= 1
        return self._buckets[self._index(key)].remove_node(node)[1]

    def keys(self):
        for bucket in self._buckets:
            node = None if bucket is None else bucket.head
            while node is not None:
                yield node.data[0]
                node = node.next

    def size(self):
        return self._size
