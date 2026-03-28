from fastapi import APIRouter, HTTPException
from models.Tries import CompressedTrie as Trie
import pickle
from instances import trie
from cache.main import get_suggestions, set_suggestions
from prometheus_client import Counter
from services.kafka_produce import log_search_event

autocomplete_requests = Counter("autocomplete_requests", "Total autocomplete requests")
cache_hits = Counter("cache_hits", "Total cache hits")
cache_misses = Counter("cache_misses", "Total cache misses")

router = APIRouter()


@router.get("/autocomplete")
async def get_autocomplete(prefix: str):
    autocomplete_requests.inc()
    suggestions = get_suggestions(prefix)
    print(f"Suggestions from cache for prefix '{prefix}': {suggestions}")
    if not suggestions:
        # print(f"Cache miss for prefix: {prefix}")
        cache_misses.inc()
        suggestions = trie.autocomplete(prefix)
        # print(f"Suggestions from trie for prefix '{prefix}': {suggestions}")
        set_suggestions(prefix, suggestions)
    else:
        cache_hits.inc()
        print(f"Cache hit for prefix: {prefix}")
    return {"prefix": prefix, "suggestions": suggestions}


@router.get("/populate")
async def populate_trie():
    f = open("google-10000-english-usa.txt", "r")
    for line in f:
        trie.insert(word=line.strip(), freq=1)
    f.close()
    pickle.dump(trie, open("trie.pkl", "wb"))
    return {"message": "Trie populated with words from google-10000-english-usa.txt"}


@router.get("/search")
async def search_word(word: str): # this endpoint searches for a word, and logs into kafka, if the word isnt found, it will be inserted into the trie with frequency 1, if it is found, its frequency will be updated by 1
    found = trie.search(word)
    log_search_event(word)
    if found:
        freq = trie.get_frequency(word)
        print(f"Word '{word}' found in trie with frequency {freq}, kafka has logged it")
        return {"message": f"Word '{word}' found in trie with frequency {freq}, kafka has logged it"}
    else:
        print(f"Word '{word}' not found in trie, kafka has logged it")
        return {"message": f"Word '{word}' not found in trie, kafka has logged it"}

@router.put("/update-freq")
async def update_freq(query: str, freq: int):
    found = trie.search(query)
    if found:
        trie.update_freq(query, trie.get_frequency(query) + freq)
        pickle.dump(trie, open("trie.pkl", "wb"))
        print(f"Updated frequency of word '{query}' to {freq}")
        return {"message": f"Updated frequency of word '{query}' to {freq}"}
    else:
        trie.insert(query, freq=freq)
        pickle.dump(trie, open("trie.pkl", "wb"))
        print(f"Inserted word '{query}' with frequency {freq}")
        return {"message": f"Inserted word '{query}' with frequency {freq}"}
    