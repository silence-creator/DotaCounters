"""Строки интерфейса на английском и русском.

Ключи сгруппированы по месту в интерфейсе. Тест test_i18n сверяет файл с кодом:
каждый ключ, к которому обращается интерфейс, здесь есть, и лишних нет. Ключи,
которые собираются из частей («role_» + позиция), перечислены в этом тесте.
"""

I18N = {
    "en": {
        # ── Шапка, вкладки, период
        "tab_search":        "Counters",
        "tab_settings":      "Settings",
        "tab_draft":         "Draft",
        "period_label":      "Data for",
        "period_week":       "Week",
        "period_month":      "Month",
        "period_patch":      "Patch",
        "ov_btn":            "Overlay",
        "api_language":      "english",
        "tab_cm":            "Captains Mode",
        "period_patch_n":    "Patch {patch}",
        "for_month":         "for the month",
        "for_week":          "for the week",
        "for_patch":         "for patch {patch}",
        "loading":           "Loading…",

        # ── Числа и время
        "age_min":           "{n} min",
        "age_hours":         "{n} h",
        "count_k":           "k",
        "count_m":           "M",
        "count_decimal":     ".",

        # ── Контрпики
        "welcome_title":     "Who counters whom",
        "err_not_found":     "Dotabuff has no hero named “{hero}”. Check the spelling or pick one from All heroes.",
        "err_network":       "Could not reach Dotabuff: {detail}",
        "err_layout":        "Dotabuff changed its page layout, so nothing is shown rather than wrong numbers. "
                             "{detail}",
        "warn_degraded":     "Section headings were not recognised; sections are taken by position and may be "
                             "mislabelled.",
        "fav_label":         "Favourites",
        "recent_label":      "Recent",
        "copy_btn":          "Copy",
        "copied":            "Copied",
        "role_no_table":     "This page has no full matchup table, so the role filter cannot be applied.",
        "hero_label":        "Hero — name, nickname or in Russian",
        "hero_placeholder":  "e.g. Pudge",
        "name_placeholder":  "Name or nickname, Enter",
        "btn_find":          "Find",
        "btn_all_heroes":    "All heroes",
        "enemy_role_label":  "Opponents' position",
        "welcome_text":      "Type a hero and press Enter: you get the heroes they are weak and strong against, "
                             "with the advantage and how many games it rests on.",
        "games_for":         "{games} games {period}",
        "saved_ago":         "saved {age} ago",
        "fresh":             "just downloaded",
        "fav_on":            "In favourites",
        "fav_off":           "Add to favourites",
        "weak_against":      "{hero} is weak against",
        "strong_against":    "{hero} is strong against",
        "adv_enemy":         "opponent's advantage",
        "adv_hero":          "{hero}'s advantage",
        "nothing_here":      "No heroes to show",
        "row_meta":          "{hero} win rate {wr} · {n} games",
        "row_meta_wr":       "{hero} win rate {wr}",
        "adv_footnote":      "Advantage — how much more or less often the pair wins than the heroes' overall win "
                             "rates suggest. Pairs under 2000 games are not shown.",

        # ── Позиции и роли
        "role_label":        "Position",
        "role_any":          "Any",
        "role_carry":        "Carry",
        "role_support":      "Support",
        "role_initiator":    "Initiator",
        "role_disabler":     "Disabler",
        "role_nuker":        "Nuker",
        "role_durable":      "Durable",
        "role_escape":       "Escape",
        "role_pusher":       "Pusher",
        "role_more":         "More",
        "role_pos1":         "Carry",
        "role_pos2":         "Mid",
        "role_pos3":         "Offlane",
        "role_pos4":         "Pos 4",
        "role_pos5":         "Pos 5",

        # ── Подбор под свободные позиции
        "fill_on":           "For open positions: {positions}",
        "fill_all":          "show all",
        "fill_off":          "All positions",
        "fill_only":         "only open positions",
        "fill_theirs":       "For the enemy's open positions: {positions}",

        # ── Драфт
        "draft_row_enemies": "Enemy",
        "draft_row_allies":  "My team",
        "draft_row_bans":    "Bans",
        "draft_moved":       "{hero} moved: {group}",
        "draft_full_group":  "No more than {max} here",
        "draft_missing":     "Loading: {heroes}",
        "draft_dup":         "{hero} is already on the list",
        "draft_nothing":     "Nothing to suggest: no full matchup table for these heroes.",
        "draft_failed":      "{hero}: {detail}",
        "draft_skipped":     "No full matchup table for: {heroes}. They were left out.",
        "draft_add":         "Add a hero",
        "draft_to_enemies":  "Enemy",
        "draft_to_allies":   "My team",
        "draft_to_bans":     "Ban",
        "draft_next_enemies": "Next enemy pick",
        "draft_next_allies": "Next ally pick",
        "draft_no_bans":     "No bans yet",
        "draft_ban_hint":    "Click a ban to remove it",
        "draft_retry":       "Retry",
        "draft_empty_title": "Add the enemy heroes",
        "draft_empty_text":  "Suggestions appear as soon as the first enemy is added. Your team and bans drop out "
                             "of the suggestions.",
        "draft_pick_title":  "Pick",
        "draft_against":     "against {heroes}",
        "draft_avoid_title": "Avoid",
        "draft_footnote2":   "Sum of advantages over the enemies. Games — in the least played pair; pairs under "
                             "2000 games count as zero.",
        "col_hero":          "Hero",
        "col_sum":           "Sum",
        "col_matches":       "Games",
        "draft_open":        "Open: {positions}",
        "draft_all_covered": "All positions are covered",

        # ── Captains Mode
        "side_radiant":      "Radiant",
        "side_dire":         "Dire",
        "cm_we_play":        "We play",
        "cm_first":          "First move",
        "cm_you":            " · you",
        "cm_undo":           "Undo",
        "cm_reset":          "Reset",
        "cm_ban":            "BAN",
        "cm_pick":           "PICK",
        "cm_your_ban":       "Your ban",
        "cm_your_pick":      "Your pick",
        "cm_their_ban":      "Ban by {side}",
        "cm_their_pick":     "Pick by {side}",
        "cm_done":           "Draft complete",
        "cm_done_hint":      "All 24 moves are made. Reset to start over.",
        "cm_step":           "Move {n} of {total} · {phase}",
        "cm_phase_ban":      "ban phase {n}",
        "cm_phase_pick":     "pick phase {n}",
        "cm_next":           "Next: {steps}",
        "cm_entry_ban":      "Who was banned on move {n}",
        "cm_entry_pick":     "Who was picked on move {n}",
        "cm_ban_title":      "Who to ban",
        "cm_pick_title":     "Your pick",
        "cm_pick_at":        "Your pick on move {n}",
        "cm_ban_why":        "strongest against your picks: {heroes}",
        "cm_pick_why":       "against their picks: {heroes}",
        "cm_failed":         "Not loaded: {heroes}",
        "cm_taken":          "{hero} is already banned or picked",
        "cm_undone":         "Undone: {hero}",
        "cm_footnote":       "Banned and picked heroes drop out of the suggestions. Games — in the least played "
                             "pair. Move order — Captains Mode 7.41.",

        # ── Мета: баны до своих пиков
        "meta_why":          "strongest in the meta by win rate — among heroes picked in {pick}%+ of "
                             "games, for the month",
        "meta_pick":         "in {pick} of games",
        "meta_failed":       "Could not load the meta: {detail}",
        "ov_meta":           "meta · {rank}",
        "meta_pick_why":     "the enemy has not picked yet — the strongest in the meta for your open "
                             "positions, among heroes picked in {pick}%+ of games",
        "ov_we":             "We",
        "ov_first":          "First",

        # ── Оценка драфта
        "view_picks":        "Suggestions",
        "view_eval":         "Draft evaluation",
        "eval_empty":        "The evaluation appears once both teams have at least one hero.",
        "eval_ours":         "Your team",
        "eval_you":          "{side} (you)",
        "eval_theirs":       "Enemy",
        "eval_score":        "{team} is ahead on matchups: {value}",
        "eval_score_why":    "sum of advantages over all {n} pairs divided by 5 — every hero faces five. "
                             "This is the matchup edge, not a win probability.",
        "eval_meta":         "Heroes' win rate in the meta ({rank}): {ours} vs {theirs}",
        "eval_unknown":      "No matchup data yet: {heroes}",
        "eval_best":         "Best pairs",
        "eval_worst":        "Dangerous pairs",
        "eval_no_pairs":     "none",
        "eval_lanes":        "Lanes",
        "eval_lane_vs":      "{ours} vs {theirs}",
        "lane_safe":         "Your safe lane",
        "lane_mid":          "Mid",
        "lane_off":          "Your offlane",
        "eval_footnote":     "A pair's value is from Dotabuff for the whole game, not just the laning stage. "
                             "Lanes follow the positions the program assigns to each team.",
        "rank_all":          "All ranks",
        "rank_herald":       "Crusader and lower (under 2K)",
        "rank_archon":       "Archon (2–3K)",
        "rank_legend":       "Legend (3–4K)",
        "rank_ancient":      "Ancient (4–5K)",
        "rank_divine":       "Divine and Immortal (5K+)",
        "rank_short_all":    "All ranks",
        "rank_short_herald": "Under 2K",
        "rank_short_archon": "Archon",
        "rank_short_legend": "Legend",
        "rank_short_ancient": "Ancient",
        "rank_short_divine": "Divine+",
        "cm_hint_games":     "{n} games",

        # ── Оверлей
        "ov_key_busy":       "{key} is taken",
        "ov_counters":       "Counters",
        "ov_draft":          "All Pick",
        "ov_hint_counters":  "Hero name, then Enter",
        "ov_hint_draft":     "Hero, then Enter — into the chosen list",
        "ov_draft_empty":    "Add enemy heroes as they are picked",
        "ov_clear":          "Clear",
        "ov_not_found":      "No hero named “{hero}”",
        "ov_network":        "Dotabuff is not responding",
        "ov_layout":         "Dotabuff changed its page",
        "ov_failed":         "{hero}: not loaded",
        "ov_nothing":        "Nothing to suggest",
        "ov_pick":           "Pick",
        "ov_avoid":          "Avoid",
        "ov_footer":         "{key} — show / hide  ·  Esc — hide",
        "ov_group_enemies":  "Enemy",
        "ov_group_allies":   "Ally",
        "ov_group_bans":     "Ban",
        "ov_cm":             "Captains Mode",
        "ov_step":           "move {n} of {total}",
        "ov_against":        "against {heroes}",
        "ov_any":            "All",

        # ── Считывание с экрана
        "scr_off":           "Read from screen",
        "scr_on":            "Reading the screen ✓",
        "scr_hint":          "Recognises heroes on the Dota draft screen by itself. Needs windowed or borderless window mode.",
        "scr_loading":       "Preparing hero portraits…",
        "scr_portraits_failed": "Could not load hero portraits — check the connection",
        "scr_missing":       "Dota 2 is not running",
        "scr_minimized":     "Dota 2 is minimised",
        "scr_black":         "The game image is black — switch Dota to borderless window mode",
        "scr_idle":          "Open Draft or Captains Mode — here or in the overlay",
        "scr_no_draft":      "Waiting for the draft screen",
        "scr_watching":      "Watching the draft · heroes recognised: {n}",
        "scr_side_unknown":  "Can't tell which side you play on",
        "scr_conflict":      "Move {n}: the screen shows {screen}, but {model} is recorded",
        "scr_error":         "Reading failed: {detail}",
        "scr_ask_slot":      "{side} {n} — who is it?",
        "scr_ask_move":      "Move {n} — who is it?",
        "scr_other":         "other…",

        # ── Список героев
        "hb_title":          "All heroes",
        "hb_sorted":         "heroes  ·  sorted A → Z",
        "hb_search_ph":      "  Search hero…",
        "hb_showing":        "Showing",
        "hb_of":             "of",
        "hb_heroes":         "heroes",
        "hb_no_match":       "\n"
                             "  No heroes match your search.\n",

        # ── Изменения патча
        "pn_source":         "  dota2.com  ·  patch notes",
        "pn_window_title":   "Patch {version} notes",
        "pn_filter_ph":      "  Filter by hero or item…",
        "pn_loading":        "\n"
                             "  ⟳  Loading patch {version} notes…\n",
        "pn_empty":          "\n"
                             "  ✕  No patch notes available.\n",
        "pn_empty_hint":     "\n"
                             "  Patch {version} data may not yet be published.\n",
        "pn_status":         "{sections} sections  ·  {notes} changes",
        "pn_status_empty":   "0 sections",
        "pn_general":        "General",
        "pn_items":          "Items",
        "pn_neutral":        "Neutral items",
        "pn_creeps":         "Neutral creeps",
        "pn_title":          "Patch {patch}",

        # ── Настройки
        "set_cache_head":    "Data",
        "set_cache_info":    "Heroes saved: {n}. A page is kept for 24 hours and is downloaded again after a new "
                             "patch.",
        "set_cache_clear":   "Clear",
        "set_cache_cleared": "Removed: {n}. The next search downloads fresh pages.",
        "set_hotkey_head":   "Overlay",
        "set_hotkey_sub":    "Shows and hides the overlay on top of the game",
        "set_hotkey_busy":   "{key} is taken by another program — {old} kept",
        "set_hotkey_ok":     "Overlay hotkey: {key}",
        "set_hotkey_custom": "custom, from dota_config.json",
        "set_about_head":    "About",
        "set_look":          "Appearance",
        "set_theme":         "Theme",
        "set_lang":          "Language",
        "set_rows":          "Rows in lists",
        "set_rows_hint":     "How many heroes the lists and suggestions show, from 1 to 12.",
        "set_hotkey":        "Hotkey",
        "set_version":       "DotaCounters {version}",
        "set_about_text":    "A desktop tool for Dota 2 counter picks and drafts. Matchup data comes from "
                             "Dotabuff, patch notes and hero roles from Valve's datafeed. Not affiliated with "
                             "Valve Corporation.",

        # ── Обновления
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
        "upd_title":         "Updates",
        "upd_text":          "v2.4\n"
                             "Reading the draft from the screen — the «Read from screen» switch in Draft, Captains Mode and the overlay. Once a second the program looks at the Dota window and recognises heroes by their portraits: in All Pick from the top bar (your team and the enemies are told apart by your name), in Captains Mode from the board with bans, who moves first and your side. A hero is recorded only when several shots in a row agree; a hero someone only hovers over is not a pick.\n"
                             "The program never fills in a hero it is unsure of: such a cell shows a question with three candidates — one click. The confirmed cell is remembered, so a hero in a set that does not look like his portrait is recognised next time.\n"
                             "Works with Dota in windowed or borderless window mode; in exclusive fullscreen Windows does not let other programs see the game.\n"
                             "\n"
                             "v2.3\n"
                             "Draft evaluation — in the Draft and Captains Mode tabs, next to the suggestions: which team is ahead on matchups and by how much, a table of every hero against every enemy, the best and the most dangerous pairs, the lanes by positions and the heroes' win rate in the meta. After the last Captains Mode move it opens by itself.\n"
                             "Captains Mode: before the enemy picks anyone, picks are suggested from the meta too — the strongest heroes for your open positions.\n"
                             "Overlay in Captains Mode: shows both who to ban and who to pick, and lets you choose your side and who moves first. The overlay is taller.\n"
                             "Your team in All Pick holds five heroes — yours included, for the evaluation.\n"
                             "\n"
                             "v2.2\n"
                             "Captains Mode: bans of the first phase, before anyone has picked. They come from the meta — the strongest heroes by win rate among those picked in at least 5% of games; the rank is chosen next to the list and remembered.\n"
                             "Captains Mode: after the first picks, ban suggestions are for the positions the enemy still lacks — no point banning a carry when they already have one. «show all» turns it off.\n"
                             "\n"
                             "v2.1\n"
                             "Positions in the filter: Carry, Mid, Offlane, Pos 4, Pos 5. Valve has no positions, only roles, so they come from Dotabuff lane statistics: the share of a hero's games in each lane and the gold earned there. A hero counts for a position from 20% of games; some heroes have two or three. Valve roles are under More.\n"
                             "The hero card shows the hero's positions before the roles.\n"
                             "Pick suggestions in the draft and Captains Mode are for the positions your team still lacks: the program places your heroes on positions and shows which are open. «show all» turns it off; picking a position or role by hand turns it off too.\n"
                             "Heroes' positions under their names in the suggestions, the draft and the overlay.\n"
                             "The overlay has its own position row: All, 1–5 — for the mode that is open.\n"
                             "The chosen position or role is remembered between launches.\n"
                             "The smallest window is now 1040×700: in a smaller one the header and the Captains Mode board were cut off.\n"
                             "Closing the patch notes before they loaded no longer causes an error in the background.\n"
                             "\n"
                             "v2.0\n"
                             "New interface: calm graphite colours instead of neon, a readable font, hero portraits instead of text lists. The advantage is shown as a number with a bar, the win rate and games — in grey under the name. There is also a light theme.\n"
                             "Sharp text with Windows scaling at 125–200%: the program used to be stretched by the system like a picture, and small text was blurry.\n"
                             "Captains Mode: a separate tab with the full order of 24 bans and picks. Enter heroes one by one — the program shows whose move it is, who to ban against your picks and who to pick against theirs.\n"
                             "Draft: the enemy team, your team and bans side by side with portraits; a suggestion table with a column for each enemy.\n"
                             "Period: data for the last week, month or the whole patch — a switch in the header. A whole patch has about five times more games, so the numbers are steadier; a week shows the latest balance changes. The choice is remembered.\n"
                             "Every row shows how many games the pair has played — how much the number rests on. In the draft it is the hero's least played pair with the enemies.\n"
                             "Patch notes open from the patch number next to the program name; updates and the change history are in Settings. The overlay got the same look and a Captains Mode mode.\n"
                             "\n"
                             "v1.8\n"
                             "Search: a role filter — for example, which supports are strongest against Pudge. Changing the role redraws the result without a new download.\n"
                             "Rare matchups no longer mislead: pairs played fewer than 2000 times are left out of the lists, and in the draft they count as zero. These are mostly pairs with Chen, Batrider, Elder Titan, Lycan, Visage and Brewmaster.\n"
                             "Dotabuff pages are kept for 24 hours in the cache folder next to the program: a repeated search or draft is instant, and fewer requests are turned away. After a new patch the pages are downloaded again. Settings show how many are saved and can clear them.\n"
                             "Hero icons no longer vanish: after a search and then a draft, switching back to the Search tab left empty spaces instead of icons, and the same the other way round.\n"
                             "\n"
                             "v1.7\n"
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
        # ── Шапка, вкладки, период
        "tab_search":        "Контрпики",
        "tab_settings":      "Настройки",
        "tab_draft":         "Драфт",
        "period_label":      "Данные за",
        "period_week":       "Неделю",
        "period_month":      "Месяц",
        "period_patch":      "Патч",
        "ov_btn":            "Оверлей",
        "api_language":      "russian",
        "tab_cm":            "Captains Mode",
        "period_patch_n":    "Патч {patch}",
        "for_month":         "за месяц",
        "for_week":          "за неделю",
        "for_patch":         "за патч {patch}",
        "loading":           "Загрузка…",

        # ── Числа и время
        "age_min":           "{n} мин",
        "age_hours":         "{n} ч",
        "count_k":           "к",
        "count_m":           " млн",
        "count_decimal":     ",",

        # ── Контрпики
        "welcome_title":     "Кто кого контрит",
        "err_not_found":     "Dotabuff не знает героя «{hero}». Проверьте написание или выберите в «Все герои».",
        "err_network":       "Не удалось связаться с Dotabuff: {detail}",
        "err_layout":        "Вёрстка страницы Dotabuff изменилась — вместо неверных цифр не показано ничего. "
                             "{detail}",
        "warn_degraded":     "Заголовки разделов не опознаны: разделы взяты по порядку и могут быть перепутаны.",
        "fav_label":         "Избранное",
        "recent_label":      "Недавние",
        "copy_btn":          "Копировать",
        "copied":            "Скопировано",
        "role_no_table":     "На странице нет полной таблицы матчапов — фильтр по роли применить нельзя.",
        "hero_label":        "Герой — имя, прозвище или по-русски",
        "hero_placeholder":  "например, Pudge",
        "name_placeholder":  "Имя или прозвище, Enter",
        "btn_find":          "Найти",
        "btn_all_heroes":    "Все герои",
        "enemy_role_label":  "Позиция соперников",
        "welcome_text":      "Наберите героя и нажмите Enter: появятся герои, против которых он слабее и сильнее, "
                             "с преимуществом и числом матчей, на котором оно основано.",
        "games_for":         "{games} игр {period}",
        "saved_ago":         "сохранено {age} назад",
        "fresh":             "только что загружено",
        "fav_on":            "В избранном",
        "fav_off":           "В избранное",
        "weak_against":      "{hero} слабее против",
        "strong_against":    "{hero} сильнее против",
        "adv_enemy":         "преимущество соперника",
        "adv_hero":          "преимущество {hero}",
        "nothing_here":      "Героев для показа нет",
        "row_meta":          "винрейт {hero} {wr} · {n} матчей",
        "row_meta_wr":       "винрейт {hero} {wr}",
        "adv_footnote":      "Преимущество — насколько пара выигрывает реже или чаще, чем ожидается по общим "
                             "винрейтам героев. Пары меньше 2000 матчей не показываются.",

        # ── Позиции и роли
        "role_label":        "Позиция",
        "role_any":          "Любая",
        "role_carry":        "Керри",
        "role_support":      "Саппорт",
        "role_initiator":    "Инициатор",
        "role_disabler":     "Контроль",
        "role_nuker":        "Нюкер",
        "role_durable":      "Стойкий",
        "role_escape":       "Побег",
        "role_pusher":       "Пуш",
        "role_more":         "Ещё",
        "role_pos1":         "Керри",
        "role_pos2":         "Мид",
        "role_pos3":         "Тройка",
        "role_pos4":         "Четвёрка",
        "role_pos5":         "Пятёрка",

        # ── Подбор под свободные позиции
        "fill_on":           "Под свободные позиции: {positions}",
        "fill_all":          "показать всех",
        "fill_off":          "Все позиции",
        "fill_only":         "только свободные позиции",
        "fill_theirs":       "Под свободные позиции противника: {positions}",

        # ── Драфт
        "draft_row_enemies": "Противник",
        "draft_row_allies":  "Своя команда",
        "draft_row_bans":    "Баны",
        "draft_moved":       "{hero} перенесён: {group}",
        "draft_full_group":  "Здесь не больше {max}",
        "draft_missing":     "Загружаются: {heroes}",
        "draft_dup":         "{hero} уже в списке",
        "draft_nothing":     "Подбирать не из чего: полной таблицы матчапов у этих героев нет.",
        "draft_failed":      "{hero}: {detail}",
        "draft_skipped":     "Нет полной таблицы матчапов: {heroes}. Они не учтены.",
        "draft_add":         "Добавить героя",
        "draft_to_enemies":  "Противник",
        "draft_to_allies":   "Своя команда",
        "draft_to_bans":     "Бан",
        "draft_next_enemies": "Следующий пик противника",
        "draft_next_allies": "Следующий пик союзника",
        "draft_no_bans":     "Банов пока нет",
        "draft_ban_hint":    "Щелчок по бану — убрать",
        "draft_retry":       "Повторить",
        "draft_empty_title": "Добавьте героев противника",
        "draft_empty_text":  "Подсказки появятся сразу после первого врага. Своя команда и баны из подсказок "
                             "исключаются.",
        "draft_pick_title":  "Брать",
        "draft_against":     "против {heroes}",
        "draft_avoid_title": "Не брать",
        "draft_footnote2":   "Сумма преимуществ над противниками. Матчей — в самой редкой паре; пары меньше 2000 "
                             "матчей считаются нулём.",
        "col_hero":          "Герой",
        "col_sum":           "Сумма",
        "col_matches":       "Матчей",
        "draft_open":        "Свободны: {positions}",
        "draft_all_covered": "Все позиции закрыты",

        # ── Captains Mode
        "side_radiant":      "Radiant",
        "side_dire":         "Dire",
        "cm_we_play":        "Мы играем за",
        "cm_first":          "Первым ходит",
        "cm_you":            " · вы",
        "cm_undo":           "Отменить ход",
        "cm_reset":          "Сбросить",
        "cm_ban":            "БАН",
        "cm_pick":           "ПИК",
        "cm_your_ban":       "Ваш бан",
        "cm_your_pick":      "Ваш пик",
        "cm_their_ban":      "Бан {side}",
        "cm_their_pick":     "Пик {side}",
        "cm_done":           "Драфт окончен",
        "cm_done_hint":      "Все 24 хода сделаны. «Сбросить» — начать заново.",
        "cm_step":           "Ход {n} из {total} · {phase}",
        "cm_phase_ban":      "фаза банов {n}",
        "cm_phase_pick":     "фаза пиков {n}",
        "cm_next":           "Дальше: {steps}",
        "cm_entry_ban":      "Кого забанили на ходу {n}",
        "cm_entry_pick":     "Кого выбрали на ходу {n}",
        "cm_ban_title":      "Кого забанить",
        "cm_pick_title":     "Ваш пик",
        "cm_pick_at":        "Ваш пик на ходу {n}",
        "cm_ban_why":        "сильнее всех против ваших пиков: {heroes}",
        "cm_pick_why":       "против их пиков: {heroes}",
        "cm_failed":         "Не загрузились: {heroes}",
        "cm_taken":          "{hero} уже забанен или выбран",
        "cm_undone":         "Отменено: {hero}",
        "cm_footnote":       "Забаненные и взятые герои в подсказки не попадают. Матчей — в самой редкой паре. "
                             "Порядок ходов — Captains Mode 7.41.",

        # ── Мета: баны до своих пиков
        "meta_why":          "сильнейшие в мете по винрейту — среди тех, кого берут от {pick}% игр, за "
                             "месяц",
        "meta_pick":         "берут в {pick} игр",
        "meta_failed":       "Не удалось загрузить мету: {detail}",
        "ov_meta":           "мета · {rank}",
        "meta_pick_why":     "противник ещё никого не взял — сильнейшие в мете под ваши свободные "
                             "позиции, среди тех, кого берут от {pick}% игр",
        "ov_we":             "Мы",
        "ov_first":          "Первые",

        # ── Оценка драфта
        "view_picks":        "Подбор",
        "view_eval":         "Оценка драфта",
        "eval_empty":        "Оценка появится, когда у обеих команд будет хотя бы по герою.",
        "eval_ours":         "Ваша команда",
        "eval_you":          "{side} (вы)",
        "eval_theirs":       "Противник",
        "eval_score":        "{team} сильнее по матчапам: {value}",
        "eval_score_why":    "сумма преимуществ по всем {n} парам, делённая на 5 — каждый герой играет "
                             "против пятерых. Это перевес по матчапам, а не вероятность победы.",
        "eval_meta":         "Винрейт героев в мете ({rank}): {ours} против {theirs}",
        "eval_unknown":      "Пока нет данных о матчапах: {heroes}",
        "eval_best":         "Выгодные пары",
        "eval_worst":        "Опасные пары",
        "eval_no_pairs":     "нет",
        "eval_lanes":        "Линии",
        "eval_lane_vs":      "{ours} против {theirs}",
        "lane_safe":         "Ваша лёгкая линия",
        "lane_mid":          "Мид",
        "lane_off":          "Ваша сложная линия",
        "eval_footnote":     "Значение пары — от Dotabuff за всю игру, а не только за стадию линий. Линии — "
                             "по позициям, на которые программа расставила каждую команду.",
        "rank_all":          "Все ранги",
        "rank_herald":       "Crusader и ниже (до 2K)",
        "rank_archon":       "Archon (2–3K)",
        "rank_legend":       "Legend (3–4K)",
        "rank_ancient":      "Ancient (4–5K)",
        "rank_divine":       "Divine и Immortal (5K+)",
        "rank_short_all":    "Все ранги",
        "rank_short_herald": "До 2K",
        "rank_short_archon": "Archon",
        "rank_short_legend": "Legend",
        "rank_short_ancient": "Ancient",
        "rank_short_divine": "Divine+",
        "cm_hint_games":     "{n} матчей",

        # ── Оверлей
        "ov_key_busy":       "{key} занята",
        "ov_counters":       "Контрпики",
        "ov_draft":          "All Pick",
        "ov_hint_counters":  "Имя героя, затем Enter",
        "ov_hint_draft":     "Герой, затем Enter — в выбранный список",
        "ov_draft_empty":    "Добавляйте врагов по мере пиков",
        "ov_clear":          "Сбросить",
        "ov_not_found":      "Нет героя «{hero}»",
        "ov_network":        "Dotabuff не отвечает",
        "ov_layout":         "Dotabuff изменил страницу",
        "ov_failed":         "{hero}: не загрузился",
        "ov_nothing":        "Подбирать не из чего",
        "ov_pick":           "Брать",
        "ov_avoid":          "Не брать",
        "ov_footer":         "{key} — показать / скрыть  ·  Esc — скрыть",
        "ov_group_enemies":  "Враг",
        "ov_group_allies":   "Союз",
        "ov_group_bans":     "Бан",
        "ov_cm":             "Captains Mode",
        "ov_step":           "ход {n} из {total}",
        "ov_against":        "против {heroes}",
        "ov_any":            "Все",

        # ── Считывание с экрана
        "scr_off":           "Читать с экрана",
        "scr_on":            "Читаю экран ✓",
        "scr_hint":          "Программа сама узнаёт героев на экране драфта Dota. Нужен режим «В окне» или «В окне без рамки».",
        "scr_loading":       "Готовлю портреты героев…",
        "scr_portraits_failed": "Не удалось загрузить портреты героев — проверьте сеть",
        "scr_missing":       "Dota 2 не запущена",
        "scr_minimized":     "Dota 2 свёрнута",
        "scr_black":         "Изображение игры чёрное — включите в Dota режим «В окне без рамки»",
        "scr_idle":          "Откройте «Драфт» или Captains Mode — здесь или в оверлее",
        "scr_no_draft":      "Жду экран драфта",
        "scr_watching":      "Слежу за драфтом · узнано героев: {n}",
        "scr_side_unknown":  "Не видно, за какую сторону вы играете",
        "scr_conflict":      "Ход {n}: на экране {screen}, а записан {model}",
        "scr_error":         "Ошибка считывания: {detail}",
        "scr_ask_slot":      "{side} {n} — кто это?",
        "scr_ask_move":      "Ход {n} — кто это?",
        "scr_other":         "другой…",

        # ── Список героев
        "hb_title":          "Все герои",
        "hb_sorted":         "героев  ·  по алфавиту",
        "hb_search_ph":      "  Поиск героя…",
        "hb_showing":        "Показано",
        "hb_of":             "из",
        "hb_heroes":         "героев",
        "hb_no_match":       "\n"
                             "  Герои не найдены.\n",

        # ── Изменения патча
        "pn_source":         "  dota2.com  ·  изменения патча",
        "pn_window_title":   "Изменения патча {version}",
        "pn_filter_ph":      "  Фильтр по герою или предмету…",
        "pn_loading":        "\n"
                             "  ⟳  Загрузка изменений патча {version}…\n",
        "pn_empty":          "\n"
                             "  ✕  Изменения патча недоступны.\n",
        "pn_empty_hint":     "\n"
                             "  Данные по патчу {version} могли ещё не выйти.\n",
        "pn_status":         "разделов: {sections}  ·  изменений: {notes}",
        "pn_status_empty":   "разделов: 0",
        "pn_general":        "Общее",
        "pn_items":          "Предметы",
        "pn_neutral":        "Нейтральные предметы",
        "pn_creeps":         "Нейтральные крипы",
        "pn_title":          "Патч {patch}",

        # ── Настройки
        "set_cache_head":    "Данные",
        "set_cache_info":    "Сохранено героев: {n}. Страница хранится 24 часа и загружается заново после нового "
                             "патча.",
        "set_cache_clear":   "Очистить",
        "set_cache_cleared": "Удалено: {n}. Следующий поиск загрузит свежие страницы.",
        "set_hotkey_head":   "Оверлей",
        "set_hotkey_sub":    "Показывает и прячет оверлей поверх игры",
        "set_hotkey_busy":   "{key} занята другой программой — оставлена {old}",
        "set_hotkey_ok":     "Клавиша оверлея: {key}",
        "set_hotkey_custom": "своя, из dota_config.json",
        "set_about_head":    "О программе",
        "set_look":          "Вид",
        "set_theme":         "Тема",
        "set_lang":          "Язык",
        "set_rows":          "Строк в списках",
        "set_rows_hint":     "Сколько героев показывать в списках и подсказках — от 1 до 12.",
        "set_hotkey":        "Клавиша",
        "set_version":       "DotaCounters {version}",
        "set_about_text":    "Настольный помощник для контрпиков и драфта в Dota 2. Данные матчапов — с Dotabuff, "
                             "изменения патча и роли героев — из datafeed Valve. Проект не связан с Valve "
                             "Corporation.",

        # ── Обновления
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
        "upd_title":         "Обновления",
        "upd_text":          "v2.4\n"
                             "Считывание драфта с экрана — выключатель «Читать с экрана» во вкладках «Драфт», Captains Mode и в оверлее. Раз в секунду программа смотрит в окно Dota и узнаёт героев по портретам: в All Pick — по верхней полосе (своих и врагов отличает по вашему имени), в Captains Mode — по доске, вместе с банами, первым ходом и вашей стороной. Герой записывается, только когда несколько снимков подряд согласны; герой, которого игрок лишь навёл, — не пик.\n"
                             "Неуверенного героя программа никогда не подставляет: в такой клетке — вопрос и три кандидата на один щелчок. Подтверждённая клетка запоминается, и герой в наборе, не похожий на свой портрет, в следующий раз узнаётся.\n"
                             "Работает, когда Dota в окне или в окне без рамки: в полноэкранном исключительном режиме Windows не даёт другим программам видеть игру.\n"
                             "\n"
                             "v2.3\n"
                             "Оценка драфта — во вкладках «Драфт» и «Captains Mode», рядом с подсказками: какая команда сильнее по матчапам и насколько, таблица «каждый против каждого», выгодные и опасные пары, линии по позициям и винрейт героев в мете. После последнего хода Captains Mode открывается сама.\n"
                             "Captains Mode: пока противник никого не взял, пики тоже подсказываются по мете — сильнейшие герои под ваши свободные позиции.\n"
                             "Оверлей в Captains Mode: показывает и кого банить, и кого брать, и позволяет выбрать сторону и первый ход. Оверлей стал выше.\n"
                             "Своя команда в All Pick — пять героев, вместе с вашим: он нужен для оценки.\n"
                             "\n"
                             "v2.2\n"
                             "Captains Mode: баны первой фазы, до любых пиков. Они берутся из меты — сильнейшие по винрейту среди героев, которых берут хотя бы в 5% игр; ранг выбирается рядом со списком и запоминается.\n"
                             "Captains Mode: после первых пиков баны подсказываются под позиции, которых не хватает противнику — керри банить незачем, если он у них уже есть. «показать всех» выключает это.\n"
                             "\n"
                             "v2.1\n"
                             "Позиции в фильтре: Керри, Мид, Тройка, Четвёрка, Пятёрка. У Valve позиций нет, только роли, поэтому они берутся из статистики линий Dotabuff: доля матчей героя на каждой линии и золото, которое он там зарабатывает. Герой попадает в позицию от 20% матчей; у некоторых героев их две или три. Роли Valve — в «Ещё».\n"
                             "В карточке героя — его позиции, а за ними роли.\n"
                             "Подсказки пиков в драфте и Captains Mode — под позиции, которых не хватает вашей команде: программа расставляет ваших героев по позициям и показывает свободные. «показать всех» выключает это; выбранная вручную позиция или роль — тоже.\n"
                             "Позиции героев — под именами в подсказках, в составе драфта и в оверлее.\n"
                             "В оверлее свой ряд позиций: Все, 1–5 — для открытого режима.\n"
                             "Выбранная позиция или роль запоминается между запусками.\n"
                             "Наименьший размер окна теперь 1040×700: в окне меньше обрезались шапка и доска Captains Mode.\n"
                             "Если закрыть изменения патча до того, как они загрузились, в фоне больше не возникает ошибка.\n"
                             "\n"
                             "v2.0\n"
                             "Новый интерфейс: спокойные графитовые цвета вместо неона, читаемый шрифт, портреты героев вместо текстовых списков. Преимущество — числом и полосой, винрейт и число матчей — серым под именем. Есть и светлая тема.\n"
                             "Чёткий текст при масштабе Windows 125–200%: раньше система растягивала программу как картинку, и мелкий текст был мыльным.\n"
                             "Captains Mode: отдельная вкладка с полным порядком из 24 банов и пиков. Вводите героев по очереди — программа показывает, чей ход, кого банить против ваших пиков и кого брать против их пиков.\n"
                             "Драфт: команда противника, своя команда и баны рядом, с портретами; таблица подсказок с колонкой на каждого врага.\n"
                             "Период: данные за последнюю неделю, месяц или весь патч — переключатель в шапке. За весь патч матчей примерно впятеро больше, цифры стабильнее; неделя показывает свежие правки баланса. Выбор запоминается.\n"
                             "У каждой строки — сколько матчей сыграно в паре, то есть на чём основана цифра. В драфте — матчей в самой редкой паре героя с противниками.\n"
                             "Изменения патча открываются по номеру патча рядом с названием программы, обновления и история изменений — в «Настройках». Оверлей получил тот же вид и режим Captains Mode.\n"
                             "\n"
                             "v1.8\n"
                             "Поиск: фильтр по роли — например, кто из саппортов сильнее против Pudge. Смена роли перерисовывает результат без новой загрузки.\n"
                             "Редкие матчапы больше не сбивают: пары, сыгранные меньше 2000 раз, в списки не попадают, а в драфте считаются нулём. Это в основном пары с Chen, Batrider, Elder Titan, Lycan, Visage и Brewmaster.\n"
                             "Страницы Dotabuff хранятся сутки в папке cache рядом с программой: повторный поиск и драфт — мгновенно, а отказов от Dotabuff меньше. После нового патча страницы загружаются заново. В настройках видно, сколько сохранено, и есть кнопка очистки.\n"
                             "Иконки героев больше не пропадают: после поиска и драфта на вкладке «Поиск» вместо иконок оставались пустые места, и наоборот.\n"
                             "\n"
                             "v1.7\n"
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
