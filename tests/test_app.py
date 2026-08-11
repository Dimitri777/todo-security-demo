import pytest
import requests

from app.app import app as flask_app, _TODOS


@pytest.fixture
def client():
    flask_app.config.update(TESTING=True)
    _TODOS.clear()
    with flask_app.test_client() as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_list_empty(client):
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_todo(client):
    resp = client.post("/todos", json={"title": "Купить молоко"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["title"] == "Купить молоко"
    assert body["done"] is False
    assert "id" in body


def test_create_todo_missing_title(client):
    resp = client.post("/todos", json={})
    assert resp.status_code == 400


def test_create_todo_wrong_type(client):
    resp = client.post("/todos", json={"title": 123})
    assert resp.status_code == 400


def test_create_todo_escapes_html(client):
    resp = client.post("/todos", json={"title": "<script>alert(1)</script>"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert "<script>" not in body["title"]
    assert "&lt;script&gt;" in body["title"]


def test_get_todo(client):
    created = client.post("/todos", json={"title": "Позвонить маме"}).get_json()
    resp = client.get(f"/todos/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == created["id"]


def test_get_missing_todo(client):
    resp = client.get("/todos/does-not-exist")
    assert resp.status_code == 404


def test_update_todo(client):
    created = client.post("/todos", json={"title": "Погулять"}).get_json()
    resp = client.put(f"/todos/{created['id']}", json={"done": True})
    assert resp.status_code == 200
    assert resp.get_json()["done"] is True


def test_update_todo_wrong_type(client):
    created = client.post("/todos", json={"title": "Погулять"}).get_json()
    resp = client.put(f"/todos/{created['id']}", json={"done": "yes"})
    assert resp.status_code == 400


def test_update_missing_todo(client):
    resp = client.put("/todos/does-not-exist", json={"done": True})
    assert resp.status_code == 404


def test_delete_todo(client):
    created = client.post("/todos", json={"title": "Удалить меня"}).get_json()
    resp = client.delete(f"/todos/{created['id']}")
    assert resp.status_code == 204

    resp2 = client.get(f"/todos/{created['id']}")
    assert resp2.status_code == 404


def test_delete_missing_todo(client):
    resp = client.delete("/todos/does-not-exist")
    assert resp.status_code == 404


def test_full_flow(client):
    # Создаём несколько задач и проверяем список
    client.post("/todos", json={"title": "A"})
    client.post("/todos", json={"title": "B"})
    resp = client.get("/todos")
    assert len(resp.get_json()) == 2

def test_root_returns_ok():
    r = requests.get("http://127.0.0.1:5000/")
    assert r.status_code == 200