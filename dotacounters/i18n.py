"""Строки интерфейса на английском и русском.

Номер версии сюда не вписывается руками: он подставляется из version.py,
поэтому обновление APP_VERSION меняет все надписи разом.
"""

from .version import APP_VERSION, SPACED_VERSION

I18N = {
    "en": {
        "app_subtitle":      f"C O U N T E R  I N T E L L I G E N C E  S Y S T E M  v {SPACED_VERSION}",
        "tab_search":        "SEARCH",
        "tab_settings":      "SETTINGS",
        "tab_updates":       "UPDATES",
        "hero_name_label":   "HERO NAME",
        "count_label":       "COUNT",
        "btn_heroes":        "⊞  HEROES",
        "btn_search":        "⟩  SEARCH",
        "btn_searching":     "  SEARCHING…",
        "placeholder":       "e.g.  Pudge",
        "status_await":      "AWAITING INPUT",
        "status_scanning":   "SCANNING NETWORK…",
        "status_complete":   "ANALYSIS COMPLETE",
        "output_header":     "  ANALYSIS OUTPUT",
        "output_source":     "DOTABUFF.COM  ",
        "footer_hint":       "[ ENTER ] search  ·  [ ⊞ HEROES ] browse all heroes  ·  images enabled",
        "welcome_title":     f"COUNTER INTELLIGENCE v{APP_VERSION}",
        "welcome_enter":     "  Enter a hero name above to begin analysis.\n",
        "welcome_browse":    "  Or click ⊞ HEROES to browse all heroes.\n\n",
        "welcome_examples":  "  Examples:\n",
        "loading_msg":       "\n  ⟳  Downloading hero profiles...\n",
        "bad_against":       "BAD AGAINST",
        "good_against":      "GOOD AGAINST",
        # Ошибки разбора и сети
        "status_failed":     "ANALYSIS FAILED",
        "err_not_found":     "  ✕  Dotabuff has no hero named “{hero}”.\n"
                             "      Check the spelling, or pick one from ⊞ HEROES.\n",
        "err_network":       "  ✕  Could not reach Dotabuff.\n"
                             "      {detail}\n",
        "err_layout":        "  ✕  Dotabuff changed its page layout — the data\n"
                             "      cannot be read reliably, so nothing is shown.\n"
                             "      {detail}\n",
        "warn_degraded":     "  ⚠  Section headings were not recognised; sections\n"
                             "      identified by position. Data may be mislabelled.\n\n",
        # Hero browser
        "hb_title":          "HERO BROWSER",
        "hb_sorted":         "heroes  ·  sorted A → Z",
        "hb_search_ph":      "  Search hero…",
        "hb_showing":        "Showing",
        "hb_of":             "of",
        "hb_heroes":         "heroes",
        "hb_no_match":       "\n  No heroes match your search.\n",
        # Заметки к патчу. api_language — код языка для datafeed Valve.
        "api_language":      "english",
        "pn_source":         "  dota2.com  ·  patch notes",
        "pn_window_title":   "Patch {version} notes",
        "pn_filter_ph":      "  Filter by hero or item…",
        "pn_loading":        "\n  ⟳  Loading patch {version} notes…\n",
        "pn_empty":          "\n  ✕  No patch notes available.\n",
        "pn_empty_hint":     "\n  Patch {version} data may not yet be published.\n",
        "pn_status":         "{sections} sections  ·  {notes} changes",
        "pn_status_empty":   "0 sections",
        "pn_general":        "GENERAL",
        "pn_items":          "ITEMS",
        "pn_neutral":        "NEUTRAL ITEMS",
        "pn_creeps":         "NEUTRAL CREEPS",
        # Settings
        "set_title":         "SETTINGS",
        "set_subtitle":      "Customize your experience",
        "set_theme_head":    "THEME",
        "set_theme_sub":     "Select interface color scheme",
        "set_lang_head":     "LANGUAGE  /  ЯЗЫК",
        "set_lang_sub":      "Select interface language",
        "set_lang_en":       "English",
        "set_lang_ru":       "Русский",
        "set_about_head":    "ABOUT",
        "set_ver":           "Version",
        "set_ver_val":       APP_VERSION,
        "set_author":        "Author",
        "set_author_val":    "KIRILL ZALESKIY",
        "set_data":          "Data source",
        "set_data_val":      "dotabuff.com",
        "set_patch":         "Patch API",
        "set_patch_val":     "dota2.com/datafeed",
        "set_built":         "Built with",
        "set_built_val":     "Python · tkinter · cloudscraper · BeautifulSoup",
        "set_desc":          "A lightweight desktop tool for Dota 2 counter-pick analysis.\nParses live data from Dotabuff and displays hero matchup statistics\nfor the current patch.",
        # Updates
        "upd_title":         "UPDATES",
        "upd_subtitle":      "Program update history",
        # История изменений: номера в записях — прошлое, поэтому зашиты явно.
        # Верхняя запись обязана совпадать с APP_VERSION — это проверяет тест.
        "upd_text":          "v1.1\n"
                             "Counter search: choose how many counters to show in each section, from 1 to 12.\n"
                             "Patch notes: the window is no longer empty. Notes follow the interface language and show hero, item, ability, stat, talent and Aghanim's icons. Talents, neutral creeps, explanatory notes and New Item badges are no longer missing.\n"
                             "Clearer messages when a hero is not found or Dotabuff changes its page layout.\n"
                             "Settings: section dividers no longer strike through their labels.\n"
                             "\n"
                             "v1.0\n"
                             "First public release. Counter-pick search via Dotabuff with hero icons and win rates, a built-in hero browser with live search, an in-app reader for the current Dota 2 patch notes, five colour themes and an English/Russian interface. Settings persist between sessions.",
    },
    "ru": {
        "app_subtitle":      f"С И С Т Е М А  А Н А Л И З А  К О Н Т Е Р П И К О В  v {SPACED_VERSION}",
        "tab_search":        "ПОИСК",
        "tab_settings":      "НАСТРОЙКИ",
        "tab_updates":       "ОБНОВЛЕНИЯ",
        "hero_name_label":   "ИМЯ ГЕРОЯ",
        "count_label":       "КОЛ-ВО",
        "btn_heroes":        "⊞  ГЕРОИ",
        "btn_search":        "⟩  ПОИСК",
        "btn_searching":     "  ПОИСК…",
        "placeholder":       "напр.  Pudge",
        "status_await":      "ОЖИДАНИЕ ВВОДА",
        "status_scanning":   "СКАНИРОВАНИЕ СЕТИ…",
        "status_complete":   "АНАЛИЗ ЗАВЕРШЁН",
        "output_header":     "  ВЫВОД АНАЛИЗА",
        "output_source":     "DOTABUFF.COM  ",
        "footer_hint":       "[ ENTER ] поиск  ·  [ ⊞ ГЕРОИ ] все герои  ·  изображения включены",
        "welcome_title":     f"АНАЛИЗ КОНТРПИКОВ v{APP_VERSION}",
        "welcome_enter":     "  Введите имя героя для начала анализа.\n",
        "welcome_browse":    "  Или нажмите ⊞ ГЕРОИ для просмотра списка.\n\n",
        "welcome_examples":  "  Примеры:\n",
        "loading_msg":       "\n  ⟳  Загрузка данных о героях...\n",
        "bad_against":       "СЛАБЕЕ ПРОТИВ",
        "good_against":      "СИЛЬНЕЕ ПРОТИВ",
        # Ошибки разбора и сети
        "status_failed":     "АНАЛИЗ НЕ УДАЛСЯ",
        "err_not_found":     "  ✕  Dotabuff не знает героя «{hero}».\n"
                             "      Проверьте написание или выберите из ⊞ ГЕРОИ.\n",
        "err_network":       "  ✕  Не удалось связаться с Dotabuff.\n"
                             "      {detail}\n",
        "err_layout":        "  ✕  Вёрстка страницы Dotabuff изменилась — данные\n"
                             "      не читаются достоверно, поэтому не показаны.\n"
                             "      {detail}\n",
        "warn_degraded":     "  ⚠  Заголовки разделов не опознаны, разделы определены\n"
                             "      по позиции. Подписи могут быть перепутаны.\n\n",
        # Hero browser
        "hb_title":          "СПИСОК ГЕРОЕВ",
        "hb_sorted":         "героев  ·  по алфавиту",
        "hb_search_ph":      "  Поиск героя…",
        "hb_showing":        "Показано",
        "hb_of":             "из",
        "hb_heroes":         "героев",
        "hb_no_match":       "\n  Герои не найдены.\n",
        # Заметки к патчу. api_language — код языка для datafeed Valve.
        "api_language":      "russian",
        "pn_source":         "  dota2.com  ·  изменения патча",
        "pn_window_title":   "Изменения патча {version}",
        "pn_filter_ph":      "  Фильтр по герою или предмету…",
        "pn_loading":        "\n  ⟳  Загрузка изменений патча {version}…\n",
        "pn_empty":          "\n  ✕  Изменения патча недоступны.\n",
        "pn_empty_hint":     "\n  Данные по патчу {version} могли ещё не выйти.\n",
        "pn_status":         "разделов: {sections}  ·  изменений: {notes}",
        "pn_status_empty":   "разделов: 0",
        "pn_general":        "ОБЩЕЕ",
        "pn_items":          "ПРЕДМЕТЫ",
        "pn_neutral":        "НЕЙТРАЛЬНЫЕ ПРЕДМЕТЫ",
        "pn_creeps":         "НЕЙТРАЛЬНЫЕ КРИПЫ",
        # Settings
        "set_title":         "НАСТРОЙКИ",
        "set_subtitle":      "Персонализация интерфейса",
        "set_theme_head":    "ТЕМА",
        "set_theme_sub":     "Выберите цветовую схему интерфейса",
        "set_lang_head":     "ЯЗЫК  /  LANGUAGE",
        "set_lang_sub":      "Выберите язык интерфейса",
        "set_lang_en":       "English",
        "set_lang_ru":       "Русский",
        "set_about_head":    "О ПРОГРАММЕ",
        "set_ver":           "Версия",
        "set_ver_val":       APP_VERSION,
        "set_author":        "Автор",
        "set_author_val":    "КИРИЛЛ ЗАЛЕСКИЙ",
        "set_data":          "Источник данных",
        "set_data_val":      "dotabuff.com",
        "set_patch":         "API патчей",
        "set_patch_val":     "dota2.com/datafeed",
        "set_built":         "Технологии",
        "set_built_val":     "Python · tkinter · cloudscraper · BeautifulSoup",
        "set_desc":          "Лёгкий десктопный инструмент для анализа контер-пиков в Dota 2.\nПолучает актуальные данные с Dotabuff и отображает статистику\nматчапов для текущего патча.",
        # Updates
        "upd_title":         "ОБНОВЛЕНИЯ",
        "upd_subtitle":      "История обновлений программы",
        "upd_text":          "v1.1\n"
                             "Поиск: можно выбрать, сколько контрпиков показывать в каждом разделе, — от 1 до 12.\n"
                             "Изменения патча: окно больше не пустое. Текст идёт на языке интерфейса, с иконками героев, предметов, способностей, характеристик, талантов и Аганима. Больше не теряются таланты, нейтральные крипы, пояснения и пометки новых предметов.\n"
                             "Понятные сообщения, если герой не найден или Dotabuff изменил страницу.\n"
                             "Настройки: разделители больше не перечёркивают подписи.\n"
                             "\n"
                             "v1.0\n"
                             "Первый публичный релиз. Поиск контрпиков через Dotabuff с иконками героев и винрейтами, встроенный список героев с живым поиском, просмотр патчноутов текущего патча Dota 2 прямо в программе, пять цветовых тем и интерфейс на русском и английском. Настройки сохраняются между запусками.",
    },
}
