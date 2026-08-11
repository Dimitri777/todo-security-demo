import subprocess
import time
import requests
import pytest
from pathlib import Path
import sys

@pytest.fixture(scope="session", autouse=True)
def app_server():
    # Получаем путь к текущему файлу (conftest.py)
    current_file = Path(__file__)

    # Получаем корень проекта (папка выше tests)
    project_root = current_file.parent.parent

    # Формируем путь к скрипту (используем относительный путь, понятный везде)
    app_script = "app/app.py"

    # ВАЖНО: Используем sys.executable — он всегда указывает на Python внутри venv
    # Не используем ".venv/Scripts/python.exe" — это сломает запуск на Linux
    cmd = [sys.executable, app_script]

    # Запускаем Flask как подпроцесс
    # cwd=str(project_root) — критически важно, чтобы Python видел модули
    proc = subprocess.Popen(
        cmd,
        cwd=str(project_root),
        stdout=subprocess.PIPE,  # Сохраняем stdout
        stderr=subprocess.PIPE,  # Сохраняем stderr
        text=True,               # Чтобы строки были строками, а не байтами
        bufsize=1
    )

    # Даём серверу время запуститься
    time.sleep(2)

    # Простая проверка, что сервер жив
    try:
        requests.get("http://127.0.0.1:5000/", timeout=5)
    except Exception as e:
        # Если не поднялся — выводим лог ошибок и убиваем процесс
        stdout, stderr = proc.communicate(timeout=1)
        print("=== Flask Server Output ===")
        print(stdout)
        print("=== Flask Server Errors ===")
        print(stderr)
        proc.terminate()
        raise RuntimeError(f"Flask app failed to start. Error: {e}")

    yield  # тесты выполняются здесь

    # После всех тестов гасим сервер
    proc.terminate()
    # Даём время на завершение, затем принудительно убиваем
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
