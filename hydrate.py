import httpx
import asyncio

async def hyd():
    try:
        with open("server/google-10000-english-usa.txt", "r") as f:
            w = f.read().splitlines()
    except FileNotFoundError:
        print("err file not fnd")
        return

    print(f"ld {len(w)} wds")
    
    async def sw(c, wd):
        try:
            await c.put(f"http://localhost:8080/tries/update_frequency", params={"query": wd, "frequency": 10})
        except httpx.RequestError:
            pass

    async with httpx.AsyncClient() as c:
        bs = 100
        for i in range(0, len(w), bs):
            b = w[i:i+bs]
            await asyncio.gather(*(sw(c, wd) for wd in b))
            print(f"prc {i + len(b)}/{len(w)}")

    print("done")

if __name__ == "__main__":
    asyncio.run(hyd())
