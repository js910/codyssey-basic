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
        self.now = 100.0
        self.db = Store(lambda: self.now)
        self.cli = CLI(self.db)

    def test_commands_and_quotes(self):
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
        self.db.set('a', '1')
        self.db.expire('a', 10)
        self.db.maxmemory = 3
        self.assertEqual(self.cli.execute('SET a toolong'), OOM)
        self.assertEqual(self.db.get('a'), '1')
        self.assertEqual(self.db.ttl('a'), 10)
        self.assertEqual(self.db.evicted_keys, 0)

    def test_utf8_accounting(self):
        self.db.set('한', '글')
        self.assertEqual(self.db.used_memory, 6)
        self.db.set('한', 'a')
        self.assertEqual(self.db.used_memory, 4)
        self.db.delete('한')
        self.assertEqual(self.db.used_memory, 0)

    def test_ttl_and_expired_global_commands(self):
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
        self.db.set('a', '1')
        for _ in range(1000):
            self.db.expire('a', 1000)
        self.db.purge_expired()
        self.assertLessEqual(self.db.expirations.size(), 64)
        self.now += 1000
        self.assertIsNone(self.db.get('a'))

    def test_errors(self):
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
