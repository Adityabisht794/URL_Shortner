# 🔗 URL Shortener — Backend Engineering Project

A progressively built URL Shortener designed to demonstrate backend engineering concepts from a simple in-memory implementation to a persistent PostgreSQL-backed service with deduplication, indexing, analytics, and redirect handling.

The project is intentionally developed in levels to show how a backend system evolves as requirements and scale increase.

---

## 🏗️ Architecture

### Level 1

```text
Client / Swagger UI
        ↓
    FastAPI API
        ↓
  URL Shortening Logic
        ↓
   SQLite Database
```

### Level 2

```text
Client / Swagger UI
        ↓
     FastAPI
        ↓
  SQLAlchemy ORM
        ↓
   PostgreSQL
        ↓
    url_mappings
```

---

# 🚀 Level 1 — Basic URL Shortener

Level 1 focuses on building the core functionality of a URL shortening service.

### Features

* REST API built with **FastAPI**
* Swagger UI for API testing
* Accepts long URLs through an API request
* Generates a compact short code
* Stores URL mappings
* Redirects users from the short URL to the original URL
* Basic URL validation
* SQLite-based persistence
* Basic click tracking

### Example

Request:

```http
POST /api/shorten
```

```json
{
  "long_url": "https://www.example.com/a/very/long/url"
}
```

Response:

```json
{
  "short_code": "1",
  "short_url": "http://short.ly/1",
  "long_url": "https://www.example.com/a/very/long/url"
}
```

Visiting:

```http
GET /1
```

redirects the user to the original URL.

### Level 1 Concepts

* HTTP methods
* REST APIs
* Request/response models
* URL validation
* HTTP redirects
* Database persistence
* CRUD operations
* API documentation with Swagger/OpenAPI
* Basic backend project structure

---

# ⚡ Level 2 — PostgreSQL, Indexing & Deduplication

Level 2 upgrades the system from a basic application into a more realistic backend service.

The SQLite storage layer is replaced with **PostgreSQL**, accessed through **SQLAlchemy**.

### Major Improvements

#### 1. PostgreSQL

Instead of relying on a local SQLite file, the application uses PostgreSQL running inside Docker.

```text
FastAPI
   ↓
SQLAlchemy
   ↓
PostgreSQL
```

PostgreSQL provides:

* Client/server database architecture
* Concurrent connections
* Server-side constraints
* Better scalability than a single SQLite file
* Production-oriented persistence

---

#### 2. Dockerized Database

PostgreSQL runs using Docker Compose.

```bash
docker compose up -d
```

Database configuration:

```text
Host: localhost
Port: 5432
Database: urlshortener
User: urlshort
```

This makes the database environment reproducible without requiring PostgreSQL to be installed directly on the host machine.

---

#### 3. SQLAlchemy ORM

The application uses SQLAlchemy to interact with PostgreSQL.

The main model is:

```text
URLMapping
```

with fields such as:

```text
id
short_code
long_url
created_at
click_count
```

The application does not need to manually construct SQL for normal CRUD operations.

---

#### 4. Short Code Generation

The database generates an auto-incrementing ID.

The ID is then converted into a compact Base62 representation.

```text
Database ID
     ↓
Base62 Encoder
     ↓
Short Code
```

Base62 uses:

```text
0-9
a-z
A-Z
```

This allows numeric IDs to be represented using fewer characters.

---

#### 5. Database Indexing

The Level 2 implementation uses indexes on frequently queried fields.

### `short_code`

Used by the redirect endpoint:

```http
GET /{short_code}
```

Instead of scanning every database row, PostgreSQL can use the index to locate the mapping efficiently.

### `long_url`

Used when shortening a URL.

The application first checks whether the URL already exists.

This makes repeated requests for the same URL efficient.

---

#### 6. URL Deduplication

Level 2 prevents the same long URL from generating multiple short URLs.

Example:

```text
Request 1
https://example.com
        ↓
short_code = 1

Request 2
https://example.com
        ↓
existing mapping found
        ↓
short_code = 1

Request 3
https://example.com
        ↓
existing mapping found
        ↓
short_code = 1
```

Instead of:

