# ui/app.py
"""Main application window for Codex Transfer."""
from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any
from pathlib import Path

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from core.config import Config
from core.database import CodexDB, ThreadRecord, find_state_db
from core.rollout import RolloutManager
from ui.widgets import CheckboxTreeview

COLUMNS = [
    ("check", "☐", 40, "center"),
    ("title", "标题", 350, "w"),
    ("time", "时间", 150, "center"),
    ("cwd", "路径", 300, "w"),
    ("provider", "归属", 120, "center"),
    ("archived", "归档", 60, "center"),
]


class CodexTransferApp:
    """Main application window that wires together all modules."""

    def __init__(self) -> None:
        self.config = Config()
        self.db: CodexDB | None = None
        self.rollout: RolloutManager | None = None
        self._threads: list[ThreadRecord] = []
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

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------
    def _setup_window(self) -> None:
        from ui.theme import get_theme_name

        theme = get_theme_name(self.config.theme)
        self.root = ttk.Window(themename=theme)
        self.root.title("Codex Transfer v1.0.0")
        self.root.geometry(self.config.window_geometry)
        self.root.minsize(800, 500)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

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
        frame = ttk.LabelFrame(self.root, text="Codex 路径", padding=5)
        frame.pack(fill=X, padx=10, pady=(10, 5))

        self._path_var = tk.StringVar(value=str(self.config.codex_home))
        self._path_entry = ttk.Entry(frame, textvariable=self._path_var, state="readonly")
        self._path_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

        btn_change = ttk.Button(frame, text="更改", command=self._change_codex_path, bootstyle=SECONDARY)
        btn_change.pack(side=LEFT, padx=(0, 5))

        btn_refresh = ttk.Button(frame, text="刷新", command=self._load_data, bootstyle=INFO)
        btn_refresh.pack(side=LEFT)

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
        frame = ttk.LabelFrame(self.root, text="筛选", padding=5)
        frame.pack(fill=X, padx=10, pady=5)

        # Provider dropdown
        ttk.Label(frame, text="归属:").pack(side=LEFT, padx=(0, 2))
        self._provider_var = tk.StringVar()
        self._provider_combo = ttk.Combobox(frame, textvariable=self._provider_var, state="readonly", width=14)
        self._provider_combo.pack(side=LEFT, padx=(0, 10))

        # CWD dropdown
        ttk.Label(frame, text="路径:").pack(side=LEFT, padx=(0, 2))
        self._cwd_var = tk.StringVar()
        self._cwd_combo = ttk.Combobox(frame, textvariable=self._cwd_var, state="readonly", width=30)
        self._cwd_combo.pack(side=LEFT, padx=(0, 10))

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
        col_headers = [c[1] for c in COLUMNS]

        self._tree = CheckboxTreeview(frame, columns=col_ids[1:], show="tree headings", selectmode="none")
        # Configure #0 as the checkbox header column
        self._tree.heading("#0", text=col_headers[0], anchor="center")
        self._tree.column("#0", width=COLUMNS[0][2], minwidth=COLUMNS[0][2], anchor=COLUMNS[0][3], stretch=False)

        for i, (cid, header, width, anchor) in enumerate(COLUMNS[1:], start=1):
            self._tree.heading(cid, text=header, anchor=anchor,
                               command=lambda c=cid: self._sort_by(c))
            self._tree.column(cid, width=width, minwidth=60, anchor=anchor, stretch=(cid == "title"))

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
        frame = ttk.LabelFrame(self.root, text="操作", padding=5)
        frame.pack(fill=X, padx=10, pady=5)

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

        # Populate filter dropdowns
        providers = self.db.get_distinct_providers()
        cwds = self.db.get_distinct_cwds()

        self._provider_combo["values"] = ["(全部)"] + providers
        self._provider_var.set("(全部)")
        self._cwd_combo["values"] = ["(全部)"] + cwds
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

        threads = self.db.list_threads(
            provider=provider if provider != "(全部)" else None,
            cwd=cwd if cwd != "(全部)" else None,
            keyword=keyword or None,
        )
        self._threads = threads
        self._refresh_table()

    def _refresh_table(self) -> None:
        self._tree.clear_checked()
        for item in self._tree.get_children():
            self._tree.delete(item)

        # Sort data
        def sort_key(t: ThreadRecord) -> Any:
            col = self._sort_column
            if col == "title":
                return t.title or ""
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
            # CheckboxTreeview.insert automatically prepends the checkbox column value
            self._tree.insert("", END, iid=t.id, values=(
                t.title or "(无标题)",
                ts,
                t.cwd or "",
                t.model_provider or "",
                archived_str,
            ))

        self._update_status()

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------
    def _sort_by(self, column: str) -> None:
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
        self._status_var.set(f"共 {total} 条记录，已选 {checked} 条")

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
            self.db.insert_thread(
                thread_id=new_id,
                rollout_path=dst_path,
                created_at=t.created_at,
                updated_at=t.updated_at,
                model_provider=new_provider,
                cwd=t.cwd,
                title=t.title,
            )
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
            self.db.insert_thread(
                thread_id=new_id,
                rollout_path=dst_path,
                created_at=t.created_at,
                updated_at=t.updated_at,
                model_provider=new_name,
                cwd=t.cwd,
                title=t.title,
            )
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
        dialog.title("新建归属")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center over parent
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 350) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")

        result: list[str | None] = [None]

        ttk.Label(dialog, text="请输入新的归属名称:").pack(pady=(20, 5))
        entry_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=entry_var, width=30)
        entry.pack(pady=5)
        entry.focus_set()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)

        def on_ok() -> None:
            name = entry_var.get().strip()
            if name:
                result[0] = name
                dialog.destroy()
            else:
                messagebox.showwarning("输入为空", "归属名称不能为空。", parent=dialog)

        def on_cancel() -> None:
            dialog.destroy()

        ttk.Button(btn_frame, text="确定", command=on_ok, bootstyle=PRIMARY).pack(side=LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=on_cancel, bootstyle=SECONDARY).pack(side=LEFT, padx=10)

        # Enter key submits
        entry.bind("<Return>", lambda _: on_ok())

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
        if values:
            title = values[1] if len(values) > 1 else values[0]
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
