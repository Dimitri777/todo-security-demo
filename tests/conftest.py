import subprocess
import time
import requests
import pytest


@pytest.fixture(scope="session", autouse=True)
def app_server():
    # Запускаем Flask как подпроцесс
    proc = subprocess.Popen(
        [".venv\\Scripts\\python.exe", "app\\app.py"],
        cwd="C:\\Users\\mrx\\Desktop\\ИЗУЧЕНИЕ ТЕСТИРОВАНИЯ\\todo-security-demo"
    )
    # Даём серверу время запуститься
    time.sleep(2)

    # Простая проверка, что сервер жив
    try:
        requests.get("http://127.0.0.1:5000/", timeout=5)
    except Exception:
        # Если не поднялся — убиваем и выбрасываем ошибку
        proc.terminate()
        raise RuntimeError("Flask app failed to start")

    yield  # тесты выполняются здесь

    # После всех тестов гасим сервер
    proc.terminate()
    proc.wait()
