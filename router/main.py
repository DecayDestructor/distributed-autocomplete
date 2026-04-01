import os

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

range1 = RangeRing('a', 'f')
range1.add_node('shard1')
range1.add_node("shard4") 
prefix_router.add_range(range1)

range2 = RangeRing('g', 'm')
range2.add_node('shard2')
prefix_router.add_range(range2)

range3 = RangeRing('n', 'z')
range3.add_node('shard3')
prefix_router.add_range(range3)

import httpx

SHARD_URLS = {
    "shard1": os.getenv('SHARD1_URL', 'http://shard1:8000'),
    "shard2": os.getenv('SHARD2_URL', 'http://shard2:8000'),
    "shard3": os.getenv('SHARD3_URL', 'http://shard3:8000'),
    "shard4": os.getenv('SHARD4_URL', 'http://shard4:8000')
}

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
async def update_frequency(word: str, frequency: int):
    shard = prefix_router.get_node(word)
    if not shard:
        return {"word": word, "found": False}

    shard_url = SHARD_URLS.get(shard)
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{shard_url}/tries/update_frequency", params={"query": word, "freq": frequency})
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
        await asyncio.sleep(5)
        for shard_name, shard_url in SHARD_URLS.items():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{shard_url}/health", timeout=2.0)
                    await asyncio.sleep(2) 
                    if response.status_code == 200:
                        if shard_name in dead_shards:
                            dead_shards.remove(shard_name)
                            prefix_router.get_range_by_shard(shard_name).add_node(shard_name)
                            print(f"Shard {shard_name} recovered. Added back to router.")
                    else:
                        if shard_name not in dead_shards:
                            dead_shards.add(shard_name)
                            prefix_router.get_range_by_shard(shard_name).remove_node(shard_name)
                            print(f"Shard {shard_name} is down. Removed from router.")
            except Exception:
                if shard_name not in dead_shards:
                    dead_shards.add(shard_name)
                    prefix_router.get_range_by_shard(shard_name).remove_node(shard_name)
                    print(f"Shard {shard_name} is down. Removed from router.")