```text
1 → example.com
2 → example.com
3 → example.com
```

the database contains a single mapping.

The `long_url` unique constraint also protects against duplicate inserts caused by concurrent requests.

---

# 📊 Analytics

Level 2 also introduces basic URL statistics.

Endpoint:

```http
GET /api/stats/{short_code}
```

Example response:

```json
{
  "short_code": "1",
  "long_url": "https://www.example.com",
  "click_count": 5,
  "created_at": "2026-08-19T..."
}
```

Every successful redirect increments the click counter.

```text
GET /1
   ↓
Find mapping
   ↓
click_count += 1
   ↓
307 Redirect
```

---

# 🔀 Redirect Handling

The redirect endpoint:

```http
GET /{short_code}
```

looks up the short code and returns:

```http
307 Temporary Redirect
```

with the original URL in the `Location` header.

This allows the browser/client to automatically navigate to the destination.

---

# 🩺 Health Check

The service exposes:

```http
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "level": 2
}
```

This provides a simple liveness check for the API.

---

# 📁 Project Structure

```text
url_shortener/
│
├── main.py
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
├── LIMITATIONS.md
│
└── app/
    ├── __init__.py
    ├── database.py
    ├── encoder.py
    ├── models.py
    ├── schemas.py
    └── crud.py
```

---

# 🛠️ Tech Stack

| Component          | Technology        |
| ------------------ | ----------------- |
| Language           | Python            |
| API Framework      | FastAPI           |
| API Documentation  | Swagger / OpenAPI |
| ORM                | SQLAlchemy        |
| Database — Level 1 | SQLite            |
| Database — Level 2 | PostgreSQL        |
| Database Container | Docker            |
| Short Code         | Base62            |
| Validation         | Pydantic          |
| Server             | Uvicorn           |

---

# ▶️ Running the Project

## 1. Start PostgreSQL

```bash
docker compose up -d
```

Check:

```bash
docker ps
```

The PostgreSQL container should report a healthy status.

---

## 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Start FastAPI

```bash
python -m uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

# 🧪 API Endpoints

| Method | Endpoint                  | Purpose                     |
| ------ | ------------------------- | --------------------------- |
| POST   | `/api/shorten`            | Create/retrieve a short URL |
| GET    | `/{short_code}`           | Redirect to original URL    |
| GET    | `/api/stats/{short_code}` | View URL statistics         |
| GET    | `/api/health`             | Health check                |

---

# 📈 Level Progression

```text
LEVEL 1
───────
FastAPI
   +
SQLite
   +
Basic URL shortening
   +
Redirects
   +
CRUD
        │
        ▼
LEVEL 2
───────
FastAPI
   +
SQLAlchemy
   +
PostgreSQL
   +
Docker
   +
Base62 encoding
   +
Database indexing
   +
URL deduplication
   +
Concurrency-safe uniqueness
   +
Click analytics
        │
        ▼
LEVEL 3
───────
Caching
Redis
Rate limiting
Horizontal scaling
Load balancing
Distributed ID generation
Observability
        │
        ▼
LEVEL 4
───────
Distributed architecture
Message queues
Analytics pipeline
High availability
Database replication
Sharding
CDN
Fault tolerance
```

---

# ⚠️ Current Level 2 Limitations

The current implementation intentionally does **not** attempt to solve every large-scale URL shortener problem.

Current limitations include:

* Single FastAPI application process
* Single PostgreSQL instance
* No Redis caching
* No distributed ID generation
* No rate limiting
* No horizontal scaling
* No load balancer
* Redirects perform synchronous database operations
* Click analytics are stored directly in the primary database
* No database replication
* No sharding
* No advanced observability

These limitations are intentional and form the basis for future levels.

---

# 🎯 Learning Objective

This project is not only about creating short URLs.

It demonstrates the progression from:

```text
"Build an API"
```

to:

```text
"Build a backend service that considers
persistence, indexing, concurrency,
deduplication and scalability."
```

The project will continue evolving through multiple levels as increasingly realistic backend and system-design requirements are introduced.

---

## 👨‍💻 Author

**Aditya Bisht**

Backend Engineering / System Design Learning Project
