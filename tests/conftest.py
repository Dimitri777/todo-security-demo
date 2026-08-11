import subprocess
import time
import requests
import pytest
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def app_server():
    # Получаем путь к текущему файлу (conftest.py)
    current_file = Path(__file__)

    # Получаем корень проекта (папка выше tests)
    project_root = current_file.parent.parent

    # Формируем относительные пути к скриптам
    python_executable = project_root / ".venv" / "Scripts" / "python.exe"
    app_script = project_root / "app" / "app.py"

    # Запускаем Flask как подпроцесс
    proc = subprocess.Popen(
        [str(python_executable), str(app_script)],
        cwd=str(project_root)  # Рабочая директория — корень проекта
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
