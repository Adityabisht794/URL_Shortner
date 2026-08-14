# URL Shortener — Level 1: Single Server, Single Database

## What this is

The simplest working version: one FastAPI process, one SQLite database file,
no cache, no queue, nothing distributed. It does exactly three things —

- `POST /shorten` — store a long URL, return a short code
- `GET /{short_code}` — redirect to the original URL (and log a visit)
- `GET /api/stats/{short_code}` — see how many times a code was visited

## How it works

1. A new URL is inserted as a row to get an auto-increment integer `id`
   from the DB.
2. That `id` is base62-encoded (`0-9a-zA-Z`) into a short string like `1`,
   `a`, `1B` — this is the short code.
3. The row is updated with that code.
4. Reads just look the code up, decode isn't even needed since we index on
   the string code directly, and redirect.

This is **the textbook naive design** — correct, easy to reason about, and
exactly the design every URL-shortener system-design writeup starts from
before scaling it up.

## Run it

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run the tests I ran

```bash
curl -X POST http://localhost:8000/shorten -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
curl -i http://localhost:8000/1
curl http://localhost:8000/api/stats/1
```

---

## Limitations — and what Level 2 has to fix

### 1. Single point of failure — one process, one DB file
Everything lives in one SQLite file on one machine's disk. If that process
or disk dies, the whole service is down, and every short link ever created
stops resolving.
→ **Level 2 fix**: replicated/managed DB (e.g. Postgres with replicas), and
more than one app server behind a load balancer, so no single machine
losing power takes down the product.

### 2. ID generation doesn't scale horizontally
The short code comes from an **auto-increment column in one database**.
That's fine with one writer. The moment you add a second app server (to
survive #1 or handle more load), you can't have two independent SQLite/DB
instances both handing out auto-increment ids — they'll collide (two
different URLs both becoming `id=5`).
→ **Level 2 fix**: a dedicated ID-generation strategy that works across
multiple nodes without a shared counter — e.g. pre-allocated ID ranges per
server, Twitter Snowflake-style ids (timestamp + machine-id + sequence), or
random-then-check-uniqueness codes. This single design choice is *the*
reason "add a second server" isn't a one-line change.

### 3. Every redirect is also a write (`visit_count`)
`GET /{short_code}` — the hottest path in the whole system, by far — does a
DB **write** on every single hit, to increment the counter. Read-heavy
traffic (redirects) is bottlenecked by the DB's write throughput.
→ **Level 2 fix**: caching (Redis) in front of the DB for the read path,
and moving analytics off the hot path — e.g. push visit events to a queue
and increment counters asynchronously instead of inline with the redirect.

### 4. No caching layer at all
Every single redirect — even for the same 5 viral links getting 90% of the
traffic — re-queries the database. There's no way to absorb a traffic spike
without the DB feeling all of it directly.
→ **Level 2 fix**: Redis cache for `short_code -> original_url`, checked
before hitting the DB. Turns "DB has to handle peak QPS" into "DB handles
cache misses only."

### 5. One database = one scaling ceiling
All rows, forever, live in one table on one database instance. As the
dataset and QPS grow, you eventually hit that database's ceiling — there's
nowhere to route "the next chunk of data" to.
→ **Level 2 fix**: sharding — split rows across multiple DB instances (e.g.
by hashing the short code or by id range), so no single database instance
has to hold or serve the entire dataset.

### 6. No load balancer / can't add capacity
There's exactly one app process listening on one port. To handle more
traffic, the *only* lever is "make this one machine bigger" (vertical
scaling), which has a ceiling and a single point of failure baked in.
→ **Level 2 fix**: run N stateless app instances behind a load balancer.
This is only possible *after* fixing #2 (ID generation) and #3 (moving
state like visit counts out of the request path), which is why those come
first conceptually even though "add a load balancer" sounds like the
obvious first move.

### 7. No rate limiting / abuse protection
Nothing stops one client from calling `/shorten` in a tight loop and
filling the database, or scraping every code sequentially since ids are
sequential and guessable.
→ **Level 2 fix**: rate limiting (e.g. token bucket in Redis) and
non-sequential/harder-to-guess codes (ties back into #2's ID strategy).

### 8. No observability
If something's slow or failing, there is currently no way to know without
reading server logs by hand — no metrics, no request tracing, no alerting.
→ **Level 2 fix**: structured logging + metrics (request latency, cache hit
rate, DB load) exported somewhere queryable, ideally per-shard/per-instance.

---

## The throughline

Notice the dependency order above isn't arbitrary:
**ID generation (#2)** has to be solved before you can honestly add more
app servers (#6), and **moving writes off the read path (#3)** has to
happen before caching (#4) actually helps, because right now every "read"
is secretly a write too. Level 2 isn't "add five features" — it's mostly
downstream of fixing those two coupling problems.
