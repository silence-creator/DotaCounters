"""Точка входа DotaCounters.

Вся логика живёт в пакете dotacounters/; здесь только запуск окна.
"""

import sys

from dotacounters.relaunch import heal_inherited_launch


def main():
    # До tkinter и сети: если нас запустила старая версия с грязным окружением,
    # эта копия живёт в папке, которую вот-вот удалят, — перезапуститься начисто.
    if heal_inherited_launch():
        sys.exit(0)

    import tkinter as tk

    from dotacounters.ui import DotaApp

    root = tk.Tk()
    DotaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
