# Codex Transfer v1.0.0 — 设计文档

## 概述

Codex Transfer 是一个轻量级 Windows 桌面应用，用于管理 Codex 的聊天历史记录。用户可以浏览、筛选、迁移、复制和删除 Codex 会话数据。

**核心目标**：
- 轻量化，资源占用少
- 无需安装，单 exe 运行
- 暗色/亮色主题跟随系统
- 防止软件多开

## 技术栈

- Python 3.10+
- tkinter + ttkbootstrap（UI 框架 + 主题）
- sqlite3（内置，数据读写）
- Pillow（图标转换）
- PyInstaller（打包 exe）
- ctypes（Windows API 调用，单实例 + 主题检测）

## 架构

```
┌─────────────────────────────────────────────┐
│              Codex Transfer v1.0.0           │
├─────────────────────────────────────────────┤
│  tkinter + ttkbootstrap (UI 层)             │
│  ├── 主窗口 (暗色/亮色主题跟随系统)          │
│  ├── 筛选栏 (provider / 路径 / 关键字)       │
│  ├── 消息列表 (Treeview 表格)               │
│  └── 操作栏 (全选 / 移动 / 复制 / 删除)      │
├─────────────────────────────────────────────┤
│  数据层                                      │
│  ├── CodexDB (SQLite 读写)                  │
│  └── RolloutManager (JSONL 文件操作)         │
├─────────────────────────────────────────────┤
│  系统层                                      │
│  ├── 单实例 Mutex                            │
│  ├── 主题检测 (Windows 注册表)               │
│  └── 配置管理 (codex_home 路径)              │
└─────────────────────────────────────────────┘
```

## 数据来源

Codex 数据目录（`codex_home`）查找优先级：
1. 用户配置路径（持久化在 `%APPDATA%/CodexTransfer/config.json`）
2. 环境变量 `CODEX_HOME`
3. 默认 `~/.codex`

关键文件：
- `state_*.sqlite` — threads 表，存储会话元数据
- `sessions/YYYY/MM/DD/rollout-*.jsonl` — 会话内容文件

## 数据模型

### SQLite threads 表关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 会话 UUID |
| title | TEXT | 会话标题 |
| model_provider | TEXT | 消息归属（如 openai） |
| cwd | TEXT | 项目路径 |
| created_at | INTEGER | 创建时间（Unix 秒） |
| updated_at | INTEGER | 更新时间（Unix 秒） |
| archived | INTEGER | 是否归档（0/1） |
| first_user_message | TEXT | 首条消息内容 |
| preview | TEXT | 预览文本 |
| rollout_path | TEXT | JSONL 文件路径 |

### 数据操作

| 操作 | SQLite | JSONL |
|------|--------|-------|
| 读取列表 | SELECT 查询 | 不读取 |
| 修改归属 | UPDATE model_provider | 替换 session_meta.payload.model_provider |
| 复制归属 | INSERT 新记录（新 ID） | 复制文件 → 修改 provider 和 ID → 回写 |
| 删除 | DELETE 记录 | 删除文件 |

## UI 布局

```
┌─────────────────────────────────────────────────────────────┐
│  Codex Transfer v1.0.0                              [─][□][✕] │
├─────────────────────────────────────────────────────────────┤
│  ⚙ Codex路径: [C:\Users\xxx\.codex        ] [更改] [刷新]    │
├─────────────────────────────────────────────────────────────┤
│  归属筛选: [全部 ▼]  路径筛选: [全部 ▼]  标题搜索: [________🔍] │
├─────────────────────────────────────────────────────────────┤
│  ☐ │ 标题                │ 时间            │ 路径        │ 归属   │
│  ──┼─────────────────────┼─────────────────┼─────────────┼─────── │
│  ☐ │ "帮我写个爬虫"      │ 2026-06-06 18:30│ D:\project1 │ openai │
│  ☐ │ "修复登录bug"       │ 2026-06-05 14:20│ D:\web_app  │ openai │
│  ☐ │ "数据分析脚本"      │ 2026-06-04 09:15│ D:\data     │ openai │
├─────────────────────────────────────────────────────────────┤
│  [全选] [全不选] [反选]                                      │
│                                                             │
│  已选 3 条 | [移动到已有归属 ▼] [移动到新归属]                │
│            | [复制到已有归属 ▼] [复制到新归属]                │
│            | [删除选中]                                     │
├─────────────────────────────────────────────────────────────┤
│  状态: 共 9 条消息 | 归属分布: openai(9)                     │
└─────────────────────────────────────────────────────────────┘
```

