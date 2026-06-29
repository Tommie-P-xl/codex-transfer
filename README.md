# Codex Transfer

<p align="center">
  <img src="assets/icon.ico" width="128" alt="Codex Transfer Logo">
</p>

<p align="center">
  <strong>Lightweight Windows desktop tool for managing Codex chat history</strong>
</p>

<p align="center">
  English | <a href="README_CN.md">中文</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.4.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="License">
</p>

---

## Overview

Codex Transfer is a lightweight Windows desktop tool for [OpenAI Codex](https://github.com/openai/codex) users. It reads the local Codex chat database, displays all session records in a sortable table, and supports batch migration, copying, and deletion.

**Core Problem Solved:** When switching between multiple `model_provider` keys (e.g., openai → packycode → xychatai), older chat records become invisible in Codex due to provider key mismatch. Codex Transfer unifies these records under a single provider, restoring history visibility.

## Features

| Feature | Description |
|---------|-------------|
| 📋 **Browse** | View all Codex chats with title, timestamp, project path, and provider |
| 🔍 **Multi-filter** | Filter by provider, project path, or title keyword |
| 📦 **Batch Move** | Migrate selected records to an existing or new provider |
| 📋 **Batch Copy** | Copy selected records with auto-sync to `session_index.jsonl` |
| 🗑️ **Batch Delete** | Remove selected records (files + database) |
| 🔄 **Check Updates** | Check GitHub Releases and open the latest download page |
| 🧹 **Stale Filtering** | Hide database rows whose JSONL files no longer exist |
| 🏷️ **Title Sync** | Prefer Codex sidebar titles from `session_index.jsonl` |
| 🌙 **Theme Sync** | Auto-detect Windows dark/light theme |
| 🔒 **Single Instance** | Prevent multiple windows, activate existing on re-launch |
| 🖥️ **DPI Aware** | Auto-detect DPI scaling (100%–200%), supports any resolution from 1366×768 to 3840×2160 |
| 📏 **Responsive Layout** | Filter bar and action bar use grid layout, components stretch automatically |
| 📊 **Dynamic Columns** | Table columns adjust based on window size |
| 📐 **Center Aligned** | All column content is center-aligned |
| ☑️ **Dynamic Checkbox** | Checkbox header reflects selection state in real-time |
| 📐 **Portable** | Single exe, no installation, ~6–9MB (Nuitka build) |

## Quick Start

### Option 1: Download exe (Recommended)

1. Download `CodexTransfer.exe` from [Releases](https://github.com/Tommie-P-xl/codex-transfer/releases)
2. Double-click to run, no installation needed

### Option 2: Run from source

```bash
git clone https://github.com/Tommie-P-xl/codex-transfer.git
cd codex-transfer
pip install ttkbootstrap Pillow
python main.py
```

### Option 3: Build exe

```bash
pip install -r requirements.txt
python build.py
# Output: dist/CodexTransfer.exe
```

### GitHub Actions

- Push a `v*` tag to auto-build `CodexTransfer.exe` on `windows-latest`
- Build artifacts are uploaded as Actions artifacts
- Tag builds auto-attach `dist/CodexTransfer.exe` to the GitHub Release

## Configuration

| Item | Default | Description |
|------|---------|-------------|
| Codex Path | `~/.codex` | Changeable via UI, persisted in `%APPDATA%/CodexTransfer/config.json` |
| Theme | `auto` | `auto` follows system / `dark` / `light` |
| Window Size | `960x620` | Auto-saved on close |

### Codex Data Directory

```
~/.codex/
├── state_*.sqlite          # Session metadata (threads table)
├── sessions/               # Session content (JSONL files)
│   └── YYYY/MM/DD/
│       └── rollout-*.jsonl
└── archived_sessions/      # Archived sessions
```

## Project Structure

```
CodexTransfer/
├── main.py                 # Entry: single-instance + DPI + launch UI
├── core/
│   ├── config.py           # Config management (%APPDATA% persistence)
│   ├── database.py         # SQLite CRUD (threads table)
│   └── rollout.py          # JSONL file operations (rewrite/copy/delete)
├── ui/
│   ├── app.py              # Main window (filter/table/actions/status)
│   ├── theme.py            # Windows theme detection (registry)
│   └── widgets.py          # Custom widgets (CheckboxTreeview)
├── assets/
│   └── icon.ico            # App icon (multi-size ICO)
├── .github/workflows/
│   └── build-release.yml   # GitHub Actions auto-build
├── build.py                # Nuitka build script
├── requirements.txt        # Dependencies
└── README.md               # This file
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| UI Framework | tkinter + ttkbootstrap |
| Database | sqlite3 (built-in) |
| Icon | Pillow |
| Packaging | Nuitka (native code, smaller, faster) |
| System API | ctypes (Windows DWM / DPI / Mutex) |

## Version History

| Version | Date | Description |
|---------|------|-------------|
| v1.4.0 | 2026-06-30 | **UI Refactor**: Compact single-row action bar; merged move/copy into unified buttons; fixed window sizing for high-DPI displays; improved visual polish |
| v1.3.0 | 2026-06-29 | **DPI Aware**: Supports any resolution (1366×768–3840×2160) and DPI scaling (100%–200%); filter/action bars use responsive grid layout |
| v1.2.0 | 2026-06-29 | **UI Optimization**: Fixed high-DPI UI crowding; screen-ratio adaptive window; dynamic column width, center alignment, row height |
| v1.1.0 | 2026-06-09 | **Size Optimization**: Switched to Nuitka compilation, exe size reduced from ~32MB to ~6–9MB |
| v1.0.0 | 2026-06-07 | **Initial Release**: Browse/filter/move/copy/delete, theme sync, single instance, DPI aware, GitHub Actions |

## License

[MIT License](LICENSE)

## Acknowledgements

- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) — Modern tkinter themes
- [Nuitka](https://nuitka.net/) — Python compiler
- [OpenAI Codex](https://github.com/openai/codex) — The tool this manages
