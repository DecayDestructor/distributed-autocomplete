import os

from dns.resolver import query
from fastapi import FastAPI
from hashlib import sha256
from ring import HashRing, RangeRing, Router
import bisect
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(health_check_loop())
    yield
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello World"}

prefix_router = Router()

import httpx
import redis

SHARD_URLS = {}
consecutive_failures = {}

async def sync_shards_from_redis():
    redis_host = os.getenv("REDIS_HOST", "redis")
    try:
        r = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
        shards = r.hgetall("shards")
        for shard_name, shard_range in shards.items():
            if shard_name not in SHARD_URLS:
                SHARD_URLS[shard_name] = f"http://{shard_name}:8000"
                consecutive_failures[shard_name] = 0
                start_char, end_char = shard_range.split("-")
                rng = None
                for existing_rng in prefix_router.ranges:
                    if existing_rng.start == start_char and existing_rng.end == end_char:
                        rng = existing_rng
                        break
                if not rng:
                    rng = RangeRing(start_char, end_char)
                    prefix_router.add_range(rng)
                rng.add_node(shard_name)
                prefix_router.register_shard(shard_name, rng)
                print(f"add shd {shard_name} rng {shard_range}")
    except Exception:
        pass

@app.get("/autocomplete")
async def autocomplete(prefix: str):
    shard = prefix_router.get_node(prefix)
    if not shard:
        return {"prefix": prefix, "suggestions": []}
    
    shard_url = SHARD_URLS.get(shard)
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{shard_url}/tries/autocomplete", params={"prefix": prefix})
        return response.json()

@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.put("/tries/update_frequency")
async def update_frequency(query: str, frequency: int):
    shard = prefix_router.get_node(query)
    if not shard:
        return {"query": query, "found": False}

    shard_url = SHARD_URLS.get(shard)
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{shard_url}/tries/update_freq", params={"query": query, "freq": frequency})
        return response.json()
    

@app.get("/tries/search")
async def search(word: str):
    shard = prefix_router.get_node(word)
    if not shard:
        return {"word": word, "found": False}

    shard_url = SHARD_URLS.get(shard)
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{shard_url}/tries/search", params={"word": word})
        return response.json()
    


from contextlib import asynccontextmanager
import asyncio

dead_shards = set()  # ← outside the loop

async def health_check_loop():
    while True:
        await sync_shards_from_redis()
        await asyncio.sleep(5)
        for shard_name, shard_url in list(SHARD_URLS.items()):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{shard_url}/health", timeout=2.0)
                    if response.status_code == 200:
                        consecutive_failures[shard_name] = 0
                        if shard_name in dead_shards:
                            dead_shards.remove(shard_name)
                            prefix_router.get_range_by_shard(shard_name).add_node(shard_name)
                            print(f"Shard {shard_name} recovered. Added back to router.")
                    else:
                        consecutive_failures[shard_name] = consecutive_failures.get(shard_name, 0) + 1
            except Exception:
                consecutive_failures[shard_name] = consecutive_failures.get(shard_name, 0) + 1
            if consecutive_failures.get(shard_name, 0) >= 3 and shard_name not in dead_shards:
                dead_shards.add(shard_name)
                prefix_router.get_range_by_shard(shard_name).remove_node(shard_name)
                print(f"Shard {shard_name} is down. Removed from router.")


