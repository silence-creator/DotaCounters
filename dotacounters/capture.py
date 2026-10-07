"""Снимок окна Dota 2 — только Windows, на других системах окно «не найдено».

Сначала PrintWindow с флагом PW_RENDERFULLCONTENT: Windows отдаёт содержимое
окна целиком, даже если поверх лежит оверлей или другая программа. Если он
вернул чёрный кадр (так бывает с некоторыми способами вывода игры), снимается
экран в границах окна — тогда окно должно быть видно. В полноэкранном
исключительном режиме оба способа дают чёрный кадр: Windows показывает игру
мимо рабочего стола.
"""

import ctypes
import sys
from ctypes import wintypes

from PIL import Image, ImageGrab, ImageStat

#: Заголовок окна игры.
TITLE = "Dota 2"

#: Кадр темнее этого — чёрный: игра в полноэкранном исключительном режиме.
BLACK_LEVEL = 3.0

PW_RENDERFULLCONTENT = 2


class Shot:
    """Итог снимка: status — «ok», «missing» (игра не запущена), «minimized»
    или «black»; image — PIL.Image при «ok»."""

    def __init__(self, status, image=None):
        self.status = status
        self.image = image


def _user32():
    return ctypes.windll.user32 if sys.platform == "win32" else None


def find_window():
    """Окно игры или None. Ищется видимое окно верхнего уровня с заголовком TITLE."""
    user32 = _user32()
    if user32 is None:
        return None
    found = []
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def check(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(64)
            user32.GetWindowTextW(hwnd, buf, 64)
            if buf.value == TITLE:
                found.append(hwnd)
                return False
        return True

    user32.EnumWindows(proto(check), 0)
    return found[0] if found else None


def client_box(hwnd):
    """Внутренняя часть окна (без рамки) в координатах экрана."""
    user32 = _user32()
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    origin = wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(origin))
    return (origin.x, origin.y, origin.x + rect.right, origin.y + rect.bottom)


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


def print_window(hwnd):
    """Содержимое окна через PrintWindow; None, если не вышло."""
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w, h = rect.right, rect.bottom
    if w <= 0 or h <= 0:
        return None
    window_dc = user32.GetDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(window_dc)
    bitmap = gdi32.CreateCompatibleBitmap(window_dc, w, h)
    old = gdi32.SelectObject(mem_dc, bitmap)
    try:
        # 1 — PW_CLIENTONLY: без рамки окна
        if not user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT | 1):
            return None
        header = _BITMAPINFOHEADER()
        header.biSize = ctypes.sizeof(header)
        header.biWidth, header.biHeight = w, -h      # минус — строки сверху вниз
        header.biPlanes, header.biBitCount = 1, 32
        buf = ctypes.create_string_buffer(w * h * 4)
        if not gdi32.GetDIBits(mem_dc, bitmap, 0, h, buf, ctypes.byref(header), 0):
            return None
        return Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1)
    finally:
        gdi32.SelectObject(mem_dc, old)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(hwnd, window_dc)


def is_black(img) -> bool:
    small = img.convert("L").resize((64, 36))
    return ImageStat.Stat(small).mean[0] < BLACK_LEVEL


def grab(hwnd=None) -> Shot:
    """Снимок окна игры. hwnd — уже найденное окно (иначе ищется заново)."""
    if _user32() is None:
        return Shot("missing")
    hwnd = hwnd or find_window()
    if not hwnd or not _user32().IsWindow(hwnd):
        return Shot("missing")
    if _user32().IsIconic(hwnd):
        return Shot("minimized")
    try:
        img = print_window(hwnd)
    except Exception:
        img = None
    if img is None or is_black(img):
        try:
            img = ImageGrab.grab(bbox=client_box(hwnd), all_screens=True)
        except Exception:
            img = None
    if img is None or is_black(img):
        return Shot("black")
    return Shot("ok", img)
