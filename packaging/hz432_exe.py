"""Entry point for the standalone Windows build (PyInstaller)."""

import multiprocessing
import sys

from hz432 import main

if __name__ == "__main__":
    # Required for worker processes (-j) in a frozen executable on Windows.
    multiprocessing.freeze_support()
    sys.exit(main())
