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
        "--onefile",
        "--windowed",
        "--name", "CodexTransfer",
        "--clean",
    ]

    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
        # 把图标文件打包进 bundle，运行时可通过 sys._MEIPASS 访问
        cmd.extend(["--add-data", f"{icon_path};assets"])

    cmd.extend([
        "--hidden-import", "ttkbootstrap",
        "--hidden-import", "PIL",
        "--hidden-import", "sqlite3",
    ])

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
