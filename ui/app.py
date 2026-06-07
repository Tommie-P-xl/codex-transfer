# ui/app.py
"""Main application window for Codex Transfer."""
from __future__ import annotations

import datetime
import json
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import webbrowser

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

from core.config import Config
from core.database import CodexDB, ThreadRecord, find_state_db
from core.rollout import RolloutManager
from ui.widgets import CheckboxTreeview

APP_VERSION = "1.0.0"
GITHUB_REPO = "Tommie-P-xl/codex-transfer"
LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"


def _icon_candidates() -> list[Path]:
    import sys
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "assets" / "icon.ico")
    candidates.append(Path(__file__).resolve().parent.parent / "assets" / "icon.ico")
    candidates.append(Path(__file__).resolve().parent / "icon.ico")
    candidates.append(Path("assets") / "icon.ico")
    return candidates


def _set_icon(window: tk.Tk | tk.Toplevel) -> None:
    """设置窗口图标，让 Tk/Windows 按场景选择最合适的图标尺寸。"""
    for p in _icon_candidates():
        if not p.exists():
            continue
        try:
            image = Image.open(p)
            ico = getattr(image, "ico", None)
            sizes = sorted(ico.sizes() if ico else [image.size], key=lambda size: size[0] * size[1])
            photos = []
            for size in sizes:
                frame = ico.getimage(size) if ico else image.resize(size, Image.Resampling.LANCZOS)
                photos.append(ImageTk.PhotoImage(frame.convert("RGBA")))
            window.iconphoto(True, *photos)
            setattr(window, "_codex_transfer_icons", photos)
            try:
                window.iconbitmap(str(p))
            except Exception:
                pass
            return
        except Exception:
            try:
                window.iconbitmap(str(p))
                return
            except Exception:
                continue


