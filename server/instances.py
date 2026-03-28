import pickle
from models.Tries import CompressedTrie as Trie

try:
    trie = pickle.load(open("trie.pkl", "rb"))
except FileNotFoundError:
    trie = Trie()

import redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)