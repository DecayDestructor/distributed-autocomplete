from fastapi import APIRouter, HTTPException
from models.Tries import CompressedTrie as Trie
import pickle
from instances import trie
from cache.main import get_suggestions, set_suggestions
from prometheus_client import Counter

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

log_number= 0
@router.get("/create-log")
async def create_log():
    from services.kafka_produce import log_search_event
    global log_number
    log_number += 1

    log_search_event("example search query"+str(log_number))
    return {"message": "Log created for example search query"+str(log_number)}