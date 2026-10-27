"""상수 시간 삽입, 삭제, 이동을 지원하는 이중 연결 리스트."""
class Node:
    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None
        self.owner = None

class DoublyLinkedList:
    def __init__(self):
        self.head = self.tail = None
        self.length = 0

    def insert_front(self, data):
        node = Node(data)
        node.owner = self
        node.next = self.head
        if self.head is not None:
            self.head.prev = node
        else:
            self.tail = node
        self.head = node
        self.length += 1
        return node

    def insert_back(self, data):
        node = Node(data)
        node.owner = self
        node.prev = self.tail
        if self.tail is not None:
            self.tail.next = node
        else:
            self.head = node
        self.tail = node
        self.length += 1
        return node

    def remove_node(self, node):
        if node.owner is not self:
            raise ValueError('Node does not belong to this list')
        if node.prev is None:
            self.head = node.next
        else:
            node.prev.next = node.next
        if node.next is None:
            self.tail = node.prev
        else:
            node.next.prev = node.prev
        node.prev = node.next = node.owner = None
        self.length -= 1
        return node.data

    def remove_front(self):
        return None if self.head is None else self.remove_node(self.head)

    def remove_back(self):
        return None if self.tail is None else self.remove_node(self.tail)

    def move_to_front(self, node):
        if node.owner is not self:
            raise ValueError('Node does not belong to this list')
        if node is self.head:
            return
        self.remove_node(node)
        node.owner = self
        node.next = self.head
        if self.head is not None:
            self.head.prev = node
        else:
            self.tail = node
        self.head = node
        self.length += 1
