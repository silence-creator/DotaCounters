"""Глобальная горячая клавиша: срабатывает, даже когда активна игра.

Регистрируется через RegisterHotKey из user32. Сообщение WM_HOTKEY приходит в
очередь того потока, который регистрировал клавишу, поэтому у клавиши свой
поток с циклом GetMessage. Колбэк вызывается из этого потока — интерфейс
должен переправить его в главный через root.after.

Разбор строки вида «ctrl+shift+d» отделён от регистрации и проверяется тестами
на любой платформе. Вне Windows регистрация просто не удаётся.
"""

import sys
import threading

DEFAULT_HOTKEY = "ctrl+shift+d"

MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN = 0x1, 0x2, 0x4, 0x8
#: Не повторять срабатывание, пока клавиша зажата.
MOD_NOREPEAT = 0x4000
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012

_MODIFIERS = {"ctrl": MOD_CONTROL, "control": MOD_CONTROL, "shift": MOD_SHIFT,
              "alt": MOD_ALT, "win": MOD_WIN}
_MOD_ORDER = (("ctrl", MOD_CONTROL), ("alt", MOD_ALT), ("shift", MOD_SHIFT), ("win", MOD_WIN))
_NAMED_KEYS = {"space": 0x20, "tab": 0x09, "home": 0x24, "end": 0x23,
               "insert": 0x2D, "pageup": 0x21, "pagedown": 0x22}


def _key_code(name: str) -> int:
    if len(name) == 1 and (name.isascii() and name.isalnum()):
        return ord(name.upper())           # коды букв и цифр совпадают с ASCII
    if name in _NAMED_KEYS:
        return _NAMED_KEYS[name]
    if name.startswith("f") and name[1:].isdigit() and 1 <= int(name[1:]) <= 24:
        return 0x70 + int(name[1:]) - 1    # F1 = 0x70
    raise ValueError("неизвестная клавиша: %s" % name)


def parse_hotkey(text: str) -> tuple:
    """«ctrl+shift+d» -> (модификаторы, код клавиши). Ошибка — ValueError.

    Без модификатора годятся только F-клавиши: иначе обычная буква
    перестала бы печататься во всех программах.
    """
    parts = [p.strip().lower() for p in str(text or "").split("+") if p.strip()]
    if not parts:
        raise ValueError("пустая комбинация")
    mods = 0
    for part in parts[:-1]:
        if part not in _MODIFIERS:
            raise ValueError("неизвестный модификатор: %s" % part)
        mods |= _MODIFIERS[part]
    key = parts[-1]
    if key in _MODIFIERS:
        raise ValueError("нет основной клавиши")
    vk = _key_code(key)
    if not mods and not 0x70 <= vk <= 0x87:
        raise ValueError("без Ctrl, Alt или Shift можно только F-клавиши")
    return mods, vk


def format_hotkey(text: str) -> str:
    """«ctrl+shift+d» -> «Ctrl+Shift+D» для подписи в интерфейсе."""
    mods, _ = parse_hotkey(text)
    key = str(text).split("+")[-1].strip()
    names = [name.capitalize() for name, flag in _MOD_ORDER if mods & flag]
    return "+".join(names + [key.upper() if len(key) <= 3 else key.capitalize()])


class GlobalHotkey:
    """Горячая клавиша на всю систему. start() -> удалось ли её занять."""

    _ID = 1

    def __init__(self, text: str, callback):
        self.mods, self.vk = parse_hotkey(text)
        self.callback = callback
        self._thread = None
        self._thread_id = None
        self._ready = threading.Event()
        self._ok = False

    def start(self, timeout: float = 2.0) -> bool:
        if sys.platform != "win32":
            return False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout)
        return self._ok

    def stop(self) -> None:
        if self._thread_id is not None:
            import ctypes
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)

    def _run(self):
        import ctypes
        from ctypes import wintypes
        user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()
        # Занята другой программой — RegisterHotKey вернёт 0.
        self._ok = bool(user32.RegisterHotKey(None, self._ID, self.mods | MOD_NOREPEAT, self.vk))
        self._ready.set()
        if not self._ok:
            self._thread_id = None
            return
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY and msg.wParam == self._ID:
                    try:
                        self.callback()
                    except Exception:
                        pass  # сбой в интерфейсе не должен убить цикл клавиши
        finally:
            user32.UnregisterHotKey(None, self._ID)
