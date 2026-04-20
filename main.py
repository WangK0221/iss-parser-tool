from __future__ import annotations

import tkinter as tk

from ui.main_window import MainWindow
from utils.logger import setup_logger


def main() -> None:
    setup_logger()
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
