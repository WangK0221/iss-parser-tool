from __future__ import annotations

import tkinter as tk

from tools.license_generator_gui import LicenseGeneratorWindow
from utils.logger import setup_logger


def main() -> None:
    setup_logger()
    root = tk.Tk()
    LicenseGeneratorWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
