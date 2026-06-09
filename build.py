"""Build Codex Transfer into a standalone .exe using Nuitka."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def build() -> None:
    project_dir = Path(__file__).parent
    icon_path = project_dir / "assets" / "icon.ico"
    main_script = project_dir / "main.py"

    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--windows-console-mode=disable",
        "--enable-plugin=tk-inter",
        "--include-data-dir=assets=assets",
        "--output-filename=CodexTransfer.exe",
        "--output-dir=" + str(project_dir / "dist"),
    ]

    if icon_path.exists():
        cmd.append(f"--windows-icon-from-ico={icon_path}")

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
