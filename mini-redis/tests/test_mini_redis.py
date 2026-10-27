"""Run with python -m unittest -v."""
import unittest
import random
from mini_redis.structures.linked_list import DoublyLinkedList
from mini_redis.structures.hash_map import HashMap
from mini_redis.structures.min_heap import MinHeap
from mini_redis.store import Store
from mini_redis.cli import CLI, INTEGER_ERROR, OOM

class StructuresTest(unittest.TestCase):
    def test_list(self):
        """연결 리스트의 삽입, 이동, 삭제와 잘못된 노드 삭제 처리를 확인한다."""
        linked = DoublyLinkedList()
        a = linked.insert_back('a')
        b = linked.insert_back('b')
        linked.move_to_front(b)
        self.assertIs(linked.head, b)
        self.assertIs(linked.tail, a)
        self.assertEqual(linked.remove_back(), 'a')
        self.assertEqual(linked.remove_front(), 'b')
        self.assertIsNone(linked.remove_front())
        self.assertEqual(linked.length, 0)
        c = linked.insert_front('c')
        self.assertEqual(linked.remove_node(c), 'c')
        with self.assertRaises(ValueError):
            linked.remove_node(c)

    def test_hash_collisions_and_resize(self):
        """해시 충돌과 버킷 확장 후에도 저장, 조회, 갱신, 삭제가 동작하는지 확인한다."""
        table = HashMap(2)
        # These two keys collide with the polynomial hash.
        table.put('Aa', 1)
        table.put('BB', 2)
        self.assertEqual(table.get('Aa'), 1)
        self.assertEqual(table.get('BB'), 2)
        for i in range(1000):
            table.put(str(i), i)
        for i in range(1000):
            self.assertEqual(table.get(str(i)), i)
        table.put('Aa', 3)
        self.assertEqual(table.size(), 1002)
        self.assertEqual(table.remove('Aa'), 3)
        self.assertFalse(table.contains('Aa'))
        self.assertEqual(len(list(table.keys())), 1001)

    def test_heap(self):
        """순서 없이 넣은 항목이 작은 값부터 나오고 빈 힙도 처리되는지 확인한다."""
        heap = MinHeap()
        values = list(range(300))
        random.Random(42).shuffle(values)
        for value in values:
            heap.push((value, str(value)))
        self.assertEqual(heap.peek(), (0, '0'))
        self.assertEqual([heap.pop()[0] for _ in values], list(range(300)))
        self.assertIsNone(heap.pop())

