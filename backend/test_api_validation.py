import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_empty_task():
    response = client.post("/run", json={"task": ""})
    assert response.status_code == 422


def test_whitespace_task():
    response = client.post("/run", json={"task": "   "})
    assert response.status_code == 422


def test_missing_task_field():
    response = client.post("/run", json={})
    assert response.status_code == 422


def test_oversized_task():
    long_task = "a" * 2000
    response = client.post("/run", json={"task": long_task})
    assert response.status_code == 422


def test_malformed_json():
    # Send invalid JSON string
    response = client.post("/run", data="{invalid json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422


def test_nonexistent_status():
    response = client.get("/status/nonexistent-id")
    assert response.status_code == 404
