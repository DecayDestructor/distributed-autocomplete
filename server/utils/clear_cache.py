from instances import r

def clear_cache():
    r.flushdb()
    print("Cache cleared successfully.")

if __name__ == "__main__":
    clear_cache()