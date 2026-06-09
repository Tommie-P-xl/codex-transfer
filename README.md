# Codex Transfer v1.1.0

<p align="center">
  <img src="assets/icon.ico" width="128" alt="Codex Transfer Logo">
</p>

<p align="center">
  <strong>轻量级 Windows 桌面应用，用于管理 Codex 聊天历史记录</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="License">
</p>

---

## 📖 项目简介

Codex Transfer 是一款专为 [OpenAI Codex](https://github.com/openai/codex) 用户设计的 Windows 桌面工具。它可以读取 Codex 的本地聊天数据库，以列表形式展示所有会话记录，并支持批量迁移、复制和删除操作。

**解决的核心问题：** 当你更换过多个 model_provider（如 openai → packycode → xychatai）后，旧的聊天记录会因为 provider key 不匹配而无法在 Codex 中正常显示。Codex Transfer 可以将这些记录统一迁移到同一个 provider 下，让历史记录重新可见。

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 📋 **浏览记录** | 以列表形式展示所有 Codex 聊天记录（优先使用 Codex 侧边栏标题、时间、项目路径、归属） |
| 🔍 **多维筛选** | 按归属（model_provider）、项目路径、标题关键字筛选 |
| 📦 **批量移动** | 将选中记录的归属迁移到已有或新建的 provider |
| 📋 **批量复制** | 将选中记录复制到已有或新建的 provider（创建新文件+新记录），自动同步 `session_index.jsonl` 确保 Codex Desktop 可见 |
| 🗑️ **批量删除** | 同时删除选中记录的 JSONL 文件和数据库记录 |
| 🔄 **检查更新** | 从 GitHub Releases 检查最新版本并打开下载页面 |
| 🧹 **残留过滤** | 自动隐藏数据库中仍存在但 JSONL 文件已删除的会话记录 |
| 🏷️ **标题同步** | 优先读取 `session_index.jsonl` 中的会话标题，避免显示第一条长消息 |
| 🔄 **索引同步** | 加载数据时自动同步数据库线程到 `session_index.jsonl`，确保 Codex Desktop 显示所有记录 |
| 🌙 **主题跟随** | 自动跟随 Windows 系统暗色/亮色主题 |
| 🔒 **单实例** | 防止软件多开，重复启动时自动激活已有窗口 |
| 🖥️ **DPI 自适应** | 在不同分辨率屏幕上正常显示 |
| 🖼️ **清晰图标** | 内置多尺寸 ICO，标题栏、任务栏、Alt-Tab 等位置优先使用匹配尺寸 |
| 📐 **轻量便携** | 单文件 exe，无需安装，约 11–14MB（优化后） |

## 🚀 快速开始

### 方式一：直接运行 exe（推荐）

1. 从 [Releases](https://github.com/Tommie-P-xl/codex-transfer/releases) 下载 `CodexTransfer.exe`
2. 双击运行，无需安装

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/Tommie-P-xl/codex-transfer.git
cd codex-transfer

# 安装依赖
pip install ttkbootstrap Pillow

# 运行
python main.py
```

### 方式三：自行构建 exe

```bash
# 安装所有依赖（含打包工具）
pip install -r requirements.txt

# 构建
python build.py

# 生成的 exe 位于 dist/CodexTransfer.exe
```

### GitHub Actions 自动构建

仓库内置 `.github/workflows/build-release.yml`：

- 推送 `v*` 标签时自动在 `windows-latest` 上构建 `CodexTransfer.exe`
- 构建产物会上传为 Actions artifact
- 标签构建会自动把 `dist/CodexTransfer.exe` 附加到对应 GitHub Release
- 也可以在 GitHub Actions 页面通过 `workflow_dispatch` 手动运行构建

## ⚙️ 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| Codex 路径 | `~/.codex` | 可通过 UI 更改，持久化在 `%APPDATA%/CodexTransfer/config.json` |
| 主题 | `auto` | `auto` 跟随系统 / `dark` 暗色 / `light` 亮色 |
| 窗口尺寸 | `900x520` | 自动保存关闭时的窗口大小 |

### Codex 数据目录结构

```
~/.codex/
├── state_*.sqlite          # 会话元数据（threads 表）
├── sessions/               # 会话内容（JSONL 文件）
│   └── YYYY/MM/DD/
│       └── rollout-*.jsonl
└── archived_sessions/      # 已归档会话
```

## 🏗️ 项目结构

```
CodexTransfer/
├── main.py                 # 入口：单实例检测 + DPI 设置 + 启动 UI
├── core/
│   ├── config.py           # 配置管理（%APPDATA% 持久化）
│   ├── database.py         # SQLite 读写（threads 表 CRUD）
│   └── rollout.py          # JSONL 文件操作（改写/复制/删除）
├── ui/
│   ├── app.py              # 主窗口（筛选/列表/操作/状态栏）
│   ├── theme.py            # Windows 主题检测（注册表读取）
│   └── widgets.py          # 自定义组件（CheckboxTreeview）
├── assets/
│   └── icon.ico            # 应用图标（16/20/24/32/40/48/64/128/256 多尺寸）
├── .github/workflows/
│   └── build-release.yml   # GitHub Actions 自动构建和发布
├── hooks/
│   └── hook-ttkbootstrap.py  # PyInstaller hook：排除未用主题资源
├── build.py                # PyInstaller 打包脚本（含 UPX/排除优化）
├── requirements.txt        # 依赖清单
└── README.md               # 本文档
```

## 🔧 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| UI 框架 | tkinter + ttkbootstrap |
| 数据库 | sqlite3（内置） |
| 图标处理 | Pillow |
| 打包 | PyInstaller |
| 系统 API | ctypes（Windows DWM / DPI / Mutex） |

## 📝 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1.0 | 2026-06-09 | **EXE 体积优化**：通过 UPX 压缩、排除无用标准库模块、精确 PIL 导入、ttkbootstrap 主题资源裁剪，体积从 ~32MB 降至 ~11–14MB，功能零损失。新增自定义 PyInstaller hooks 目录 |
| v1.0.0 | 2026-06-07 | **修复复制功能**：复制线程后 Codex Desktop 无法显示的问题。根因：(1) `session_index.jsonl` 未同步新线程 ID；(2) 复制文件名格式不符合 Codex Desktop 预期。新增 `_sync_session_index()` 加载时自动补全索引 |
| v1.0.0 | 2026-06-07 | 修复新归属弹窗自适应与闪烁，优化运行时图标清晰度，新增检查更新、残留会话过滤和 GitHub Actions 自动构建 |
| v1.0.0 | 2026-06-07 | 初始版本：浏览/筛选/移动/复制/删除，主题跟随，单实例，DPI 自适应 |

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 🙏 致谢

- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) — 现代 tkinter 主题
- [PyInstaller](https://pyinstaller.org/) — Python 打包工具
- [OpenAI Codex](https://github.com/openai/codex) — 本工具的管理对象

---

# English Version

## Overview

Codex Transfer is a lightweight Windows desktop tool for [OpenAI Codex](https://github.com/openai/codex) users. It reads the local Codex chat database, displays all session records in a sortable table, and supports batch migration, copying, and deletion.

**Core Problem Solved:** When switching between multiple `model_provider` keys (e.g., openai → packycode → xychatai), older chat records become invisible in Codex due to provider key mismatch. Codex Transfer unifies these records under a single provider, restoring history visibility.

## Features

- **Browse** — View all Codex chats with title, timestamp, project path, and provider
- **Filter** — Filter by provider, project path, or title keyword
- **Batch Move** — Migrate selected records to an existing or new provider
- **Batch Copy** — Copy selected records (new JSONL files + new DB records), auto-sync `session_index.jsonl` for Codex Desktop compatibility
- **Index Sync** — Auto-sync database threads to `session_index.jsonl` on load, ensuring all records visible in Codex Desktop
- **Batch Delete** — Remove selected records (files + database)
- **Check Updates** — Check GitHub Releases and open the latest download page
- **Stale Record Filtering** — Hide database rows whose JSONL rollout files no longer exist
- **Title Sync** — Prefer Codex sidebar titles from `session_index.jsonl` to avoid showing long first messages
- **Theme Sync** — Auto-detect Windows dark/light theme
- **Single Instance** — Prevent multiple windows, activate existing on re-launch
- **DPI Aware** — Scales correctly on high-DPI displays
- **Crisp Icons** — Multi-size ICO for clearer title bar, taskbar, and Alt-Tab icons
- **Portable** — Single exe, no installation, ~11–14MB (optimized)

## Quick Start

**Download exe:** Get `CodexTransfer.exe` from [Releases](https://github.com/Tommie-P-xl/codex-transfer/releases) and double-click.

**From source:**
```bash
git clone https://github.com/Tommie-P-xl/codex-transfer.git
cd codex-transfer
pip install ttkbootstrap Pillow
python main.py
```

**Build exe:**
```bash
pip install -r requirements.txt
python build.py
# Output: dist/CodexTransfer.exe
```

## Tech Stack

Python 3.10+ / tkinter + ttkbootstrap / sqlite3 / Pillow / PyInstaller / ctypes (Windows API)

## License

[MIT License](LICENSE)
