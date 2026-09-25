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
        # Избранное, история, копирование
        "fav_label":         "Favourites",
        "recent_label":      "Recent",
        "fav_add":           "Add to favourites",
        "fav_remove":        "Remove from favourites",
        "copy_btn":          "⧉  COPY",
        "copied":            "Copied to clipboard",
        "copy_empty":        "Nothing to copy yet",
        # Драфт
        "tab_draft":         "DRAFT",
        "draft_label":       "ADD TO",
        "draft_group_enemies": "ENEMIES",
        "draft_group_allies":  "ALLIES",
        "draft_group_bans":    "BANS",
        "draft_row_enemies": "Enemies",
        "draft_row_allies":  "Allies",
        "draft_row_bans":    "Bans",
        "draft_moved":       "{hero} moved: {group}",
        "draft_full_group":  "No more than {max} here",
        "draft_missing":     "  ⟳  Loading: {heroes}\n",
        "draft_role_note":   "  Only heroes with the role: {role}\n",
        "role_label":        "ROLE",
        "role_any":          "Any",
        "role_carry":        "Carry",
        "role_support":      "Support",
        "role_initiator":    "Initiator",
        "role_disabler":     "Disabler",
        "role_nuker":        "Nuker",
        "role_durable":      "Durable",
        "role_escape":       "Escape",
        "role_pusher":       "Pusher",
        "draft_btn":         "⟩  SUGGEST",
        "draft_working":     "  WORKING…",
        "draft_hint":        "Add the enemies — and allies and bans if you like — then press SUGGEST",
        "draft_empty":       "No enemy heroes added yet",
        "draft_dup":         "{hero} is already on the list",
        "draft_full":        "Up to {max} enemy heroes",
        "draft_best":        "BEST PICKS AGAINST",
        "draft_worst":       "WORST PICKS AGAINST",
        "draft_nothing":     "\n  ✕  Nothing to suggest: no full matchup table for these heroes.\n",
        "draft_failed":      "  ✕  {hero}: {detail}\n",
        "draft_skipped":     "  ⚠  No full matchup table for: {heroes}. They were left out.\n",
        "draft_footnote":    "\n  Numbers add up each hero's advantage over the enemies, from Dotabuff.\n",
        # Оверлей поверх игры
        "ov_btn":            "⧉  OVERLAY",
        "ov_key_busy":       "{key} is taken",
        "ov_counters":       "COUNTERS",
        "ov_draft":          "DRAFT",
        "ov_hint_counters":  "Hero name, then Enter",
        "ov_hint_draft":     "Hero, then Enter — into the chosen list",
        "ov_draft_empty":    "Add enemy heroes as they are picked",
        "ov_clear":          "CLEAR",
        "ov_loading":        "Loading…",
        "ov_not_found":      "No hero named “{hero}”",
        "ov_network":        "Dotabuff is not responding",
        "ov_layout":         "Dotabuff changed its page",
        "ov_failed":         "{hero}: not loaded",
        "ov_nothing":        "Nothing to suggest",
        "ov_pick":           "PICK",
        "ov_avoid":          "AVOID",
        "ov_footer":         "{key} — show / hide  ·  Esc — hide",
        "ov_group_enemies":  "ENEMY",
        "ov_group_allies":   "ALLY",
        "ov_group_bans":     "BAN",
        "set_hotkey_head":   "OVERLAY",
        "set_hotkey_sub":    "Hotkey that shows and hides it",
        "set_hotkey_busy":   "{key} is taken by another program — {old} kept",
        "set_hotkey_ok":     "Overlay hotkey: {key}",
        "set_hotkey_custom": "custom, from dota_config.json",
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
        "set_built_val":     "Python · tkinter · curl_cffi · BeautifulSoup",
        "set_desc":          "A lightweight desktop tool for Dota 2 counter-pick analysis.\nParses live data from Dotabuff and displays hero matchup statistics\nfor the current patch.",
        # Updates
        # Обновления программы
        "upd_check_btn":     "Check for updates",
        "upd_checking":      "Checking…",
        "upd_uptodate":      "Version {version} is the latest",
        "upd_available":     "Version {version} is available",
        "upd_install_btn":   "Update",
        "upd_page_btn":      "Release page",
        "upd_downloading":   "Downloading… {percent}%",
        "upd_installing":    "Installing…",
        "upd_restart":       "Restarting…",
        "upd_error":         "Update failed: {detail}",
        "upd_title":         "UPDATES",
        "upd_subtitle":      "Program update history",
        # История изменений: номера в записях — прошлое, поэтому зашиты явно.
        # Верхняя запись обязана совпадать с APP_VERSION — это проверяет тест.
        "upd_text":          "v1.7\n"
                             "Draft: besides the enemies you can add your allies and bans — they drop out of the suggestions. A hero added to another list moves there.\n"
                             "Draft: a role filter — Carry, Support, Initiator and others, as Valve tags the heroes.\n"
                             "The draft is shared by the Draft tab and the overlay, and enemy pages load as soon as a hero is added; SUGGEST retries the ones that failed.\n"
                             "Nicknames work: \"sf\", \"бара\", \"шейкер\", \"войд\", \"карл\" and more. Typing a name and pressing Enter now searches the hero the suggestion shows — \"пудж\" used to give \"hero not found\".\n"
                             "Pangolier and Windranger can be found again — the list had them as Pango and Wind Ranger, which Dotabuff does not know. Largo is added.\n"
                             "Settings: the overlay hotkey can be picked from several combinations.\n"
                             "\n"
                             "v1.6\n"
                             "Overlay: a narrow window on top of the game. Ctrl+Shift+D shows it and puts the cursor in the field even while the game is active; pressing it again or Esc hides it. The OVERLAY button next to the tabs does the same.\n"
                             "The overlay has two modes. Counters: type a hero and press Enter. Draft: add enemy heroes one by one as they are picked, and the picks are recalculated at once; a click on an enemy removes it.\n"
                             "The overlay can be dragged by its top bar and remembers where it was left. It works with Dota in windowed or borderless mode, not in exclusive fullscreen.\n"
                             "The update bar no longer sticks to the tabs and the search field.\n"
                             "\n"
                             "v1.5.1\n"
                             "The network works right after an update. Previously the first launch after Update could not reach any site: the header showed a stale patch number and searches failed until the program was restarted by hand.\n"
                             "The file is now simply DotaCounters.exe, without a version in its name.\n"
                             "\n"
                             "v1.5\n"
                             "Hero names can be typed in Russian: \"пудж\" finds Pudge, \"мипо\" finds Meepo. Misspellings are forgiven too.\n"
                             "Favourites and recent heroes sit under the search field — one click repeats a search. The star marks the hero in the field.\n"
                             "Hero icons are kept on disk, so repeating a search no longer downloads them again and finishes about six times faster.\n"
                             "A Copy button puts the result into the clipboard as text.\n"
                             "The window opens where it was closed, in the same size.\n"
                             "\n"
                             "v1.4\n"
                             "New Draft tab: add up to five enemy heroes and the app sums their matchups to show which heroes to pick against that line-up, and which to avoid.\n"
                             "Counter searches are steadier: Dotabuff turned away part of the requests, so a request is now retried and a draft runs on a single connection.\n"
                             "\n"
                             "v1.3\n"
                             "The app checks GitHub for a new version once a day and shows a bar when one is out; there is also a Check for updates button on this tab.\n"
                             "Update downloads the release, verifies its checksum, replaces the program and restarts it. Where the folder is read-only, the bar links to the release page instead.\n"
                             "\n"
                             "v1.2\n"
                             "Hero name suggestions appear as you type: arrows to pick one, Enter to search, Escape to dismiss. Hyphens and apostrophes can be skipped, so \"antimage\" finds Anti-Mage.\n"
                             "The mouse wheel now scrolls the hero list, Settings and Updates wherever the cursor sits; it used to work only in the gaps between cards.\n"
                             "\n"
                             "v1.1.1\n"
                             "Counter search works again. Dotabuff's protection started rejecting the previous HTTP client in September 2026 and every search failed with HTTP 403; requests now carry a real browser's TLS fingerprint.\n"
                             "\n"
                             "v1.1\n"
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
        # Избранное, история, копирование
        "fav_label":         "Избранное",
        "recent_label":      "Недавние",
        "fav_add":           "В избранное",
        "fav_remove":        "Убрать из избранного",
        "copy_btn":          "⧉  КОПИРОВАТЬ",
        "copied":            "Скопировано в буфер",
        "copy_empty":        "Копировать пока нечего",
        # Драфт
        "tab_draft":         "ДРАФТ",
        "draft_label":       "ДОБАВИТЬ В",
        "draft_group_enemies": "ВРАГИ",
        "draft_group_allies":  "СОЮЗНИКИ",
        "draft_group_bans":    "БАНЫ",
        "draft_row_enemies": "Враги",
        "draft_row_allies":  "Союзники",
        "draft_row_bans":    "Баны",
        "draft_moved":       "{hero} перенесён: {group}",
        "draft_full_group":  "Здесь не больше {max}",
        "draft_missing":     "  ⟳  Загружаются: {heroes}\n",
        "draft_role_note":   "  Только герои с ролью: {role}\n",
        "role_label":        "РОЛЬ",
        "role_any":          "Любая",
        "role_carry":        "Керри",
        "role_support":      "Саппорт",
        "role_initiator":    "Инициатор",
        "role_disabler":     "Контроль",
        "role_nuker":        "Нюкер",
        "role_durable":      "Стойкий",
        "role_escape":       "Побег",
        "role_pusher":       "Пуш",
        "draft_btn":         "⟩  ПОДОБРАТЬ",
        "draft_working":     "  ПОДБОР…",
        "draft_hint":        "Добавьте врагов, при желании союзников и баны, и нажмите ПОДОБРАТЬ",
        "draft_empty":       "Герои противника пока не добавлены",
        "draft_dup":         "{hero} уже в списке",
        "draft_full":        "Не больше {max} героев противника",
        "draft_best":        "ЛУЧШИЙ ВЫБОР ПРОТИВ",
        "draft_worst":       "ХУДШИЙ ВЫБОР ПРОТИВ",
        "draft_nothing":     "\n  ✕  Подбирать не из чего: полной таблицы матчапов у этих героев нет.\n",
        "draft_failed":      "  ✕  {hero}: {detail}\n",
        "draft_skipped":     "  ⚠  Нет полной таблицы матчапов: {heroes}. Они не учтены.\n",
        "draft_footnote":    "\n  Число — сумма преимуществ героя над противниками по данным Dotabuff.\n",
        # Оверлей поверх игры
        "ov_btn":            "⧉  ОВЕРЛЕЙ",
        "ov_key_busy":       "{key} занята",
        "ov_counters":       "КОНТРПИКИ",
        "ov_draft":          "ДРАФТ",
        "ov_hint_counters":  "Имя героя, затем Enter",
        "ov_hint_draft":     "Герой, затем Enter — в выбранный список",
        "ov_draft_empty":    "Добавляйте врагов по мере пиков",
        "ov_clear":          "СБРОС",
        "ov_loading":        "Загрузка…",
        "ov_not_found":      "Нет героя «{hero}»",
        "ov_network":        "Dotabuff не отвечает",
        "ov_layout":         "Dotabuff изменил страницу",
        "ov_failed":         "{hero}: не загрузился",
        "ov_nothing":        "Подбирать не из чего",
        "ov_pick":           "БРАТЬ",
        "ov_avoid":          "НЕ БРАТЬ",
        "ov_footer":         "{key} — показать / скрыть  ·  Esc — скрыть",
        "ov_group_enemies":  "ВРАГ",
        "ov_group_allies":   "СОЮЗ",
        "ov_group_bans":     "БАН",
        "set_hotkey_head":   "ОВЕРЛЕЙ",
        "set_hotkey_sub":    "Клавиша, которая показывает и прячет его",
        "set_hotkey_busy":   "{key} занята другой программой — оставлена {old}",
        "set_hotkey_ok":     "Клавиша оверлея: {key}",
        "set_hotkey_custom": "своя, из dota_config.json",
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
        "set_built_val":     "Python · tkinter · curl_cffi · BeautifulSoup",
        "set_desc":          "Лёгкий десктопный инструмент для анализа контер-пиков в Dota 2.\nПолучает актуальные данные с Dotabuff и отображает статистику\nматчапов для текущего патча.",
        # Updates
        # Обновления программы
        "upd_check_btn":     "Проверить обновления",
        "upd_checking":      "Проверяем…",
        "upd_uptodate":      "Версия {version} — последняя",
        "upd_available":     "Доступна версия {version}",
        "upd_install_btn":   "Обновить",
        "upd_page_btn":      "Страница релиза",
        "upd_downloading":   "Скачивание… {percent}%",
        "upd_installing":    "Установка…",
        "upd_restart":       "Перезапуск…",
        "upd_error":         "Не удалось обновить: {detail}",
        "upd_title":         "ОБНОВЛЕНИЯ",
        "upd_subtitle":      "История обновлений программы",
        "upd_text":          "v1.7\n"
                             "Драфт: кроме врагов можно добавить своих союзников и баны — они исчезают из подсказок. Герой, добавленный в другой список, переносится туда.\n"
                             "Драфт: фильтр по роли — керри, саппорт, инициатор и другие, по разметке Valve.\n"
                             "Состав драфта общий для вкладки и оверлея, а страницы врагов загружаются сразу при добавлении; «Подобрать» повторяет те, что не загрузились.\n"
                             "Работают прозвища: «sf», «бара», «шейкер», «войд», «карл» и другие. Набранное имя с Enter теперь ищет того героя, что показывает подсказка, — раньше «пудж» давал «герой не найден».\n"
                             "Снова находятся Pangolier и Windranger — в списке они были записаны как Pango и Wind Ranger, и Dotabuff их не знал. Добавлен Largo.\n"
                             "Настройки: клавишу оверлея можно выбрать из нескольких сочетаний.\n"
                             "\n"
                             "v1.6\n"
                             "Оверлей — узкое окно поверх игры. Ctrl+Shift+D показывает его и ставит курсор в поле ввода, даже когда активна игра; повторное нажатие или Esc прячет. То же делает кнопка «ОВЕРЛЕЙ» рядом с вкладками.\n"
                             "В оверлее два режима. Контрпики: набрали героя — Enter. Драфт: добавляйте героев противника по одному, по мере пиков, и подбор пересчитывается сразу; щелчок по врагу убирает его.\n"
                             "Оверлей перетаскивается за верхнюю полосу и запоминает, где его оставили. Работает, когда Dota запущена в окне или в окне без рамки; в полноэкранном исключительном режиме — нет.\n"
                             "Плашка обновления больше не липнет к вкладкам и полю поиска.\n"
                             "\n"
                             "v1.5.1\n"
                             "Сеть работает сразу после обновления. Раньше первый запуск после кнопки «Обновить» не мог достучаться ни до одного сайта: в шапке был устаревший номер патча, а поиск не работал, пока программу не перезапустишь вручную.\n"
                             "Файл теперь называется просто DotaCounters.exe, без версии в имени.\n"
                             "\n"
                             "v1.5\n"
                             "Имя героя можно набирать по-русски: «пудж» находит Pudge, «мипо» — Meepo. Опечатки тоже прощаются.\n"
                             "Под полем поиска — избранное и недавние герои, щелчок повторяет поиск. Звёздочка отмечает героя, который сейчас в поле.\n"
                             "Иконки героев хранятся на диске: повторный поиск больше не качает их заново и проходит примерно в шесть раз быстрее.\n"
                             "Кнопка «Копировать» кладёт результат в буфер обмена текстом.\n"
                             "Окно открывается там же и такого же размера, каким его закрыли.\n"
                             "\n"
                             "v1.4\n"
                             "Новая вкладка «Драфт»: добавьте до пяти героев противника, и программа сложит их матчапы и покажет, кого брать против такого состава, а кого не стоит.\n"
                             "Поиск контрпиков стал надёжнее: Dotabuff отбивал часть запросов, теперь запрос повторяется, а подбор в драфте идёт одним соединением.\n"
                             "\n"
                             "v1.3\n"
                             "Программа раз в сутки проверяет, не вышла ли новая версия, и показывает плашку. На этой вкладке есть и кнопка «Проверить обновления».\n"
                             "Кнопка «Обновить» скачивает сборку, сверяет контрольную сумму, заменяет программу и перезапускает её. Если папка защищена от записи, останется ссылка на страницу релиза.\n"
                             "\n"
                             "v1.2\n"
                             "При вводе имени героя появляются подсказки: стрелки — выбрать, Enter — искать, Escape — закрыть. Дефисы и апострофы можно не набирать: «antimage» находит Anti-Mage.\n"
                             "Колесо мыши теперь прокручивает список героев, настройки и обновления в любом месте окна — раньше оно срабатывало только в промежутках между карточками.\n"
                             "\n"
                             "v1.1.1\n"
                             "Поиск контрпиков снова работает. В сентябре 2026 защита Dotabuff перестала пропускать прежний сетевой клиент, и поиск падал с ошибкой HTTP 403; теперь запросы идут с отпечатком настоящего браузера.\n"
                             "\n"
                             "v1.1\n"
                             "Поиск: можно выбрать, сколько контрпиков показывать в каждом разделе, — от 1 до 12.\n"
                             "Изменения патча: окно больше не пустое. Текст идёт на языке интерфейса, с иконками героев, предметов, способностей, характеристик, талантов и Аганима. Больше не теряются таланты, нейтральные крипы, пояснения и пометки новых предметов.\n"
                             "Понятные сообщения, если герой не найден или Dotabuff изменил страницу.\n"
                             "Настройки: разделители больше не перечёркивают подписи.\n"
                             "\n"
                             "v1.0\n"
                             "Первый публичный релиз. Поиск контрпиков через Dotabuff с иконками героев и винрейтами, встроенный список героев с живым поиском, просмотр патчноутов текущего патча Dota 2 прямо в программе, пять цветовых тем и интерфейс на русском и английском. Настройки сохраняются между запусками.",
    },
}