class StoreTest(unittest.TestCase):
    def setUp(self):
        """각 테스트에서 사용할 조절 가능한 시계와 새 저장소, CLI를 준비한다."""
        self.now = 100.0
        self.db = Store(lambda: self.now)
        self.cli = CLI(self.db)

    def test_commands_and_quotes(self):
        """기본 명령어와 공백을 포함한 값, 종료 명령의 처리를 확인한다."""
        self.assertEqual(self.cli.execute('SET user "Alice Kim"'), 'OK')
        self.assertEqual(self.cli.execute('GET user'), '"Alice Kim"')
        self.assertEqual(self.cli.execute('EXISTS user'), '(integer) 1')
        self.assertEqual(self.cli.execute('DBSIZE'), '(integer) 1')
        self.assertIn('"user"', self.cli.execute('KEYS'))
        self.assertEqual(self.cli.execute('DEL user'), '(integer) 1')
        self.assertEqual(self.cli.execute('DEL user'), '(integer) 0')
        self.assertEqual(self.cli.execute('KEYS'), '(empty array)')
        self.assertIsNone(self.cli.execute('quit'))

    def test_lru(self):
        """조회한 키의 사용 순서가 바뀌어 오래 사용하지 않은 키부터 제거되는지 확인한다."""
        self.db.maxmemory = 4
        self.db.set('a', '1')
        self.db.set('b', '2')
        self.db.get('a')
        self.db.set('c', '3')
        self.assertEqual(self.db.get('a'), '1')
        self.assertIsNone(self.db.get('b'))
        self.assertEqual(self.db.used_memory, 4)
        self.assertEqual(self.db.evicted_keys, 1)

    def test_oom_preserves_old_value_and_ttl(self):
        """저장할 값이 너무 크면 기존 값과 만료 시간이 유지되는지 확인한다."""
        self.db.set('a', '1')
        self.db.expire('a', 10)
        self.db.maxmemory = 3
        self.assertEqual(self.cli.execute('SET a toolong'), OOM)
        self.assertEqual(self.db.get('a'), '1')
        self.assertEqual(self.db.ttl('a'), 10)
        self.assertEqual(self.db.evicted_keys, 0)

    def test_utf8_accounting(self):
        """한글을 포함한 키와 값의 저장, 덮어쓰기, 삭제 시 바이트 계산을 확인한다."""
        self.db.set('한', '글')
        self.assertEqual(self.db.used_memory, 6)
        self.db.set('한', 'a')
        self.assertEqual(self.db.used_memory, 4)
        self.db.delete('한')
        self.assertEqual(self.db.used_memory, 0)

    def test_ttl_and_expired_global_commands(self):
        """만료 상태와 남은 시간, 만료 후 키 개수와 메모리 정리를 확인한다."""
        self.assertEqual(self.db.ttl('a'), -2)
        self.db.set('a', '1')
        self.assertEqual(self.db.ttl('a'), -1)
        self.db.expire('a', 3)
        self.now += 1.2
        self.assertEqual(self.db.ttl('a'), 1)
        self.now += 1.8
        self.assertEqual(self.cli.execute('DBSIZE'), '(integer) 0')
        self.assertEqual(self.db.used_memory, 0)
        self.assertEqual(self.db.lru.length, 0)
        self.assertIsNone(self.db.get('a'))
        self.assertEqual(self.db.evicted_keys, 0)

    def test_stale_expiration_after_overwrite_delete_and_reschedule(self):
        """덮어쓰기, 삭제 후 재생성, TTL 변경 때 예전 기록이 새 값을 지우지 않는지 확인한다."""
        self.db.set('a', '1')
        self.db.expire('a', 2)
        self.db.set('a', '2')
        self.now += 3
        self.assertEqual(self.db.get('a'), '2')
        self.assertEqual(self.db.ttl('a'), -1)
        self.db.expire('a', 2)
        self.db.delete('a')
        self.db.set('a', '3')
        self.db.expire('a', 10)
        self.now += 3
        self.assertEqual(self.db.get('a'), '3')
        self.db.expire('a', 20)
        self.now += 8
        self.assertEqual(self.db.get('a'), '3')
        self.assertEqual(self.db.expire('missing', 1), 0)
        self.assertEqual(self.db.expire('a', 0), 1)
        self.assertEqual(self.db.ttl('a'), -2)

    def test_heap_compaction(self):
        """반복된 만료 설정의 오래된 기록을 정리하고 최신 만료를 유지하는지 확인한다."""
        self.db.set('a', '1')
        for _ in range(1000):
            self.db.expire('a', 1000)
        self.db.purge_expired()
        self.assertLessEqual(self.db.expirations.size(), 64)
        self.now += 1000
        self.assertIsNone(self.db.get('a'))

    def test_errors(self):
        """명령어, 인자 수, 따옴표, 정수 입력 오류와 메모리 정보 출력을 확인한다."""
        self.assertIn('unknown command', self.cli.execute('HELLO'))
        self.assertIn('wrong number', self.cli.execute('GET'))
        self.assertIn('invalid quoting', self.cli.execute('SET a "'))
        for value in ('abc', '-1', '1.0', '9223372036854775808'):
            self.assertEqual(self.cli.execute('CONFIG SET maxmemory ' + value), INTEGER_ERROR)
        self.assertEqual(self.cli.execute('EXPIRE a abc'), INTEGER_ERROR)
        self.assertEqual(self.cli.execute('CONFIG SET maxmemory 0'), 'OK')
        self.assertIn('used_memory:0', self.cli.execute('INFO memory'))

if __name__ == '__main__':
    unittest.main()
