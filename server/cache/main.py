from instances import r
if __name__ == "__main__":
    r.set("test", "works")
    print(r.get("test"))


def get_suggestions(prefix: str):

    suggestions = r.zrevrange(prefix, 0, -1, withscores=True)
    print(f"Retrieved suggestions from cache for prefix '{prefix}': {suggestions}")
    return suggestions


def set_suggestions(prefix: str, suggestions: list[(int,str)]):
    for suggestion in suggestions:
        r.zadd(prefix, {suggestion[1]: suggestion[0]},)
    r.expire(prefix, 300)  
    return True