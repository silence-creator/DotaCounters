"""Хранение выбранной темы и языка между запусками."""

import json
import os
import sys

DEFAULTS = {"theme": "cyber", "lang": "en", "limit": 5}


def _settings_dir():
    """Папка, рядом с которой лежит dota_config.json.

    В собранном одним файлом .exe модули распаковываются во временный каталог,
    и __file__ указывает туда же — этот каталог удаляется при выходе, так что
    настройки бы не пережили перезапуск. Поэтому в замороженном режиме
    ориентируемся на сам исполняемый файл, а при запуске из исходников — на
    корень проекта (уровнем выше пакета), как было раньше.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CONFIG_FILE = os.path.join(_settings_dir(), "dota_config.json")


def cache_dir() -> str | None:
    """Папка для скачанного впрок — иконок героев. None, если создать нельзя."""
    path = os.path.join(_settings_dir(), "cache")
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except OSError:
        return None  # папка только для чтения — обойдёмся без кеша


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return dict(DEFAULTS)


def update_config(**values):
    """Дописать значения, не трогая остальные.

    save_config переписывает файл целиком, поэтому служебные записи вроде даты
    последней проверки обновлений без слияния терялись бы при смене темы.
    """
    cfg = load_config()
    cfg.update(values)
    save_config(cfg)
    return cfg


def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass
