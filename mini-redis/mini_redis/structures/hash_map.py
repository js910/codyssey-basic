"""UTF-8 다항식 해시와 연결 리스트 체이닝을 사용하는 해시맵."""
from .linked_list import DoublyLinkedList

class HashMap:
    def __init__(self, capacity=8):
        """지정한 개수의 빈 버킷과 저장된 키 개수를 초기화한다."""
        if capacity < 1:
            raise ValueError('capacity must be positive')
        self._buckets = [None] * capacity
        self._size = 0

    def _index(self, key):
        """키의 UTF-8 바이트로 해시를 계산해 버킷 위치를 구한다."""
        value = 0
        for byte in key.encode('utf-8'):
            value = (value * 31 + byte) & 0xffffffffffffffff
        return value % len(self._buckets)

    def _find(self, key):
        """해당 버킷의 연결 리스트에서 키가 같은 노드를 찾는다."""
        bucket = self._buckets[self._index(key)]
        node = None if bucket is None else bucket.head
        while node is not None:
            if node.data[0] == key:
                return node
            node = node.next
        return None

    def put(self, key, value):
        """키의 값을 저장하거나 갱신하고 로드 팩터가 0.75를 넘으면 버킷을 두 배로 늘린다."""
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
        """키에 해당하는 값을 반환하고 키가 없으면 기본값을 반환한다."""
        node = self._find(key)
        return default if node is None else node.data[1]

    def contains(self, key):
        """해당 키가 해시맵에 저장되어 있는지 확인한다."""
        return self._find(key) is not None

    def remove(self, key):
        """키에 해당하는 노드를 제거하고 기존 값을 반환하며 없으면 None을 반환한다."""
        node = self._find(key)
        if node is None:
            return None
        self._size -= 1
        return self._buckets[self._index(key)].remove_node(node)[1]

    def keys(self):
        """모든 버킷의 연결 리스트를 순회하며 키를 하나씩 전달한다."""
        for bucket in self._buckets:
            node = None if bucket is None else bucket.head
            while node is not None:
                yield node.data[0]
                node = node.next

    def size(self):
        """현재 저장된 키의 개수를 반환한다."""
        return self._size
