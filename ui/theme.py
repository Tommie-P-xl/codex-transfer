# ui/theme.py
"""Detect Windows system theme and map to ttkbootstrap theme."""
from __future__ import annotations

import sys


def detect_system_theme() -> str:
    """Detect if Windows is using light or dark theme.

    Returns:
        "darkly" for dark theme, "cosmo" for light theme.
        Defaults to "cosmo" if detection fails.
    """
    if sys.platform != "win32":
        return "cosmo"

    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "darkly" if value == 0 else "cosmo"
    except (OSError, FileNotFoundError):
        return "cosmo"


def get_theme_name(preference: str) -> str:
    """Resolve theme name from user preference.

    Args:
        preference: "auto", "dark", or "light"

    Returns:
        ttkbootstrap theme name ("darkly" or "cosmo")
    """
    if preference == "dark":
        return "darkly"
    if preference == "light":
        return "cosmo"
    return detect_system_theme()
