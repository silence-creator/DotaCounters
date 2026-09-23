"""Единая фабрика HTTP-клиента.

Dotabuff закрыт Cloudflare. До версии 1.1 использовался cloudscraper, но с
сентября 2026 он получает 403: библиотека подделывает только заголовки, а
Cloudflare проверяет ещё и TLS-отпечаток соединения. curl_cffi умеет повторять
отпечаток настоящего Chrome, поэтому запросы проходят.

Клиент совместим с requests по тем вызовам, что нужны программе: get(url,
timeout=...) с полями status_code, text, content и headers.
"""

from curl_cffi import requests as curl_requests

#: Какой браузер изображать. Псевдоним без номера версии — curl_cffi сам берёт
#: самый свежий из поддерживаемых, так что обновление библиотеки поднимает и его.
IMPERSONATE = "chrome"


def create_scraper():
    """Новый HTTP-клиент с общими для всего приложения настройками."""
    return curl_requests.Session(impersonate=IMPERSONATE)
