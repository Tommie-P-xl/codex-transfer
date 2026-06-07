# Codex Transfer v1.0.0

轻量级 Windows 桌面应用，用于管理 Codex 聊天历史记录。

## 功能

- 📋 浏览所有 Codex 聊天记录（标题、时间、路径、归属）
- 🔍 按归属、项目路径、标题关键字筛选
- 📦 批量移动消息归属（修改 model_provider）
- 📋 批量复制消息到新归属（复制 JSONL 文件 + 新建记录）
- 🗑️ 批量删除消息（同时删除文件和记录）
- 🌙 暗色/亮色主题跟随系统
- 🔒 防止软件多开

## 使用

### 直接运行（开发模式）

```bash
pip install ttkbootstrap Pillow
python main.py
```

### 构建 exe

```bash
pip install -r requirements.txt
python build.py
```

构建完成后，exe 文件位于 `dist/CodexTransfer.exe`。

## 配置

- 配置文件位置：`%APPDATA%/CodexTransfer/config.json`
- 默认 Codex 路径：`~/.codex`
- 可通过 UI 更改 Codex 路径

## 数据说明

- 读取 `state_*.sqlite` 中的 `threads` 表
- 修改归属时同时更新 SQLite 和 JSONL 文件
- 复制时创建新的 JSONL 文件和 SQLite 记录
- 删除时同时移除文件和记录

## 版本历史

- v1.0.0 (2026-06-07) — 初始版本
