"""Единая фабрика HTTP-клиента.

Dotabuff закрыт Cloudflare, поэтому вместо requests используется cloudscraper,
представляющийся Chrome под Windows.
"""

import cloudscraper


def create_scraper():
    """Новый scraper с общими для всего приложения настройками."""
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
