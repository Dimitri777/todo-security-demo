"""
Учебная имитация IAST (Interactive Application Security Testing).

ВАЖНО: настоящий IAST — это агент, встраиваемый в рантайм (байткод/JVM
инструментация и т.п.), который отслеживает поток "грязных" (untrusted)
данных от источника (request) до опасного места использования (sink:
SQL-запрос, exec, запись файла и т.д.) прямо во время выполнения тестов
или в проде. Из открытых бесплатных инструментов полноценного IAST
практически нет — это в основном коммерческие продукты (Contrast
Security, Checkmarx IAST, HCL AppScan, OpenText Fortify).

Этот модуль НЕ является заменой такому инструменту. Это простая WSGI
middleware, которая:
  1. Помечает все данные из query string, form и JSON body как "tainted".
  2. Логирует, если такие данные позже "утекают" без экранирования в
     заголовки ответа или напрямую совпадают с телом ответа без изменений
     в подозрительном контексте (очень грубая эвристика).

Используйте это только как учебный пример принципа работы IAST в CI/CD
пайплайне; для реального проекта подключайте настоящий IAST-агент.
"""
from __future__ import annotations

import logging
from typing import Callable, Iterable

logger = logging.getLogger("toy_iast")
logging.basicConfig(level=logging.INFO)


class ToyIASTMiddleware:
    """Простая WSGI middleware для демонстрации runtime-мониторинга."""

    def __init__(self, wsgi_app: Callable) -> None:
        self.wsgi_app = wsgi_app

    def __call__(self, environ: dict, start_response: Callable) -> Iterable[bytes]:
        query_string = environ.get("QUERY_STRING", "")

        tainted_markers = []
        if query_string:
            tainted_markers.append(query_string)

        response_body_chunks = []

        def capturing_start_response(status, headers, exc_info=None):
            for marker in tainted_markers:
                for _, value in headers:
                    if marker and marker in value:
                        logger.warning(
                            "[toy-iast] Возможная утечка непроверенных данных "
                            "из query string в заголовок ответа: %r", marker
                        )
            return start_response(status, headers, exc_info)

        for chunk in self.wsgi_app(environ, capturing_start_response):
            response_body_chunks.append(chunk)
            for marker in tainted_markers:
                if marker.encode() in chunk:
                    logger.warning(
                        "[toy-iast] Query string отражается в теле ответа "
                        "без видимого экранирования: %r", marker
                    )

        return response_body_chunks
