# Distributed Autocomplete System

> Not a CRUD app. A ground-up distributed autocomplete service built to understand how systems like Google Search suggestions actually work under the hood.

---

## What it does

Returns ranked autocomplete suggestions for a prefix in real time.

```
GET /autocomplete?prefix=mic
→ ["minecraft", "microsoft", "microphone", "microwave"]
```

Rankings update automatically based on what users actually search — type a word 50 times and watch it climb.

---

## Architecture

```
Client
  ↓
Nginx  (load balancer — round robins across 2 router instances)
  ↓
Router  (consistent hash ring + range partitioning — routes prefix to correct shard)
  ↓
Trie Shards x4  (in-memory compressed radix trie, each owns a letter range)
  ↓
Redis  (caching layer — 99% cache hit rate under load)

Search Events Pipeline:
Shard → Kafka (search-events) → Consumer (30s aggregation) → Kafka (trie-updates) → Trie Updater → Router → Correct Shard
```

---

## Key Design Decisions

**Sharding strategy — Range + Consistent Hashing hybrid**

Prefixes are first routed by first-character range (`a-f → shard1/shard4`, `g-m → shard2`, `n-z → shard3`). Within each range, consistent hashing distributes load across multiple nodes. Adding a new shard to a range only affects that range's keyspace — nothing else reshuffles.

**Why not pure consistent hashing?**

Autocomplete has natural prefix locality — a query for `"mic"` only ever needs the `m` subtrie. Range partitioning preserves this locality while consistent hashing handles load balancing within each range.

**Eventual consistency**

Trie frequency updates are asynchronous. A completed search logs to Kafka, gets aggregated over 30-second windows, then updates the trie. Rankings may lag by up to 30 seconds — acceptable for autocomplete. This keeps the read path fast and never blocked by writes.

**Fault tolerance**

Router runs a background health check every 5 seconds against all shards. Dead shard → removed from hash ring → traffic redistributes to remaining nodes automatically. Shard recovers → added back to ring. No manual intervention.

**Caching**

Redis sits in front of the trie. Repeated prefix queries hit Redis without touching the trie at all. Under load testing the cache hit rate climbed to 99% as hot prefixes warmed up.

---

## Data Structure

Compressed radix trie (not a basic trie). Instead of one node per character, whole string chunks are stored on edges — `"apple"` and `"apply"` share one edge labelled `"appl"` then split. Every node maintains a frequency dict of its top suggestions, updated on every insert along the full ancestor path.

```
Query: "mic"
→ traverse to "mic" node
→ return node.topk sorted by frequency
→ ["minecraft" (freq: 847), "microsoft" (freq: 623), "microphone" (freq: 412)]
```

---

## Tech Stack

| Component | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Data Structure | Compressed Radix Trie (custom) |
| Caching | Redis |
| Message Queue | Apache Kafka |
| Load Balancer | Nginx |
| Routing | Custom consistent hash ring |
| Observability | Prometheus + Grafana Cloud |
| Containerization | Docker + Docker Compose |
| Load Testing | Locust |

---

## Load Test Results

Tested with 100 concurrent users hitting randomized prefixes across all letter ranges.

| Metric | Result |
|---|---|
| Sustained RPS | ~80 req/sec across 4 shards |
| p50 latency | 600ms |
| p95 latency | 1100ms |
| Failure rate | 0% |
| Cache hit rate | 99% (after warmup) |

Latency is higher than production targets due to Docker overhead and all services sharing a single development machine. On separate hardware with dedicated CPU per service, p95 would drop significantly.

---

## Observability

Live Grafana dashboard tracking:
- Requests per second per shard
- p50 and p95 latency
- Cache hit/miss rate and ratio
- Per-shard traffic distribution
- Error rate

---

## Project Structure

```
distributed-autocomplete/
  server/                    ← FastAPI trie shard (runs as shard1/2/3/4)
    models/Tries.py          ← Compressed radix trie implementation
    routes/tries_crud.py     ← Autocomplete, search, update endpoints
    cache/main.py            ← Redis caching layer
    services/kafka_produce.py← Kafka producer for search events
  router/                    ← Consistent hash ring router
    main.py                  ← FastAPI router with health check loop
    ring.py                  ← HashRing, RangeRing, Router classes
  kafka/                     ← Search event consumer + aggregator
    consumer.py              ← Reads search-events, aggregates 30s windows
    producer.py              ← Publishes aggregated counts to trie-updates
  trie-updates/              ← Trie update service
    consumer.py              ← Reads trie-updates, calls router /update_frequency
  nginx/
    nginx.conf               ← Load balancer config
  locust/
    locustfile.py            ← Load test scenarios
  docker-compose.yml         ← Full system orchestration
  requirements.txt
```

---

## Running Locally

```bash
git clone https://github.com/DecayDestructor/distributed-autocomplete
cd distributed-autocomplete
docker compose up --build
```

All services start automatically in the correct order. System is ready when all containers show healthy.

Hit the system via Nginx:
```
GET http://localhost:8080/autocomplete?prefix=app
GET http://localhost:8080/tries/search?word=apple
```

**Fault tolerance demo:**
```bash
# Kill a shard
docker stop distributed-autocomplete-shard1-1

# Watch router detect and reroute (within 5-10 seconds)
docker compose logs -f router

# Bring it back
docker start distributed-autocomplete-shard1-1
```

**Load test:**
```bash
pip install locust
locust -f locust/locustfile.py --host=http://localhost:8080
# Open localhost:8089
```

---

## Known Limitations

- Pickle used for trie persistence — production would serialize the word-frequency dict to JSON and rebuild on startup, or use Kafka offset-based event replay
- Single Kafka broker — production runs a multi-broker cluster with rack awareness
- No multi-region deployment
- Shard state is not replicated — if a shard dies its in-memory frequency data is lost until rebuilt from pickle on restart

---

## What I learned

Started this because I wanted to build something that wasn't CRUD and was getting into system design. Ended up independently arriving at event sourcing, consistent hashing tradeoffs, the read/write path decoupling problem, and why eventual consistency is the right choice for non-critical ranked data. Built everything from scratch — the trie, the hash ring, the router, the pipeline.