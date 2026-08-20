from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "level": 2}


def test_shorten_url():
    response = client.post("/api/shorten", json={"long_url": "https://example.com"})

    assert response.status_code == 200

    data = response.json()

    assert "short_code" in data
    assert "short_url" in data
    assert data["long_url"] == "https://example.com/"


def test_url_deduplication():
    url = "https://dedup-test.example.com"

    response1 = client.post("/api/shorten", json={"long_url": url})

    response2 = client.post("/api/shorten", json={"long_url": url})

    assert response1.status_code == 200
    assert response2.status_code == 200

    assert response1.json()["short_code"] == response2.json()["short_code"]


def test_stats():
    response = client.post(
        "/api/shorten", json={"long_url": "https://stats-test.example.com"}
    )

    short_code = response.json()["short_code"]

    stats_response = client.get(f"/api/stats/{short_code}")

    assert stats_response.status_code == 200

    data = stats_response.json()

    assert data["short_code"] == short_code
    assert data["click_count"] >= 0
