import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from models.Tries import CompressedTrie

def test_insert_and_search():
    trie = CompressedTrie()
    trie.insert("apple")
    assert trie.search("apple") is True
    assert trie.search("app") is False
    assert trie.search("apples") is False

def test_autocomplete():
    trie = CompressedTrie(k=3)
    trie.insert("apple", freq=10)
    trie.insert("application", freq=5)
    trie.insert("apply", freq=15)
    trie.insert("apricot", freq=2)
    results = trie.autocomplete("app")
    assert len(results) == 3
    assert results[0] == (15, "apply")
    assert results[1] == (10, "apple")
    assert results[2] == (5, "application")

def test_delete():
    trie = CompressedTrie()
    trie.insert("apple")
    trie.insert("application")
    assert trie.search("apple") is True
    assert trie.delete("apple") is True
    assert trie.search("apple") is False
    assert trie.search("application") is True

def test_update_frequency():
    trie = CompressedTrie(k=3)
    trie.insert("apple", freq=1)
    results = trie.autocomplete("app")
    assert results[0] == (1, "apple")
    trie.update_frequency("apple", 20)
    results = trie.autocomplete("app")
    assert results[0] == (20, "apple")
    assert trie.get_frequency("apple") == 20

def test_get_frequency():
    trie = CompressedTrie()
    trie.insert("apple", freq=5)
    assert trie.get_frequency("apple") == 5
    assert trie.get_frequency("app") == 0

def test_edge_cases():
    trie = CompressedTrie()
    trie.insert("a", 10)
    trie.insert("ab", 20)
    assert trie.search("a") is True
    assert trie.search("ab") is True
    assert trie.search("b") is False
    assert trie.get_frequency("a") == 10
    assert trie.get_frequency("ab") == 20
    trie.delete("a")
    assert trie.search("a") is False
    assert trie.search("ab") is True
