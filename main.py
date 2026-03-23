from fastapi import FastAPI
from models.Tries import CompressedTrie as Trie
from routes.tries_crud import router as tries_router

app = FastAPI()

app.include_router(tries_router, prefix="/tries", tags=["tries"])


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}
