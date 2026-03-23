from fastapi import APIRouter, HTTPException
from models.Tries import CompressedTrie as Trie
import pickle

router = APIRouter()
try:
    trie = pickle.load(open("trie.pkl", "rb"))
except FileNotFoundError:
    trie = Trie()


@router.get("/autocomplete")
async def get_autocomplete(prefix: str):
    suggestions = trie.autocomplete(prefix)
    return {"prefix": prefix, "suggestions": suggestions}


@router.get("/populate")
async def populate_trie():
    f = open("google-10000-english-usa.txt", "r")
    for line in f:
        trie.insert(word=line.strip(), freq=1)
    f.close()
    pickle.dump(trie, open("trie.pkl", "wb"))
    return {"message": "Trie populated with words from google-10000-english-usa.txt"}
