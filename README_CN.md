# Codex Transfer

<p align="center">
  <img src="assets/icon.ico" width="128" alt="Codex Transfer Logo">
</p>

<p align="center">
  <strong>轻量级 Windows 桌面应用，用于管理 Codex 聊天历史记录</strong>
</p>

<p align="center">
  <a href="README.md">English</a> | 中文
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.4.0-blue" alt="Version">
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
| 📋 **批量复制** | 将选中记录复制到已有或新建的 provider，自动同步 `session_index.jsonl` 确保 Codex Desktop 可见 |
| 🗑️ **批量删除** | 同时删除选中记录的 JSONL 文件和数据库记录 |
| 🔄 **检查更新** | 从 GitHub Releases 检查最新版本并打开下载页面 |
| 🧹 **残留过滤** | 自动隐藏数据库中仍存在但 JSONL 文件已删除的会话记录 |
| 🏷️ **标题同步** | 优先读取 `session_index.jsonl` 中的会话标题，避免显示第一条长消息 |
| 🌙 **主题跟随** | 自动跟随 Windows 系统暗色/亮色主题 |
| 🔒 **单实例** | 防止软件多开，重复启动时自动激活已有窗口 |
| 🖥️ **DPI 感知自适应** | 自动检测系统 DPI 缩放比例（100%–200%），支持任意分辨率（1366×768 到 3840×2160） |
| 📏 **弹性布局** | 筛选栏和操作栏使用 grid 布局，组件能根据窗口大小自动伸缩 |
| 📊 **动态列宽** | 表格列宽根据窗口大小动态调整，项目路径等长文本自动适应 |
| ☑️ **动态勾选** | 复选框标题栏支持动态勾选状态显示，实时反映选中数量 |
| 📐 **轻量便携** | 单文件 exe，无需安装，约 6–9MB（Nuitka 编译） |

## 🚀 快速开始

### 方式一：直接运行 exe（推荐）

1. 从 [Releases](https://github.com/Tommie-P-xl/codex-transfer/releases) 下载 `CodexTransfer.exe`
2. 双击运行，无需安装

### 方式二：从源码运行

```bash
git clone https://github.com/Tommie-P-xl/codex-transfer.git
cd codex-transfer
pip install ttkbootstrap Pillow
python main.py
```

### 方式三：自行构建 exe

```bash
pip install -r requirements.txt
python build.py
# 生成的 exe 位于 dist/CodexTransfer.exe
```

### GitHub Actions 自动构建

- 推送 `v*` 标签时自动在 `windows-latest` 上构建 `CodexTransfer.exe`
- 构建产物会上传为 Actions artifact
- 标签构建会自动把 `dist/CodexTransfer.exe` 附加到对应 GitHub Release

## ⚙️ 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| Codex 路径 | `~/.codex` | 可通过 UI 更改，持久化在 `%APPDATA%/CodexTransfer/config.json` |
| 主题 | `auto` | `auto` 跟随系统 / `dark` 暗色 / `light` 亮色 |
| 窗口尺寸 | `960x620` | 自动保存关闭时的窗口大小 |

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
│   └── icon.ico            # 应用图标（多尺寸 ICO）
├── .github/workflows/
│   └── build-release.yml   # GitHub Actions 自动构建和发布
├── build.py                # Nuitka 打包脚本
├── requirements.txt        # 依赖清单
└── README_CN.md            # 本文档
```

## 🔧 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| UI 框架 | tkinter + ttkbootstrap |
| 数据库 | sqlite3（内置） |
| 图标处理 | Pillow |
| 打包 | Nuitka（编译为原生代码，体积更小、启动更快） |
| 系统 API | ctypes（Windows DWM / DPI / Mutex） |

## 📝 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.4.0 | 2026-06-30 | **UI 重构**：操作栏压缩为单行紧凑布局；合并移动/复制为统一按钮；修复高 DPI 下窗口底部被遮挡问题；界面美化 |
| v1.3.0 | 2026-06-29 | **DPI 感知自适应**：支持任意分辨率（1366×768 到 3840×2160）和 DPI 缩放（100%–200%）；筛选栏和操作栏改用弹性 grid 布局 |
| v1.2.0 | 2026-06-29 | **UI 全面优化**：修复高 DPI 屏幕 UI 拥挤问题；窗口按屏幕比例自适应；动态列宽、内容居中对齐、行高增大 |
| v1.1.0 | 2026-06-09 | **EXE 体积优化**：换用 Nuitka 编译，体积从 ~32MB 降至 ~6–9MB |
| v1.0.0 | 2026-06-07 | **初始版本**：浏览/筛选/移动/复制/删除，主题跟随，单实例，DPI 自适应 |

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 🙏 致谢

- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) — 现代 tkinter 主题
- [Nuitka](https://nuitka.net/) — Python 编译器
- [OpenAI Codex](https://github.com/openai/codex) — 本工具的管理对象
