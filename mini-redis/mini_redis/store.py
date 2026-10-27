"""해시맵, LRU 리스트, 만료 힙을 결합한 메모리 저장소."""
import math
import time
from .structures.hash_map import HashMap
from .structures.linked_list import DoublyLinkedList
from .structures.min_heap import MinHeap

class Entry:
    def __init__(self, key, value, node):
        self.value = value
        self.node = node
        self.bytes = len(key.encode('utf-8')) + len(value.encode('utf-8'))
        self.expire_at = None
        self.version = None

class Store:
    def __init__(self, clock=time.monotonic):
        self.data = HashMap()
        self.lru = DoublyLinkedList()
        self.expirations = MinHeap()
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0
        self._version = 0
        self._clock = clock

    def _delete(self, key):
        entry = self.data.remove(key)
        if entry is None:
            return False
        self.lru.remove_node(entry.node)
        self.used_memory -= entry.bytes
        # 과거 힙 기록은 버전 검증으로 무효화한다 (lazy deletion).
        return True

    def purge_expired(self):
        now = self._clock()
        while self.expirations.size() and self.expirations.peek()[0] <= now:
            _, key, version = self.expirations.pop()
            entry = self.data.get(key)
            if entry is not None and entry.version == version:
                self._delete(key)
        # 반복 EXPIRE/DEL로 생긴 무효 기록이 무한히 쌓이지 않게 재구성한다.
        if self.expirations.size() > max(64, self.data.size() * 2):
            heap = MinHeap()
            for key in self.data.keys():
                entry = self.data.get(key)
                if entry.expire_at is not None:
                    heap.push((entry.expire_at, key, entry.version))
            self.expirations = heap

    def set(self, key, value):
        self.purge_expired()
        size = len(key.encode('utf-8')) + len(value.encode('utf-8'))
        if self.maxmemory and size > self.maxmemory:
            return False
        self._delete(key)
        node = self.lru.insert_front(key)
        self.data.put(key, Entry(key, value, node))
        self.used_memory += size
        while self.maxmemory and self.used_memory > self.maxmemory:
            self._delete(self.lru.tail.data)
            self.evicted_keys += 1
        return True

    def get(self, key):
        self.purge_expired()
        entry = self.data.get(key)
        if entry is None:
            return None
        self.lru.move_to_front(entry.node)
        return entry.value

    def delete(self, key):
        self.purge_expired()
        return int(self._delete(key))

    def exists(self, key):
        self.purge_expired()
        return int(self.data.contains(key))

    def expire(self, key, seconds):
        self.purge_expired()
        entry = self.data.get(key)
        if entry is None:
            return 0
        if seconds <= 0:
            self._delete(key)
            return 1
        self._version += 1
        entry.expire_at = self._clock() + seconds
        entry.version = self._version
        self.expirations.push((entry.expire_at, key, entry.version))
        return 1

    def ttl(self, key):
        self.purge_expired()
        entry = self.data.get(key)
        if entry is None:
            return -2
        if entry.expire_at is None:
            return -1
        return max(0, math.floor(entry.expire_at - self._clock()))
