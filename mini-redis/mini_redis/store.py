"""해시맵, LRU 리스트, 만료 힙을 결합한 메모리 저장소."""
import math
import time
from .structures.hash_map import HashMap
from .structures.linked_list import DoublyLinkedList
from .structures.min_heap import MinHeap

class Entry:
    def __init__(self, key, value, node):
        """값과 LRU 노드 참조, 바이트 크기, 만료 정보를 하나로 묶는다."""
        self.value = value
        self.node = node
        self.bytes = len(key.encode('utf-8')) + len(value.encode('utf-8'))
        self.expire_at = None
        self.version = None

class Store:
    def __init__(self, clock=time.monotonic):
        """데이터 해시맵과 LRU 리스트, 만료 힙, 메모리 집계를 초기화한다."""
        self.data = HashMap()
        self.lru = DoublyLinkedList()
        self.expirations = MinHeap()
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0
        self._version = 0
        self._clock = clock

    def _delete(self, key):
        """키의 데이터와 LRU 노드를 삭제하고 사용 메모리를 차감한다."""
        entry = self.data.remove(key)
        if entry is None:
            return False
        self.lru.remove_node(entry.node)
        self.used_memory -= entry.bytes
        # 과거 힙 기록은 버전 검증으로 무효화한다 (lazy deletion).
        return True

    def purge_expired(self):
        """만료된 키를 삭제하고 오래된 만료 기록이 많이 쌓이면 힙을 다시 만든다."""
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
        """값을 최근 사용 위치에 저장하고 용량이 부족하면 오래 사용하지 않은 키부터 제거한다."""
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
        """만료되지 않은 값을 조회하고 성공한 키를 최근 사용 위치로 옮긴다."""
        self.purge_expired()
        entry = self.data.get(key)
        if entry is None:
            return None
        self.lru.move_to_front(entry.node)
        return entry.value

    def delete(self, key):
        """만료된 키를 정리한 뒤 대상 키를 삭제하고 성공 여부를 1 또는 0으로 반환한다."""
        self.purge_expired()
        return int(self._delete(key))

    def exists(self, key):
        """만료된 키를 정리한 뒤 대상 키가 있으면 1, 없으면 0을 반환한다."""
        self.purge_expired()
        return int(self.data.contains(key))

    def expire(self, key, seconds):
        """키의 만료 시간을 설정하고 입력한 초가 0 이하이면 즉시 삭제한다."""
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
        """남은 만료 시간을 초 단위로 반환하며 만료 설정이 없으면 -1, 키가 없으면 -2를 반환한다."""
        self.purge_expired()
        entry = self.data.get(key)
        if entry is None:
            return -2
        if entry.expire_at is None:
            return -1
        return max(0, math.floor(entry.expire_at - self._clock()))
