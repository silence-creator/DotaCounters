"""Точка входа DotaCounters.

Вся логика живёт в пакете dotacounters/; здесь только запуск окна.
"""

import tkinter as tk

from dotacounters.ui import DotaApp


def main():
    root = tk.Tk()
    DotaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