**表格交互**：
- 点击行选中（支持 Ctrl/Shift 多选）
- 复选框列支持单个勾选
- 归档消息行背景色略不同以区分
- 点击列头可排序
- 双击行可复制标题到剪贴板

## 筛选功能

- **归属筛选**：下拉框，列出所有唯一的 model_provider 值 + "全部"
- **路径筛选**：下拉框，列出所有唯一的 cwd 值 + "全部"
- **标题搜索**：输入框，实时模糊匹配标题（LIKE %keyword%）
- 筛选条件可组合使用

## 操作功能

### 移动到已有归属
1. 用户从下拉框选择目标 provider
2. 对每条选中消息：UPDATE SQLite model_provider → 读取 JSONL → 替换 provider → 回写
3. 刷新列表

### 移动到新归属
1. 弹出对话框让用户输入新 provider 名称
2. 若该 provider 名称已存在，提示用户"该归属已存在，请使用'移动到已有归属'"并终止操作
3. 否则执行与"移动到已有归属"相同逻辑

### 复制到已有归属
1. 用户从下拉框选择目标 provider
2. 对每条选中消息：
   - 复制 JSONL 文件（同目录，新文件名含新 UUID）
   - 读取新文件 → 修改 provider 和 session ID → 回写
   - INSERT 新 thread 记录（新 ID，新 rollout_path，目标 provider）
3. 刷新列表

### 复制到新归属
1. 弹出对话框让用户输入新 provider 名称
2. 若该 provider 名称已存在，提示用户"该归属已存在，请使用'复制到已有归属'"并终止操作
3. 否则执行与"复制到已有归属"相同逻辑

### 删除选中
1. 弹出确认对话框（显示将删除的条数）
2. 对每条选中消息：DELETE SQLite 记录 → 删除 JSONL 文件
3. 刷新列表

## 单实例机制

- 使用 `ctypes` 调用 `CreateMutexW` 创建命名互斥锁
- Mutex 名称：`CodexTransfer_SingleInstance`
- 检测到已有实例时：通过 `ctypes` 调用 `FindWindowW` 查找已有窗口 → `SetForegroundWindow` 激活
- 无需额外依赖

## 主题跟随系统

- 读取注册表：`HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize\AppsUseLightTheme`
- 值为 0 → 暗色主题（ttkbootstrap `darkly`）
- 值为 1 → 亮色主题（ttkbootstrap `cosmo`）
- 启动时检测一次，不实时监听

## 配置持久化

配置文件位置：`%APPDATA%/CodexTransfer/config.json`

```json
{
  "codex_home": "C:\\Users\\xxx\\.codex",
  "theme": "auto",
  "window_geometry": "1200x700"
}
```

## 错误处理

- SQLite 文件不存在或损坏 → 提示用户检查路径
- JSONL 文件读写失败 → 跳过并记录日志，不中断批量操作
- 删除前弹出确认对话框
- 批量操作显示进度

## 资源优化

- 表格分页：每页 500 条，避免大量数据一次性加载
- SQLite 连接用完即关
- 启动时仅读 SQLite，操作时才读写 JSONL
- 预计内存占用：~30-40MB

## 打包

- PyInstaller `--onefile --windowed`
- 图标：将提供的 PNG 转换为 .ico（含 16/32/48/256 尺寸）
- 预计打包体积：~25-35MB

## 依赖

```
ttkbootstrap>=1.10
Pillow>=10.0
pyinstaller>=6.0  # 仅打包时
```

## 项目结构

```
D:\edge_load\CodexTransfer\
├── main.py              # 入口，单实例检测 + 启动 UI
├── ui/
│   ├── app.py           # 主窗口
│   ├── theme.py         # 主题检测与切换
│   └── widgets.py       # 自定义组件
├── core/
│   ├── database.py      # SQLite 操作封装
│   ├── rollout.py       # JSONL 文件操作封装
│   └── config.py        # 配置管理
├── assets/
│   └── icon.ico         # 应用图标
├── build.py             # PyInstaller 打包脚本
├── requirements.txt
└── README.md
```
