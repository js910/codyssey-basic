"""상수 시간 삽입, 삭제, 이동을 지원하는 이중 연결 리스트."""
class Node:
    def __init__(self, data):
        """데이터와 앞뒤 노드 참조, 소속 리스트 정보를 초기화한다."""
        self.data = data
        self.prev = None
        self.next = None
        self.owner = None

class DoublyLinkedList:
    def __init__(self):
        """첫 노드와 마지막 노드가 없는 빈 연결 리스트를 만든다."""
        self.head = self.tail = None
        self.length = 0

    def insert_front(self, data):
        """새 노드를 리스트 맨 앞에 넣고 그 노드를 반환한다."""
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
        """새 노드를 리스트 맨 뒤에 넣고 그 노드를 반환한다."""
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
        """지정한 노드의 앞뒤 연결을 이어 노드를 제거하고 데이터를 반환한다."""
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
        """맨 앞 노드를 제거하고 데이터를 반환하며 비어 있으면 None을 반환한다."""
        return None if self.head is None else self.remove_node(self.head)

    def remove_back(self):
        """맨 뒤 노드를 제거하고 데이터를 반환하며 비어 있으면 None을 반환한다."""
        return None if self.tail is None else self.remove_node(self.tail)

    def move_to_front(self, node):
        """기존 노드를 새로 만들지 않고 리스트 맨 앞으로 옮긴다."""
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
