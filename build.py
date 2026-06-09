"""Build Codex Transfer into a standalone .exe using PyInstaller."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def build() -> None:
    project_dir = Path(__file__).parent
    icon_path = project_dir / "assets" / "icon.ico"
    main_script = project_dir / "main.py"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed",
        "--name", "CodexTransfer", "--clean",
        # Point to custom hooks directory (Step 2)
        "--additional-hooks-dir", str(project_dir / "hooks"),
    ]

    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
        cmd.extend(["--add-data", f"{icon_path};assets"])

    # Precise hidden imports (Step 1: avoid bundling entire PIL)
    cmd.extend([
        "--hidden-import", "ttkbootstrap",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageTk",
        "--collect-submodules", "PIL",
        "--hidden-import", "sqlite3",
    ])

    # Exclude unused standard library modules (Step 1: save ~3-5 MB)
    excludes = [
        "email",    "html",         "xml",       "unittest",
        "distutils", "pydoc",        "doctest",   "difflib",
        "multiprocessing", "concurrent", "asyncio",
        "http",      "xmlrpc",       "ftplib",
        "imaplib",   "poplib",       "smtplib",   "telnetlib",
        "turtle",    "curses",       "antigravity", "this",
    ]
    for m in excludes:
        cmd.extend(["--exclude-module", m])

    # UPX compression (Step 1: install UPX and set path)
    upx_path = Path(r"C:\tools\upx")
    if upx_path.exists():
        cmd.extend(["--upx-dir", str(upx_path)])

    cmd.append(str(main_script))

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(project_dir))

    if result.returncode == 0:
        exe_path = project_dir / "dist" / "CodexTransfer.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\nBuild successful: {exe_path} ({size_mb:.1f} MB)")
        else:
            print("\nBuild completed but exe not found at expected path")
    else:
        print(f"\nBuild failed with exit code {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    build()
