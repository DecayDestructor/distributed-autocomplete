import hashlib
import bisect

class HashRing:
    def __init__(self, virtual_nodes: int = 3):
        self.virtual_nodes = virtual_nodes
        self.hash_ring = {}
        self.sorted_keys = []

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, shard_name: str):
        for i in range(self.virtual_nodes):
            position = self._hash(f"{shard_name}-v{i}")
            self.hash_ring[position] = shard_name
            bisect.insort(self.sorted_keys, position)

    def remove_node(self, shard_name: str):
        for i in range(self.virtual_nodes):
            position = self._hash(f"{shard_name}-v{i}")
            if position in self.hash_ring:
                del self.hash_ring[position]
                self.sorted_keys.remove(position)

    def get_node(self, key: str) -> str:
        if not self.sorted_keys:
            return None
        hash_value = self._hash(key)
        index = bisect.bisect_left(self.sorted_keys, hash_value)
        if index == len(self.sorted_keys):
            index = 0
        return self.hash_ring[self.sorted_keys[index]]


class RangeRing:
    def __init__(self, start: str, end: str):
        self.start = start
        self.end = end
        self.hash_ring = HashRing()

    def in_range(self, key: str) -> bool:
        first_char = key[0].lower()
        return self.start <= first_char <= self.end

    def add_node(self, shard_name: str):
        self.hash_ring.add_node(shard_name)

    def remove_node(self, shard_name: str):
        self.hash_ring.remove_node(shard_name)

    def get_node(self, key: str) -> str:
        if not self.in_range(key):
            return None
        return self.hash_ring.get_node(key)


class Router:
    def __init__(self):
        self.ranges = []

    def add_range(self, range_ring: RangeRing):
        self.ranges.append(range_ring)

    def get_node(self, key: str) -> str:
        for r in self.ranges:
            if r.in_range(key):
                return r.get_node(key)
        return None
    

router = Router()

range1 = RangeRing('a', 'f')
range1.add_node('shard1')
router.add_range(range1)

range2 = RangeRing('g', 'm')
range2.add_node('shard2')
router.add_range(range2)

range3 = RangeRing('n', 'z')
range3.add_node('shard3')
router.add_range(range3)