def _parse_version(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", value)
    return tuple(int(part) for part in parts[:3]) or (0,)


def _is_newer_version(remote: str, current: str) -> bool:
    remote_parts = _parse_version(remote)
    current_parts = _parse_version(current)
    width = max(len(remote_parts), len(current_parts))
    return remote_parts + (0,) * (width - len(remote_parts)) > current_parts + (0,) * (width - len(current_parts))


def _resolve_rollout_path(codex_home: Path, rollout_path: str) -> Path:
    path = Path(rollout_path)
    if path.is_absolute():
        return path
    return codex_home / path


def _clean_cell_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _load_session_title_index(codex_home: Path) -> dict[str, str]:
    index_path = codex_home / "session_index.jsonl"
    titles: dict[str, str] = {}
    if not index_path.exists():
        return titles
    try:
        lines = index_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return titles
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        thread_id = payload.get("id")
        thread_name = _clean_cell_text(payload.get("thread_name"))
        if isinstance(thread_id, str) and thread_name:
            titles[thread_id] = thread_name
    return titles


def _append_session_index(codex_home: Path, thread_id: str, title: str) -> None:
    """Append a new entry to session_index.jsonl for Codex Desktop compatibility."""
    index_path = codex_home / "session_index.jsonl"
    entry = {
        "id": thread_id,
        "thread_name": _clean_cell_text(title),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    try:
        with open(index_path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def _sync_session_index(codex_home: Path, threads: list[ThreadRecord], session_titles: dict[str, str]) -> None:
    """Sync database threads to session_index.jsonl, adding any missing entries."""
    index_path = codex_home / "session_index.jsonl"

    # Load existing entries
    existing_ids: set[str] = set()
    if index_path.exists():
        try:
            for line in index_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                    if isinstance(payload.get("id"), str):
                        existing_ids.add(payload["id"])
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass

    # Find threads missing from session_index
    missing_threads = []
    for thread in threads:
        if thread.id not in existing_ids:
            title = session_titles.get(thread.id) or _clean_cell_text(thread.title) or "(无标题)"
            missing_threads.append((thread.id, title))

    # Append missing entries
    if missing_threads:
        try:
            with open(index_path, "a", encoding="utf-8") as f:
                for thread_id, title in missing_threads:
                    entry = {
                        "id": thread_id,
                        "thread_name": _clean_cell_text(title),
                        "updated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    }
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass


def _apply_titlebar_theme(window: tk.Tk, theme_pref: str) -> None:
    """让 Windows 标题栏跟随系统暗色/亮色主题（Win10 1809+）。"""
    import sys
    if sys.platform != "win32":
        return

    from ui.theme import detect_system_theme
    # detect_system_theme 返回 "darkly" 或 "cosmo"
    is_dark = detect_system_theme() == "darkly"

    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Win10 1809+) / 19 (older)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1 if is_dark else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value), ctypes.sizeof(value)
        )
    except Exception:
        pass


COLUMNS = [
    ("check", "☐", 40, "center"),
    ("title", "标题", 300, "w"),
    ("time", "时间", 140, "center"),
    ("cwd", "路径", 350, "w"),
    ("provider", "归属", 100, "center"),
    ("archived", "归档", 50, "center"),
]


class CodexTransferApp:
    """Main application window that wires together all modules."""

    def __init__(self, root: ttk.Window, config: Config) -> None:
        self.root = root
        self.config = config
        self.db: CodexDB | None = None
        self.rollout: RolloutManager | None = None
        self._threads: list[ThreadRecord] = []
        self._session_titles: dict[str, str] = {}
        self._sort_column: str = "time"
        self._sort_reverse: bool = True
        self._toast_after_id: str | None = None

        self._setup_window()
        self._build_path_bar()
        self._build_filter_bar()
        self._build_table()
        self._build_action_bar()
        self._build_status_bar()
        self._load_data()
        # 所有 UI 构建完成后显示窗口，避免小窗口闪烁
        self.root.update_idletasks()
        self.root.deiconify()

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------
    def _setup_window(self) -> None:
        self.root.title(f"Codex Transfer v{APP_VERSION}")

        # 使用配置的尺寸，但如果太小则用默认值
        geo = self.config.window_geometry
        try:
            w, h = geo.split("x")[0], geo.split("x")[1].split("+")[0]
            if int(w) < 900 or int(h) < 520:
                geo = "900x520"
        except Exception:
            geo = "900x520"
        self.root.geometry(geo)
        self.root.minsize(600, 450)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 设置窗口图标
        _set_icon(self.root)

        # 让 Windows 标题栏跟随系统暗色/亮色主题
        _apply_titlebar_theme(self.root, self.config.theme)

        # 配置全局字体 — Microsoft YaHei UI 更美观，字号 11
        import tkinter.font as tkfont
        for font_name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont", "TkTooltipFont"):
            try:
                tkfont.nametofont(font_name).configure(family="Microsoft YaHei UI", size=11)
            except Exception:
                pass
        # Treeview 使用 style 设置字体
        style = ttk.Style()
        style.configure("Treeview", font=("Microsoft YaHei UI", 11), rowheight=28)
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 11, "bold"))

    def _on_close(self) -> None:
        # Save current window geometry before closing
        self.config.window_geometry = self.root.geometry()
        self.config.save()
        if self.db:
            self.db.close()
        self.root.destroy()

    # ------------------------------------------------------------------
    # Path bar
    # ------------------------------------------------------------------
    def _build_path_bar(self) -> None:
        lf = ttk.LabelFrame(self.root, text=" Codex 路径 ")
        lf.pack(fill=X, padx=10, pady=(10, 5))
        frame = ttk.Frame(lf, padding=8)
        frame.pack(fill=X)

        self._path_var = tk.StringVar(value=str(self.config.codex_home))
        self._path_entry = ttk.Entry(frame, textvariable=self._path_var, state="readonly")
        self._path_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

        btn_change = ttk.Button(frame, text="更改", command=self._change_codex_path, bootstyle=SECONDARY)
        btn_change.pack(side=LEFT, padx=(0, 5))

        btn_refresh = ttk.Button(frame, text="刷新", command=self._load_data, bootstyle=INFO)
        btn_refresh.pack(side=LEFT, padx=(0, 5))

        btn_update = ttk.Button(frame, text="检查更新", command=self._check_for_updates, bootstyle=SECONDARY)
        btn_update.pack(side=LEFT)

    def _change_codex_path(self) -> None:
        chosen = filedialog.askdirectory(title="选择 Codex 根目录")
        if not chosen:
            return
        self.config.codex_home = Path(chosen)
        self.config.save()
        self._path_var.set(chosen)
        self._load_data()

    # ------------------------------------------------------------------
    # Filter bar
    # ------------------------------------------------------------------
    def _build_filter_bar(self) -> None:
        lf = ttk.LabelFrame(self.root, text=" 筛选 ")
        lf.pack(fill=X, padx=10, pady=5)
        frame = ttk.Frame(lf, padding=8)
        frame.pack(fill=X)

        # Provider dropdown
        ttk.Label(frame, text="归属:").pack(side=LEFT, padx=(0, 2))
        self._provider_var = tk.StringVar()
        self._provider_combo = ttk.Combobox(frame, textvariable=self._provider_var, state="readonly", width=14)
        self._provider_combo.pack(side=LEFT, padx=(0, 10))
        self._provider_combo.bind("<<ComboboxSelected>>", lambda _: self._apply_filters())

        # CWD dropdown
        ttk.Label(frame, text="路径:").pack(side=LEFT, padx=(0, 2))
        self._cwd_var = tk.StringVar()
        self._cwd_combo = ttk.Combobox(frame, textvariable=self._cwd_var, state="readonly", width=30)
        self._cwd_combo.pack(side=LEFT, padx=(0, 10))
        self._cwd_combo.bind("<<ComboboxSelected>>", lambda _: self._apply_filters())

        # Keyword search
        ttk.Label(frame, text="关键词:").pack(side=LEFT, padx=(0, 2))
        self._keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(frame, textvariable=self._keyword_var, width=20)
        keyword_entry.pack(side=LEFT, padx=(0, 5))
        keyword_entry.bind("<Return>", lambda _: self._apply_filters())

        btn_search = ttk.Button(frame, text="🔍", command=self._apply_filters, bootstyle=SECONDARY, width=3)
        btn_search.pack(side=LEFT)

    # ------------------------------------------------------------------
    # Main table
    # ------------------------------------------------------------------
    def _build_table(self) -> None:
        frame = ttk.Frame(self.root)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        col_ids = [c[0] for c in COLUMNS]

        self._tree = CheckboxTreeview(frame, columns=col_ids, show="headings", selectmode="none", height=12)

        # 配置所有列
        for cid, header, width, anchor in COLUMNS:
            self._tree.heading(cid, text=header, anchor="center",
                               command=lambda c=cid: self._sort_by(c) if c != "check" else None)
            self._tree.column(cid, width=width, minwidth=40, anchor=anchor, stretch=False)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Double-click to copy title
        self._tree.bind("<Double-1>", self._on_double_click)

    # ------------------------------------------------------------------
    # Action bar
    # ------------------------------------------------------------------
    def _build_action_bar(self) -> None:
        lf = ttk.LabelFrame(self.root, text=" 操作 ")
        lf.pack(fill=X, padx=10, pady=5)
        frame = ttk.Frame(lf, padding=8)
        frame.pack(fill=X)

        # Selection buttons
        ttk.Button(frame, text="全选", command=self._tree.check_all, bootstyle=SECONDARY).pack(side=LEFT, padx=2)
        ttk.Button(frame, text="全不选", command=self._tree.uncheck_all, bootstyle=SECONDARY).pack(side=LEFT, padx=2)
        ttk.Button(frame, text="反选", command=self._tree.invert_checked, bootstyle=SECONDARY).pack(side=LEFT, padx=2)

        ttk.Separator(frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=8)

        # Move to existing provider
        self._move_exist_var = tk.StringVar()
        self._move_exist_combo = ttk.Combobox(frame, textvariable=self._move_exist_var, state="readonly", width=14)
        self._move_exist_combo.pack(side=LEFT, padx=2)
        ttk.Button(frame, text="移动到已有归属", command=self._move_to_existing, bootstyle=PRIMARY).pack(side=LEFT, padx=2)

        # Move to new provider
        ttk.Button(frame, text="移动到新归属", command=self._move_to_new, bootstyle=PRIMARY).pack(side=LEFT, padx=2)

        ttk.Separator(frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=8)

        # Copy to existing provider
        self._copy_exist_var = tk.StringVar()
        self._copy_exist_combo = ttk.Combobox(frame, textvariable=self._copy_exist_var, state="readonly", width=14)
        self._copy_exist_combo.pack(side=LEFT, padx=2)
        ttk.Button(frame, text="复制到已有归属", command=self._copy_to_existing, bootstyle=SUCCESS).pack(side=LEFT, padx=2)

        # Copy to new provider
        ttk.Button(frame, text="复制到新归属", command=self._copy_to_new, bootstyle=SUCCESS).pack(side=LEFT, padx=2)

        ttk.Separator(frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=8)

        # Delete
        ttk.Button(frame, text="删除选中", command=self._delete_selected, bootstyle=DANGER).pack(side=LEFT, padx=2)

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------
    def _build_status_bar(self) -> None:
        frame = ttk.Frame(self.root, padding=(10, 5))
        frame.pack(fill=X, side=BOTTOM)

        self._status_var = tk.StringVar(value="就绪")
        self._status_label = ttk.Label(frame, textvariable=self._status_var, anchor=W)
        self._status_label.pack(side=LEFT, fill=X, expand=True)

        self._toast_var = tk.StringVar(value="")
        self._toast_label = ttk.Label(frame, textvariable=self._toast_var, anchor=E, bootstyle="info")
        self._toast_label.pack(side=RIGHT)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def _load_data(self) -> None:
        # Close previous DB connection if any
        if self.db:
            self.db.close()
            self.db = None

        db_path = find_state_db(self.config.codex_home)
        if db_path is None:
            self._status_var.set("未找到 Codex 数据库。请确认 Codex 路径正确。")
            return

        self.db = CodexDB(db_path)
        self.rollout = RolloutManager(self.config.codex_home)
        self._session_titles = _load_session_title_index(self.config.codex_home)

        # Populate filter dropdowns
        all_threads = self.db.list_threads()
        active_threads, missing_count = self._filter_existing_threads(all_threads)
        self._missing_rollout_count = missing_count

        # Sync database threads to session_index.jsonl for Codex Desktop compatibility
        _sync_session_index(self.config.codex_home, active_threads, self._session_titles)
        providers = sorted({t.model_provider for t in active_threads if t.model_provider})
        cwds_raw = sorted({t.cwd for t in active_threads if t.cwd})
        # 去掉路径中的 \\?\ 前缀用于显示，同时建立 显示→原始 的映射
        self._cwd_display_map: dict[str, str] = {}
        cwds_clean: list[str] = []
        for c in cwds_raw:
            clean = c.replace("\\\\?\\", "").replace("\\?\\", "")
            self._cwd_display_map[clean] = c
            cwds_clean.append(clean)

        self._provider_combo["values"] = ["(全部)"] + providers
        self._provider_var.set("(全部)")
        self._cwd_combo["values"] = ["(全部)"] + cwds_clean
        self._cwd_var.set("(全部)")

        # Populate action bar dropdowns
        self._move_exist_combo["values"] = providers
        self._copy_exist_combo["values"] = providers
        if providers:
            self._move_exist_var.set(providers[0])
            self._copy_exist_var.set(providers[0])

        self._apply_filters()

    def _apply_filters(self) -> None:
        if self.db is None:
            return

        provider = self._provider_var.get()
        cwd = self._cwd_var.get()
        keyword = self._keyword_var.get().strip()

        # 把显示路径映射回数据库原始路径
        cwd_query = None
        if cwd != "(全部)":
            cwd_query = self._cwd_display_map.get(cwd, cwd)

        threads = self.db.list_threads(
            provider=provider if provider != "(全部)" else None,
            cwd=cwd_query,
        )
        threads, self._missing_rollout_count = self._filter_existing_threads(threads)
        if keyword:
            keyword_lower = keyword.lower()
            threads = [
                thread for thread in threads
                if keyword_lower in self._display_title(thread).lower()
                or keyword_lower in _clean_cell_text(thread.first_user_message).lower()
                or keyword_lower in _clean_cell_text(thread.preview).lower()
            ]
        self._threads = threads
        self._refresh_table()

    def _display_title(self, thread: ThreadRecord) -> str:
        return self._session_titles.get(thread.id) or _clean_cell_text(thread.title) or "(无标题)"

    def _filter_existing_threads(self, threads: list[ThreadRecord]) -> tuple[list[ThreadRecord], int]:
        visible: list[ThreadRecord] = []
        missing = 0
        for thread in threads:
            if _resolve_rollout_path(self.config.codex_home, thread.rollout_path).exists():
                visible.append(thread)
            else:
                missing += 1
        return visible, missing

    def _refresh_table(self) -> None:
        self._tree.clear_checked()
        for item in self._tree.get_children():
            self._tree.delete(item)

        # Sort data
        def sort_key(t: ThreadRecord) -> Any:
            col = self._sort_column
            if col == "title":
                return self._display_title(t)
            if col == "time":
                return t.updated_at
            if col == "cwd":
                return t.cwd or ""
            if col == "provider":
                return t.model_provider or ""
            if col == "archived":
                return t.archived
            return ""

        sorted_threads = sorted(self._threads, key=sort_key, reverse=self._sort_reverse)

        for t in sorted_threads:
            ts = datetime.datetime.fromtimestamp(t.updated_at).strftime("%Y-%m-%d %H:%M") if t.updated_at else ""
            archived_str = "是" if t.archived else ""
            # 去掉 cwd 中的 \\?\ 前缀
            cwd_display = _clean_cell_text((t.cwd or "").replace("\\\\?\\", "").replace("\\?\\", ""))
            # CheckboxTreeview.insert automatically prepends the checkbox column value
            self._tree.insert("", END, iid=t.id, values=(
                self._display_title(t),
                ts,
                cwd_display,
                _clean_cell_text(t.model_provider),
                archived_str,
            ))

        self._update_status()

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------
    def _sort_by(self, column: str) -> None:
        if column == "check":
            return
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = True
        self._refresh_table()

    # ------------------------------------------------------------------
    # Status update
    # ------------------------------------------------------------------
    def _update_status(self) -> None:
        total = len(self._threads)
        checked = len(self._tree.get_checked_ids())
        suffix = f"，已隐藏 {self._missing_rollout_count} 条已删除记录" if getattr(self, "_missing_rollout_count", 0) else ""
        self._status_var.set(f"共 {total} 条记录，已选 {checked} 条{suffix}")

    def _check_for_updates(self) -> None:
        self._show_toast("正在检查更新...")

        def worker() -> None:
            try:
                request = Request(
                    LATEST_RELEASE_API,
                    headers={
                        "Accept": "application/vnd.github+json",
                        "User-Agent": f"CodexTransfer/{APP_VERSION}",
                    },
                )
                with urlopen(request, timeout=10) as response:
                    data = json.loads(response.read().decode("utf-8"))
                latest = str(data.get("tag_name") or data.get("name") or "").lstrip("v")
                html_url = str(data.get("html_url") or RELEASES_URL)
                if not latest:
                    raise ValueError("GitHub Releases 未返回版本号")
                self.root.after(0, lambda: self._show_update_result(latest, html_url))
            except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                detail = str(exc)
                self.root.after(0, lambda detail=detail: self._show_update_error(detail))

        threading.Thread(target=worker, daemon=True).start()

    def _show_update_result(self, latest: str, html_url: str) -> None:
        if _is_newer_version(latest, APP_VERSION):
            ok = messagebox.askyesno(
                "发现新版本",
                f"当前版本：v{APP_VERSION}\n最新版本：v{latest}\n\n是否打开下载页面？",
                parent=self.root,
            )
            if ok:
                webbrowser.open(html_url)
            self._show_toast(f"发现新版本 v{latest}")
        else:
            messagebox.showinfo("检查更新", f"当前已是最新版本：v{APP_VERSION}", parent=self.root)
            self._show_toast("当前已是最新版本")

    def _show_update_error(self, detail: str) -> None:
        messagebox.showwarning("检查更新失败", f"无法获取最新版本信息。\n\n{detail}", parent=self.root)
        self._show_toast("检查更新失败")

    # ------------------------------------------------------------------
    # Move to existing provider
    # ------------------------------------------------------------------
    def _move_to_existing(self) -> None:
        if self.db is None or self.rollout is None:
            return
        checked_ids = self._tree.get_checked_ids()
        if not checked_ids:
            self._show_toast("请先勾选要操作的记录")
            return
        new_provider = self._move_exist_var.get()
        if not new_provider:
            self._show_toast("请先选择目标归属")
            return

        # Gather rollout paths for the checked threads
        id_to_thread = {t.id: t for t in self._threads}
        rollout_paths = [id_to_thread[tid].rollout_path for tid in checked_ids if tid in id_to_thread]

        # Update JSONL files
        self.rollout.rewrite_providers(rollout_paths, new_provider)
        # Update SQLite records
        self.db.update_provider_batch(checked_ids, new_provider)

        self._show_toast(f"已移动 {len(checked_ids)} 条记录到归属 \"{new_provider}\"")
        self._load_data()

    # ------------------------------------------------------------------
    # Move to new provider
    # ------------------------------------------------------------------
    def _move_to_new(self) -> None:
        if self.db is None or self.rollout is None:
            return
        checked_ids = self._tree.get_checked_ids()
        if not checked_ids:
            self._show_toast("请先勾选要操作的记录")
            return

        new_name = self._ask_provider_name()
        if not new_name:
            return

        existing = self.db.get_distinct_providers()
        if new_name in existing:
            messagebox.showwarning("归属已存在", f"归属 \"{new_name}\" 已存在，请使用\"移动到已有归属\"功能。")
            return

        id_to_thread = {t.id: t for t in self._threads}
        rollout_paths = [id_to_thread[tid].rollout_path for tid in checked_ids if tid in id_to_thread]

        self.rollout.rewrite_providers(rollout_paths, new_name)
        self.db.update_provider_batch(checked_ids, new_name)

        self._show_toast(f"已移动 {len(checked_ids)} 条记录到新归属 \"{new_name}\"")
        self._load_data()

    # ------------------------------------------------------------------
    # Copy to existing provider
    # ------------------------------------------------------------------
    def _copy_to_existing(self) -> None:
        if self.db is None or self.rollout is None:
            return
        checked_ids = self._tree.get_checked_ids()
        if not checked_ids:
            self._show_toast("请先勾选要操作的记录")
            return
        new_provider = self._copy_exist_var.get()
        if not new_provider:
            self._show_toast("请先选择目标归属")
            return

        id_to_thread = {t.id: t for t in self._threads}
        count = 0
        for tid in checked_ids:
            t = id_to_thread[tid]
            if t is None:
                continue
            dst_path, new_id = self.rollout.copy_rollout(t.rollout_path, new_provider)
            title = self._display_title(t)
            self.db.insert_thread(
                thread_id=new_id,
                rollout_path=dst_path,
                created_at=t.created_at,
                updated_at=t.updated_at,
                model_provider=new_provider,
                cwd=t.cwd,
                title=title,
            )
            _append_session_index(self.config.codex_home, new_id, title)
            count += 1

        self._show_toast(f"已复制 {count} 条记录到归属 \"{new_provider}\"")
        self._load_data()

    # ------------------------------------------------------------------
    # Copy to new provider
    # ------------------------------------------------------------------
    def _copy_to_new(self) -> None:
        if self.db is None or self.rollout is None:
            return
        checked_ids = self._tree.get_checked_ids()
        if not checked_ids:
            self._show_toast("请先勾选要操作的记录")
            return

        new_name = self._ask_provider_name()
        if not new_name:
            return

        existing = self.db.get_distinct_providers()
        if new_name in existing:
            messagebox.showwarning("归属已存在", f"归属 \"{new_name}\" 已存在，请使用\"复制到已有归属\"功能。")
            return

        id_to_thread = {t.id: t for t in self._threads}
        count = 0
        for tid in checked_ids:
            t = id_to_thread[tid]
            if t is None:
                continue
            dst_path, new_id = self.rollout.copy_rollout(t.rollout_path, new_name)
            title = self._display_title(t)
            self.db.insert_thread(
                thread_id=new_id,
                rollout_path=dst_path,
                created_at=t.created_at,
                updated_at=t.updated_at,
                model_provider=new_name,
                cwd=t.cwd,
                title=title,
            )
            _append_session_index(self.config.codex_home, new_id, title)
            count += 1

        self._show_toast(f"已复制 {count} 条记录到新归属 \"{new_name}\"")
        self._load_data()

    # ------------------------------------------------------------------
    # Delete selected
    # ------------------------------------------------------------------
    def _delete_selected(self) -> None:
        if self.db is None or self.rollout is None:
            return
        checked_ids = self._tree.get_checked_ids()
        if not checked_ids:
            self._show_toast("请先勾选要操作的记录")
            return

        ok = messagebox.askyesno("确认删除", f"确定要删除选中的 {len(checked_ids)} 条记录吗？\n\n此操作不可撤销，将同时删除 JSONL 文件和数据库记录。")
        if not ok:
            return

        id_to_thread = {t.id: t for t in self._threads}
        for tid in checked_ids:
            t = id_to_thread.get(tid)
            if t:
                self.rollout.delete_rollout(t.rollout_path)
        self.db.delete_threads(checked_ids)

        self._show_toast(f"已删除 {len(checked_ids)} 条记录")
        self._load_data()

    # ------------------------------------------------------------------
    # Provider name dialog
    # ------------------------------------------------------------------
    def _ask_provider_name(self) -> str | None:
        """Show a modal dialog to enter a new provider name. Returns name or None."""
        dialog = tk.Toplevel(self.root)
        dialog.withdraw()
        dialog.title("新建归属")
        _set_icon(dialog)
        scaling = max(float(self.root.tk.call("tk", "scaling")), 1.0)
        width = min(max(int(360 * scaling), 350), max(self.root.winfo_screenwidth() - 80, 320))
        height = min(max(int(150 * scaling), 150), max(self.root.winfo_screenheight() - 80, 145))
        dialog.geometry(f"{width}x{height}")
        dialog.minsize(330, 145)
        dialog.resizable(True, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center over parent
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - height) // 2
        x = max(0, min(x, self.root.winfo_screenwidth() - width))
        y = max(0, min(y, self.root.winfo_screenheight() - height))
        dialog.geometry(f"{width}x{height}+{x}+{y}")

        result: list[str | None] = [None]

        body = ttk.Frame(dialog, padding=(16, 12, 16, 10))
        body.pack(fill=BOTH, expand=True)
        body.columnconfigure(0, weight=1)

        ttk.Label(body, text="请输入新的归属名称:").grid(row=0, column=0, sticky=W, pady=(0, 8))
        entry_var = tk.StringVar()
        entry = ttk.Entry(body, textvariable=entry_var)
        entry.grid(row=1, column=0, sticky=EW)
        entry.focus_set()

        btn_frame = ttk.Frame(body)
        btn_frame.grid(row=2, column=0, sticky=E, pady=(12, 0))

        def on_ok() -> None:
            name = entry_var.get().strip()
            if name:
                result[0] = name
                dialog.destroy()
            else:
                messagebox.showwarning("输入为空", "归属名称不能为空。", parent=dialog)

        def on_cancel() -> None:
            dialog.destroy()

        ttk.Button(btn_frame, text="确定", command=on_ok, bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="取消", command=on_cancel, bootstyle=SECONDARY, width=10).pack(side=LEFT)

        # Enter key submits
        entry.bind("<Return>", lambda _: on_ok())

        dialog.update_idletasks()
        dialog.deiconify()
        dialog.lift(self.root)
        dialog.wait_window()
        return result[0]

    # ------------------------------------------------------------------
    # Double-click handler
    # ------------------------------------------------------------------
    def _on_double_click(self, event: tk.Event) -> None:
        """Copy the title of the double-clicked row to the clipboard."""
        item = self._tree.identify_row(event.y)
        if not item:
            return
        values = self._tree.item(item, "values")
        # values[0]=checkbox, values[1]=title
        if values and len(values) > 1:
            title = values[1]
            self.root.clipboard_clear()
            self.root.clipboard_append(title)
            self._show_toast(f"已复制标题: {title}")

    # ------------------------------------------------------------------
    # Toast notification
    # ------------------------------------------------------------------
    def _show_toast(self, message: str, duration_ms: int = 3000) -> None:
        """Show a temporary status message."""
        if self._toast_after_id is not None:
            self.root.after_cancel(self._toast_after_id)
        self._toast_var.set(message)
        self._toast_after_id = self.root.after(duration_ms, lambda: self._toast_var.set(""))

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Start the main event loop."""
        self.root.mainloop()
