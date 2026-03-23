import heapq
from collections import defaultdict


class TrieNode:
    def __init__(self):
        self.children = {}  # char/prefix -> TrieNode
        self.edge_label = ""  # the compressed edge string leading to this node
        self.is_end = False  # marks a complete word
        self.frequency = 0  # how often this word was inserted
        self.top_k = []  # min-heap of (-freq, word) for top-k


class CompressedTrie:
    def __init__(self, k=6):
        self.root = TrieNode()
        self.k = k

    # ── insertion ────────────────────────────────────────────────

    def insert(self, word: str, freq: int = 1):
        self._insert(self.root, word, word, freq)

    def _insert(self, node: TrieNode, remaining: str, full_word: str, freq: int):
        # update this node's top-k with the incoming word
        self._update_topk(node, full_word, freq)

        if not remaining:
            node.is_end = True
            node.frequency += freq
            return

        first_char = remaining[0]

        # no child starts with this character — create a new leaf
        if first_char not in node.children:
            child = TrieNode()
            child.edge_label = remaining
            child.is_end = True
            child.frequency = freq
            self._update_topk(child, full_word, freq)
            node.children[first_char] = child
            return

        child = node.children[first_char]
        label = child.edge_label
        common = self._common_prefix(remaining, label)

        # the edge label is fully consumed — keep descending
        if common == label:
            self._insert(child, remaining[len(common) :], full_word, freq)
            return

        # partial match — split the edge
        split = TrieNode()
        split.edge_label = common

        # existing child becomes a deeper node with the leftover label
        child.edge_label = label[len(common) :]
        split.children[child.edge_label[0]] = child

        # new leaf for the word we're inserting
        leftover = remaining[len(common) :]
        if leftover:
            new_leaf = TrieNode()
            new_leaf.edge_label = leftover
            new_leaf.is_end = True
            new_leaf.frequency = freq
            self._update_topk(new_leaf, full_word, freq)
            split.children[leftover[0]] = new_leaf
        else:
            split.is_end = True
            split.frequency = freq

        self._update_topk(split, full_word, freq)
        # bubble up existing words under the child into split's top-k
        for _, w in child.top_k:
            self._update_topk(split, w, self._word_freq(child, w))

        node.children[first_char] = split

    # ── search ───────────────────────────────────────────────────

    def search(self, word: str) -> bool:
        node, _ = self._find_node(word)
        return node is not None and node.is_end

    def autocomplete(self, prefix: str) -> list[str]:
        """Return top-k completions for a given prefix."""
        node, _ = self._find_node(prefix)
        if node is None:
            return []
        return sorted(node.top_k, key=lambda x: -x[0])  # highest freq first

    def _find_node(self, text: str):
        node = self.root
        while text:
            first_char = text[0]
            if first_char not in node.children:
                return None, None
            child = node.children[first_char]
            label = child.edge_label
            if text.startswith(label):
                text = text[len(label) :]
                node = child
            elif label.startswith(text):
                # prefix ends in the middle of an edge — still valid for autocomplete
                return child, text
            else:
                return None, None
        return node, ""

    def delete(self, word: str) -> bool:
        """
        Remove a word from the trie. Returns True if deleted, False if not found.
        Cleans up top-k heaps along the path and merges single-child nodes.
        """
        # first verify the word actually exists
        if not self.search(word):
            return False

        self._delete(self.root, word, word)
        return True

    def _delete(self, node: TrieNode, remaining: str, full_word: str):
        # remove this word from the current node's top-k
        self._remove_from_topk(node, full_word)

        if not remaining:
            # we've reached the terminal node — unmark it
            node.is_end = False
            node.frequency = 0
            return

        first_char = remaining[0]
        child = node.children[first_char]
        label = child.edge_label

        if remaining.startswith(label):
            self._delete(child, remaining[len(label) :], full_word)
        else:
            # prefix ends mid-edge (shouldn't happen if search passed, but guard it)
            self._delete(child, "", full_word)

        # ── structural cleanup after recursion unwinds ──────────────

        # case 1: child is now a dead leaf (no word, no children) — prune it
        if not child.is_end and not child.children:
            del node.children[first_char]
            return

        # case 2: child has exactly one grandchild and isn't a word — merge edges
        if not child.is_end and len(child.children) == 1:
            grandchild_key = next(iter(child.children))
            grandchild = child.children[grandchild_key]
            # collapse: parent absorbs child's edge + grandchild's edge
            grandchild.edge_label = child.edge_label + grandchild.edge_label
            node.children[first_char] = grandchild

    def _remove_from_topk(self, node: TrieNode, word: str):
        """Drop a word from a node's top-k heap entirely."""
        node.top_k = [(f, w) for f, w in node.top_k if w != word]

    # ── helpers ──────────────────────────────────────────────────

    def _update_topk(self, node: TrieNode, word: str, freq: int):
        """Maintain a min-heap of size k: (freq, word) pairs."""
        # remove stale entry for the same word if it exists
        node.top_k = [(f, w) for f, w in node.top_k if w != word]
        heapq.heappush(node.top_k, (freq, word))
        if len(node.top_k) > self.k:
            heapq.heappop(node.top_k)  # evict the lowest-frequency word

    def _word_freq(self, node: TrieNode, word: str) -> int:
        for freq, w in node.top_k:
            if w == word:
                return freq
        return 0

    @staticmethod
    def _common_prefix(a: str, b: str) -> str:
        i = 0
        while i < len(a) and i < len(b) and a[i] == b[i]:
            i += 1
        return a[:i]
