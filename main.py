# main.py
"""Codex Transfer - Entry point with single-instance detection."""
from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from pathlib import Path

# Windows single-instance constants
MUTEX_NAME = "CodexTransfer_SingleInstance"
ERROR_ALREADY_EXISTS = 183


def check_single_instance() -> bool:
    """Check if another instance is already running.

    Returns True if this is the only instance, False if another exists.
    """
    if sys.platform != "win32":
        return True

    handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == ERROR_ALREADY_EXISTS:
        _activate_existing_window()
        return False

    return True


def _activate_existing_window() -> None:
    """Find and activate the existing Codex Transfer window."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Codex Transfer v1.0.0")
        if hwnd:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def main() -> None:
    """Application entry point."""
    if not check_single_instance():
        sys.exit(0)

    # DPI 自适应：让应用在不同分辨率屏幕上正常显示
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    # Late imports to speed up single-instance check
    import ttkbootstrap as ttk

    from core.config import Config
    from ui.theme import get_theme_name
    from ui.app import CodexTransferApp

    config = Config()
    theme_name = get_theme_name(config.theme)

    root = ttk.Window(themename=theme_name)
    # 立即隐藏窗口，避免小窗口闪烁
    root.withdraw()

    icon_path = Path(__file__).parent / "assets" / "icon.ico"
    if icon_path.exists():
        root.iconbitmap(str(icon_path))

    app = CodexTransferApp(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
