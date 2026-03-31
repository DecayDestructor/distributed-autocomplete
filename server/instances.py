import pickle
from models.Tries import CompressedTrie as Trie

try:
    trie = pickle.load(open("trie.pkl", "rb"))
except FileNotFoundError:
    trie = Trie()

import redis
import os
r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"))