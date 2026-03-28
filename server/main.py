from fastapi import FastAPI
from models.Tries import CompressedTrie as Trie
from routes.tries_crud import router as tries_router
from prometheus_fastapi_instrumentator import Instrumentator
app = FastAPI()
Instrumentator().instrument(app).expose(app)
app.include_router(tries_router, prefix="/tries", tags=["tries"])


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}
