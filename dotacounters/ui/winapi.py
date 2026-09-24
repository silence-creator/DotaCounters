"""Специфика Windows: тёмный заголовок окна через DWM.

На других платформах вызов молча ничего не делает.
"""

import ctypes


def set_title_bar_color(root):
    try:
        root.update()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ctypes.windll.user32.GetParent
        hwnd = get_parent(root.winfo_id())
        value = ctypes.c_int(2)
        set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                             ctypes.byref(value), ctypes.sizeof(value))
    except Exception:
        pass


def bring_to_front(window):
    """Сделать окно активным, даже если сейчас активна другая программа.

    focus -force у Tk для окна без рамки фокус из чужой программы не забирает:
    набранное уходило в игру. SetForegroundWindow Windows разрешает процессу,
    которому пришло последнее нажатие, — после горячей клавиши это мы. Если
    всё же отказано, помогает временно подключиться к вводу активного потока.
    """
    try:
        user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
        hwnd = int(window.wm_frame(), 16)
        if user32.SetForegroundWindow(hwnd):
            return
        other = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
        mine = kernel32.GetCurrentThreadId()
        user32.AttachThreadInput(mine, other, True)
        try:
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
        finally:
            user32.AttachThreadInput(mine, other, False)
    except Exception:
        pass
