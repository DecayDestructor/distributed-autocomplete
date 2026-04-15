from fastapi import FastAPI
import os
import redis
from models.Tries import CompressedTrie as Trie
from routes.tries_crud import router as tries_router
from prometheus_fastapi_instrumentator import Instrumentator
app = FastAPI()
Instrumentator().instrument(app).expose(app)
app.include_router(tries_router, prefix="/tries", tags=["tries"])

@app.on_event("startup")
async def startup_event():
    shard_name = os.getenv("SHARD_NAME")
    shard_range = os.getenv("SHARD_RANGE")
    redis_host = os.getenv("REDIS_HOST")
    if shard_name and shard_range and redis_host:
        r = redis.Redis(host=redis_host, port=6379, db=0)
        r.hset("shards", shard_name, shard_range)
        print(f"reg shard {shard_name} rng {shard_range}")

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}