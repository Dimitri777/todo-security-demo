"""
Простое Todo REST API на Flask.

Специально оставлено простым, чтобы служить учебным полигоном для
демонстрации security-инструментов: SAST, DAST, SCA, IAST.
"""
from __future__ import annotations

import html
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict

from flask import Flask, jsonify, request, abort

from .iast_middleware import ToyIASTMiddleware


app = Flask(__name__)

# Простое runtime-инструментирование запросов (см. app/iast_middleware.py).
# Это НЕ настоящий IAST-агент, а учебная иллюстрация принципа.
app.wsgi_app = ToyIASTMiddleware(app.wsgi_app)  # type: ignore[assignment]


@dataclass
class Todo:
    id: str
    title: str
    done: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


# In-memory хранилище. В реальном проекте — база данных.
_TODOS: Dict[str, Todo] = {}


@app.get("/health")
def health() -> tuple:
    return jsonify({"status": "ok"}), 200


@app.get("/todos")
def list_todos():
    return jsonify([t.to_dict() for t in _TODOS.values()]), 200


@app.post("/todos")
def create_todo():
    payload = request.get_json(silent=True) or {}
    title = payload.get("title")

    if not title or not isinstance(title, str):
        abort(400, description="Field 'title' is required and must be a string")

    # Экранируем на выходе, а не доверяем вводу "как есть" (XSS-гигиена).
    safe_title = html.escape(title.strip())[:200]

    todo_id = str(uuid.uuid4())
    _TODOS[todo_id] = Todo(id=todo_id, title=safe_title)
    return jsonify(_TODOS[todo_id].to_dict()), 201


@app.get("/todos/<todo_id>")
def get_todo(todo_id: str):
    todo = _TODOS.get(todo_id)
    if todo is None:
        abort(404, description="Todo not found")
    return jsonify(todo.to_dict()), 200


@app.put("/todos/<todo_id>")
def update_todo(todo_id: str):
    todo = _TODOS.get(todo_id)
    if todo is None:
        abort(404, description="Todo not found")

    payload = request.get_json(silent=True) or {}
    if "title" in payload:
        if not isinstance(payload["title"], str):
            abort(400, description="Field 'title' must be a string")
        todo.title = html.escape(payload["title"].strip())[:200]
    if "done" in payload:
        if not isinstance(payload["done"], bool):
            abort(400, description="Field 'done' must be a boolean")
        todo.done = payload["done"]

    return jsonify(todo.to_dict()), 200


@app.delete("/todos/<todo_id>")
def delete_todo(todo_id: str):
    if todo_id not in _TODOS:
        abort(404, description="Todo not found")
    del _TODOS[todo_id]
    return "", 204


@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(err):
    return jsonify({"error": err.description}), err.code


def create_app() -> Flask:
    """Фабрика приложения — удобно для тестов и WSGI-серверов."""
    return app

@app.route('/')
def index():
    return "Security demo app is running!"

if __name__ == "__main__":
    # host=0.0.0.0 нужен, чтобы DAST-сканер (например, ZAP в контейнере) достучался.
    app.run(host="0.0.0.0", port=5000)
