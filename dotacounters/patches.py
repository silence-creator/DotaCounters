"""Данные о патчах Dota 2 из официального datafeed Valve.

fetch_current_patch() определяет номер актуального патча, fetch_patch_notes()
разбирает заметки к нему в секции, пригодные для показа в окне.
"""

import re

from bs4 import BeautifulSoup

from .net import create_scraper


def fetch_current_patch():
    scraper = create_scraper()
    # Source 1: Valve JSON API
    try:
        url = "https://www.dota2.com/datafeed/patchnoteslist?language=english"
        resp = scraper.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            patches = data.get("patches") or data.get("patch_notes") or []
            if patches:
                newest = patches[-1]
                number = (
                    newest.get("patch_number")
                    or newest.get("patch_name")
                    or newest.get("version")
                    or ""
                )
                m = re.search(r'7\.\d+[a-z]?', str(number))
                if m:
                    return m.group(0)
    except Exception:
        pass
    # Source 2: Dotabuff page
    try:
        resp = scraper.get(
            "https://www.dotabuff.com/heroes/anti-mage/counters", timeout=10
        )
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup.find_all(string=re.compile(r'(?i)patch')):
                m = re.search(r'7\.\d+[a-z]?', tag)
                if m:
                    return m.group(0)
            m = re.search(r'7\.\d+[a-z]?', resp.text)
            if m:
                return m.group(0)
    except Exception:
        pass
    return "7.41b"


def fetch_patch_notes(patch_version: str) -> list[dict]:
    """
    Загружает список изменений патча через Valve JSON API.
    Возвращает формат для вашего GUI: [{"title": str, "notes": [str, ...]}, ...]
    """
    scraper = create_scraper()

    try:
        # Убираем лишние точки, если пользователь ввел "7.35."
        patch_version = patch_version.strip().strip('.')

        # Step 1: Resolve the exact internal version key from the patch list.
        # Valve's patchnotes API uses a specific key (e.g. "7.41b" or "7.41_2")
        # that may differ from the display name. We look it up first.
        resolved_version = patch_version
        try:
            list_url = "https://www.dota2.com/datafeed/patchnoteslist?language=english"
            list_resp = scraper.get(list_url, timeout=10)
            if list_resp.status_code == 200:
                list_data = list_resp.json()
                patches = list_data.get("patches") or list_data.get("patch_notes") or []
                # Build a map of display-name → internal key
                # Each patch entry typically has "patch_number" and optionally a
                # separate "patch_name" or "version" field used as the API key.
                for p in reversed(patches):  # newest first
                    # The internal key used by the /patchnotes endpoint
                    internal_key = (
                        p.get("patch_name")
                        or p.get("version")
                        or p.get("patch_number")
                        or ""
                    )
                    display_name = (
                        p.get("patch_number")
                        or p.get("patch_name")
                        or p.get("version")
                        or ""
                    )
                    # Match either by display name or by internal key
                    m_internal = re.search(r'7\.\d+[a-z]?', str(internal_key))
                    m_display  = re.search(r'7\.\d+[a-z]?', str(display_name))
                    matched_display  = m_display.group(0)  if m_display  else ""
                    matched_internal = m_internal.group(0) if m_internal else ""
                    if matched_display == patch_version or matched_internal == patch_version:
                        resolved_version = str(internal_key).strip()
                        break
                else:
                    # Fallback: try the last patch in the list
                    if patches:
                        last = patches[-1]
                        resolved_version = str(
                            last.get("patch_name")
                            or last.get("version")
                            or last.get("patch_number")
                            or patch_version
                        ).strip()
        except Exception:
            pass  # Keep resolved_version = patch_version if lookup fails

        url = f"https://www.dota2.com/datafeed/patchnotes?version={resolved_version}&language=english"

        resp = scraper.get(url, timeout=12)
        if resp.status_code != 200:
            return []

        data = resp.json()

        # Valve sometimes wraps everything under a "result" or "patch" key
        if not any(k in data for k in ("generic_notes", "items", "heroes")):
            for wrapper_key in ("result", "patch", "data", "notes"):
                if isinstance(data.get(wrapper_key), dict):
                    data = data[wrapper_key]
                    break

        sections = []

        # 1. GENERAL (Это СПИСОК в JSON Valve)
        generic = data.get("generic_notes")
        if isinstance(generic, list) and generic:
            notes = []
            for entry in generic:
                note = entry.get("note") or entry.get("text")
                if note: notes.append(note.strip())
            if notes:
                sections.append({"title": "GENERAL", "notes": notes})

        # 2. ITEMS (Это СЛОВАРЬ в JSON Valve)
        items_data = data.get("items")
        if isinstance(items_data, dict):
            item_notes = []
            for item_key, item_info in items_data.items():
                # Проверяем, что item_info - это словарь, а не список
                if isinstance(item_info, dict):
                    changes = item_info.get("ability_notes") or item_info.get("notes") or []
                    for ch in changes:
                        note = ch.get("note") or ch.get("text")
                        if note:
                            name = item_key.replace('item_', '').replace('_', ' ').upper()
                            item_notes.append(f"{name}: {note.strip()}")
            if item_notes:
                sections.append({"title": "ITEMS", "notes": item_notes})

        # 3. HEROES (Это СЛОВАРЬ в JSON Valve)
        heroes_data = data.get("heroes")
        if isinstance(heroes_data, dict):
            for hero_key, hero_info in heroes_data.items():
                if not isinstance(hero_info, dict): continue
                
                hero_display = hero_key.replace("npc_dota_hero_", "").replace("_", " ").upper()
                current_hero_notes = []

                # Заметки героя
                h_notes = hero_info.get("hero_notes") or []
                for entry in h_notes:
                    note = entry.get("note") or entry.get("text")
                    if note: current_hero_notes.append(note.strip())

                # Способности героя
                abilities = hero_info.get("abilities") or {}
                if isinstance(abilities, dict):
                    for ab_key, ab_info in abilities.items():
                        if not isinstance(ab_info, dict): continue
                        ab_notes = ab_info.get("ability_notes") or []
                        ab_name = ab_key.replace("_", " ").title()
                        for entry in ab_notes:
                            note = entry.get("note") or entry.get("text")
                            if note: current_hero_notes.append(f"[{ab_name}] {note.strip()}")

                if current_hero_notes:
                    sections.append({"title": hero_display, "notes": current_hero_notes})

        return sections

    except Exception as e:
        print(f"Критическая ошибка парсинга: {e}")
        return []
