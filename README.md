# Codex Transfer v1.0.0

<p align="center">
  <img src="assets/icon.ico" width="128" alt="Codex Transfer Logo">
</p>

<p align="center">
  <strong>轻量级 Windows 桌面应用，用于管理 Codex 聊天历史记录</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.0.0-blue" alt="Version">
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
| 📋 **浏览记录** | 以列表形式展示所有 Codex 聊天记录（标题、时间、项目路径、归属） |
| 🔍 **多维筛选** | 按归属（model_provider）、项目路径、标题关键字筛选 |
| 📦 **批量移动** | 将选中记录的归属迁移到已有或新建的 provider |
| 📋 **批量复制** | 将选中记录复制到已有或新建的 provider（创建新文件+新记录） |
| 🗑️ **批量删除** | 同时删除选中记录的 JSONL 文件和数据库记录 |
| 🌙 **主题跟随** | 自动跟随 Windows 系统暗色/亮色主题 |
| 🔒 **单实例** | 防止软件多开，重复启动时自动激活已有窗口 |
| 🖥️ **DPI 自适应** | 在不同分辨率屏幕上正常显示 |
| 📐 **轻量便携** | 单文件 exe，无需安装，约 32MB |

## 🚀 快速开始

### 方式一：直接运行 exe（推荐）

1. 从 [Releases](../../releases) 下载 `CodexTransfer.exe`
2. 双击运行，无需安装

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/codex-transfer.git
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
│   ├── icon.ico            # 应用图标（16/32/48/256 多尺寸）
│   └── convert_icon.py     # PNG → ICO 转换脚本
├── tests/                  # 单元测试（25 个测试用例）
├── build.py                # PyInstaller 打包脚本
├── requirements.txt        # 依赖清单
└── README.md               # 本文档
```

## 🧪 运行测试

```bash
pip install pytest
python -m pytest tests/ -v
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
- **Batch Copy** — Copy selected records (new JSONL files + new DB records)
- **Batch Delete** — Remove selected records (files + database)
- **Theme Sync** — Auto-detect Windows dark/light theme
- **Single Instance** — Prevent multiple windows, activate existing on re-launch
- **DPI Aware** — Scales correctly on high-DPI displays
- **Portable** — Single exe, no installation, ~32MB

## Quick Start

**Download exe:** Get `CodexTransfer.exe` from [Releases](../../releases) and double-click.

**From source:**
```bash
git clone https://github.com/YOUR_USERNAME/codex-transfer.git
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
