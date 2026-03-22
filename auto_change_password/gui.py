"""Auto Change Password — Giao diện tkinter hiện đại."""

from __future__ import annotations

import threading
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from account_loader import Account, load_file, save_file
from changer import ChangeResult, open_login_page, run_batch


# ══════════════════════════════════════════════════════════════════════════════
# PALETTE & HELPERS
# ══════════════════════════════════════════════════════════════════════════════

_P = {
    "bg":      "#0D1117",
    "panel":   "#161B22",
    "surface": "#21262D",
    "border":  "#30363D",
    "accent":  "#58A6FF",
    "green":   "#2EA043",
    "red":     "#DA3633",
    "orange":  "#D29922",
    "text":    "#C9D1D9",
    "muted":   "#8B949E",
    "dim":     "#484F58",
}

_LOG_TAGS = [
    ("ok",    "#3FB950", ("✔",)),
    ("err",   "#F85149", ("✗",)),
    ("warn",  "#E3B341", ("⚠",)),
    ("start", "#58A6FF", ("▶",)),
    ("step",  "#484F58", ("  →",)),
]

_STATUS_COLORS = {"ok": "#3FB950", "fail": "#F85149", "-": "#484F58"}


def _dk(hex_color: str, f: float = 0.78) -> str:
    """Return a darkened shade of a hex colour."""
    r = max(0, int(int(hex_color[1:3], 16) * f))
    g = max(0, int(int(hex_color[3:5], 16) * f))
    b = max(0, int(int(hex_color[5:7], 16) * f))
    return f"#{r:02x}{g:02x}{b:02x}"


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOM WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

class RBtn(tk.Canvas):
    """Rounded, filled button drawn on a Canvas — no system chrome."""

    def __init__(self, parent: tk.Widget, text: str = "", cmd=None,
                 bg: str | None = None, fg: str = "white",
                 w: int = 120, h: int = 34, r: int = 8,
                 fnt: tuple | None = None, **kw) -> None:
        bg = bg or _P["accent"]
        pbg = parent.cget("bg")
        super().__init__(parent, width=w, height=h,
                         bg=pbg, bd=0, highlightthickness=0, **kw)
        self._t, self._bg, self._fg = text, bg, fg
        self._hc = _dk(bg, 0.82)
        self._pc = _dk(bg, 0.65)
        self._r, self._w, self._h = r, w, h
        self._fnt = fnt or ("Segoe UI", 9, "bold")
        self._cmd = cmd
        self._on  = True
        self.after_idle(self._render, bg, fg)
        self._rebind()

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _render(self, bg: str, fg: str | None = None) -> None:
        w, h, r = self._w, self._h, self._r
        tc = fg or self._fg
        self.delete("all")
        kw: dict = dict(fill=bg, outline=bg)
        self.create_arc(    0,     0, r*2,   r*2, start=90,  extent=90, **kw)
        self.create_arc(w-r*2,     0,   w,   r*2, start=0,   extent=90, **kw)
        self.create_arc(w-r*2, h-r*2,   w,     h, start=270, extent=90, **kw)
        self.create_arc(    0, h-r*2, r*2,     h, start=180, extent=90, **kw)
        self.create_rectangle(  r, 0, w-r,   h, **kw)
        self.create_rectangle(  0, r,   w, h-r, **kw)
        self.create_text(w // 2, h // 2, text=self._t, fill=tc,
                         font=self._fnt, anchor="center")

    # ── Events ────────────────────────────────────────────────────────────────
    def _rebind(self) -> None:
        self.bind("<Enter>",           self._enter)
        self.bind("<Leave>",           self._leave)
        self.bind("<Button-1>",        self._press)
        self.bind("<ButtonRelease-1>", self._release)

    def _unbind_all(self) -> None:
        for ev in ("<Enter>", "<Leave>", "<Button-1>", "<ButtonRelease-1>"):
            self.unbind(ev)

    def _enter(self, _) -> None:
        if self._on:
            self._render(self._hc)
            tk.Canvas.configure(self, cursor="hand2")

    def _leave(self, _) -> None:
        if self._on:
            self._render(self._bg)
            tk.Canvas.configure(self, cursor="")

    def _press(self, _) -> None:
        if self._on:
            self._render(self._pc)

    def _release(self, _) -> None:
        if self._on:
            self._render(self._hc)
            if self._cmd:
                self._cmd()

    # ── Public interface ──────────────────────────────────────────────────────
    def config(self, _opts: dict | None = None, **kw) -> None:  # type: ignore[override]
        if isinstance(_opts, dict):
            kw.update(_opts)
        if "state" in kw:
            s = kw.pop("state")
            self._on = (s == "normal")
            if self._on:
                self._render(self._bg)
                self._rebind()
                tk.Canvas.configure(self, cursor="")
            else:
                self._unbind_all()
                self._render(_P["surface"], _P["dim"])
                tk.Canvas.configure(self, cursor="")
        if "command" in kw:
            self._cmd = kw.pop("command")
        if kw:
            tk.Canvas.configure(self, **kw)

    configure = config  # type: ignore[assignment]


# ══════════════════════════════════════════════════════════════════════════════
# MODEL
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class AppModel:
    url:      str           = ""
    accounts: list[Account] = field(default_factory=list)
    running:  bool          = False

    def stop_requested(self) -> bool:
        return not self.running


# ══════════════════════════════════════════════════════════════════════════════
# VIEW
# ══════════════════════════════════════════════════════════════════════════════

class AppView(tk.Tk):

    # ── Khởi tạo ──────────────────────────────────────────────────────────────
    def __init__(self) -> None:
        super().__init__()
        self.title("Auto Change Password")
        self.minsize(920, 600)
        self.configure(bg=_P["bg"])
        self._setup_styles()
        self._build()
        self.update_idletasks()
        w, h = 1080, 710
        sx, sy = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sx - w) // 2}+{(sy - h) // 2}")

    # ── ttk Styles ────────────────────────────────────────────────────────────
    def _setup_styles(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("Treeview",
                    background=_P["surface"],
                    fieldbackground=_P["surface"],
                    foreground=_P["muted"],
                    rowheight=26,
                    font=("Segoe UI", 9),
                    borderwidth=0)
        s.configure("Treeview.Heading",
                    background=_P["panel"],
                    foreground=_P["dim"],
                    font=("Segoe UI", 8, "bold"),
                    relief="flat")
        s.map("Treeview",
              background=[("selected", _P["accent"])],
              foreground=[("selected", "white")])
        s.map("Treeview.Heading", relief=[("active", "flat")])

        s.configure("prog.Horizontal.TProgressbar",
                    troughcolor=_P["border"],
                    background=_P["accent"],
                    thickness=5)

        s.configure("Vertical.TScrollbar",
                    background=_P["surface"],
                    troughcolor=_P["panel"],
                    borderwidth=0,
                    arrowsize=12)
        s.map("Vertical.TScrollbar",
              background=[("active", _P["border"])])

    # ── Widget factory helpers ─────────────────────────────────────────────────
    def _entry(self, parent: tk.Widget, placeholder: str,
               mask: str = "", width: int = 22) -> tk.Entry:
        e = tk.Entry(
            parent, width=width,
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=_P["border"],
            highlightcolor=_P["accent"],
            font=("Segoe UI", 9),
            bg=_P["surface"], fg=_P["muted"],
            insertbackground=_P["text"],
        )
        e.insert(0, placeholder)
        e.bind("<FocusIn>",
               lambda _: (e.delete(0, "end"),
                          e.config(fg=_P["text"], show=mask))
               if e.get() == placeholder else None)
        e.bind("<FocusOut>",
               lambda _: (e.config(fg=_P["muted"], show=""),
                          e.insert(0, placeholder))
               if not e.get() else None)
        return e

    def _flat_btn(self, parent: tk.Widget, text: str,
                  bg: str = _P["border"], fg: str = "white",
                  fnt: tuple | None = None) -> tk.Button:
        hov = _dk(bg, 0.75)
        b = tk.Button(
            parent, text=text, bg=bg, fg=fg,
            activebackground=hov, activeforeground=fg,
            relief="flat", cursor="hand2",
            padx=10, pady=5, bd=0,
            font=fnt or ("Segoe UI", 8, "bold"),
        )
        b.bind("<Enter>", lambda _: b.config(bg=hov))
        b.bind("<Leave>", lambda _: b.config(bg=bg))
        return b

    def _section_label(self, parent: tk.Widget, text: str) -> None:
        tk.Label(parent, text=text,
                 bg=_P["panel"], fg=_P["dim"],
                 font=("Segoe UI", 7, "bold"),
                 padx=12, pady=6, anchor="w").pack(fill="x")

    def _divider(self, parent: tk.Widget, pady: tuple = (4, 4)) -> None:
        tk.Frame(parent, bg=_P["border"], height=1).pack(
            fill="x", padx=0, pady=pady)

    # ── Build: root layout ────────────────────────────────────────────────────
    def _build(self) -> None:
        self._build_header()
        tk.Frame(self, bg=_P["accent"], height=2).pack(fill="x")

        body = tk.Frame(self, bg=_P["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=(10, 6))

        self._build_toolbar(body)

        content = tk.Frame(body, bg=_P["bg"])
        content.pack(fill="both", expand=True, pady=(10, 0))
        self._build_accounts_panel(content)
        self._build_log_panel(content)

        self._build_statusbar()

    # ── Header ─────────────────────────────────────────────────────────────────
    def _build_header(self) -> None:
        hdr = tk.Frame(self, bg=_P["panel"])
        hdr.pack(fill="x")

        left = tk.Frame(hdr, bg=_P["panel"])
        left.pack(side="left", padx=16, pady=10)
        tk.Label(left, text="🔑  Auto Change Password",
                 bg=_P["panel"], fg=_P["text"],
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(left, text="Tự động đổi mật khẩu hàng loạt tài khoản web",
                 bg=_P["panel"], fg=_P["muted"],
                 font=("Segoe UI", 8)).pack(anchor="w")

        badge = tk.Frame(hdr, bg=_P["panel"])
        badge.pack(side="right", padx=16, pady=14)
        tk.Label(badge, text=" v1.0 ",
                 bg=_P["accent"], fg="white",
                 font=("Segoe UI", 8, "bold"),
                 padx=6, pady=2).pack()

    # ── Toolbar (URL + action buttons) ────────────────────────────────────────
    def _build_toolbar(self, parent: tk.Frame) -> None:
        card = tk.Frame(parent, bg=_P["panel"],
                        highlightbackground=_P["border"],
                        highlightthickness=1)
        card.pack(fill="x")

        # ── Left: URL input ───────────────────────────────────────────────────
        left = tk.Frame(card, bg=_P["panel"])
        left.pack(side="left", fill="x", expand=True, padx=14, pady=12)

        tk.Label(left, text="URL TRANG WEB",
                 bg=_P["panel"], fg=_P["dim"],
                 font=("Segoe UI", 7, "bold")).pack(anchor="w", pady=(0, 5))

        url_row = tk.Frame(left, bg=_P["panel"])
        url_row.pack(fill="x")
        tk.Label(url_row, text="🔗",
                 bg=_P["panel"], fg=_P["muted"],
                 font=("Segoe UI", 11)).pack(side="left", padx=(0, 6))
        self.e_url = self._entry(url_row, "https://example.com/login", width=42)
        self.e_url.pack(side="left", fill="x", expand=True, ipady=7, ipadx=6)

        # ── Right: Action buttons ─────────────────────────────────────────────
        right = tk.Frame(card, bg=_P["panel"])
        right.pack(side="right", padx=14, pady=12)

        row1 = tk.Frame(right, bg=_P["panel"])
        row1.pack(anchor="e", pady=(0, 6))

        self.btn_run = self._flat_btn(row1, "▶  Chạy auto", _P["green"])
        self.btn_run.pack(side="left", padx=(0, 6))

        self.btn_stop = self._flat_btn(row1, "■  Tạm dừng", _P["red"])
        self.btn_stop.pack(side="left")

        row2 = tk.Frame(right, bg=_P["panel"])
        row2.pack(anchor="e")

        self.btn_import = self._flat_btn(row2, "↑  Nhập account",
                                         fnt=("Segoe UI", 8, "bold"))
        self.btn_import.pack(side="left", padx=(0, 6))

        self.btn_export = self._flat_btn(row2, "↓  Xuất kết quả",
                                         fnt=("Segoe UI", 8, "bold"))
        self.btn_export.pack(side="left")

        # ── Progress (inside card, below inputs) ──────────────────────────────
        prog_wrap = tk.Frame(card, bg=_P["panel"])
        prog_wrap.pack(fill="x", padx=14, pady=(0, 10))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(
            prog_wrap, variable=self.progress_var,
            maximum=100, style="prog.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x")

        self.lbl_progress = tk.Label(
            prog_wrap, text="0 / 0",
            bg=_P["panel"], fg=_P["muted"],
            font=("Segoe UI", 7),
        )
        self.lbl_progress.pack(anchor="e", pady=(3, 0))

    # ── Left panel: Accounts ──────────────────────────────────────────────────
    def _build_accounts_panel(self, parent: tk.Frame) -> None:
        panel = tk.Frame(parent, bg=_P["panel"],
                         highlightbackground=_P["border"],
                         highlightthickness=1)
        panel.pack(side="left", fill="both", padx=(0, 8))
        panel.pack_propagate(False)
        panel.configure(width=400)

        # Title bar
        title_row = tk.Frame(panel, bg=_P["panel"])
        title_row.pack(fill="x")
        tk.Label(title_row, text="DANH SÁCH TÀI KHOẢN",
                 bg=_P["panel"], fg=_P["dim"],
                 font=("Segoe UI", 7, "bold"),
                 padx=12, pady=8).pack(side="left")
        self.lbl_count = tk.Label(title_row, text="0",
                                  bg=_P["accent"], fg="white",
                                  font=("Segoe UI", 8, "bold"),
                                  padx=7, pady=2)
        self.lbl_count.pack(side="right", padx=10, pady=8)
        self._divider(panel, (0, 0))

        # Add / Edit form
        form = tk.Frame(panel, bg=_P["panel"])
        form.pack(fill="x", padx=12, pady=(10, 0))

        def _field(lbl: str, ph: str, mask: str = "") -> tk.Entry:
            row = tk.Frame(form, bg=_P["panel"])
            row.pack(fill="x", pady=(0, 5))
            tk.Label(row, text=lbl,
                     bg=_P["panel"], fg=_P["muted"],
                     font=("Segoe UI", 8), width=13, anchor="w").pack(side="left")
            e = self._entry(row, ph, mask=mask, width=22)
            e.pack(side="left", fill="x", expand=True, ipady=5, ipadx=4)
            return e

        self.e_user   = _field("Tài khoản",    "username")
        self.e_old_pw = _field("Mật khẩu cũ",  "old password", mask="*")
        self.e_new_pw = _field("Mật khẩu mới", "new password", mask="*")

        btn_row = tk.Frame(panel, bg=_P["panel"])
        btn_row.pack(fill="x", padx=12, pady=(4, 10))
        self.btn_add    = self._flat_btn(btn_row, "+ Thêm",  _P["green"])
        self.btn_edit   = self._flat_btn(btn_row, "✎ Sửa",   _P["orange"])
        self.btn_delete = self._flat_btn(btn_row, "✕ Xóa",   _P["red"])
        for b in (self.btn_add, self.btn_edit, self.btn_delete):
            b.pack(side="left", padx=(0, 6))

        self._divider(panel, (0, 0))

        # Treeview
        tv_wrap = tk.Frame(panel, bg=_P["panel"])
        tv_wrap.pack(fill="both", expand=True, padx=4, pady=4)

        cols = ("username", "old_password", "new_password", "status")
        self.tree = ttk.Treeview(tv_wrap, columns=cols,
                                 show="headings", selectmode="extended")
        for col, text, w in [
            ("username",     "Tài khoản",    140),
            ("old_password", "Mật khẩu cũ",  100),
            ("new_password", "Mật khẩu mới", 100),
            ("status",       "Trạng thái",    70),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, minwidth=50, anchor="w")

        sb_tv = ttk.Scrollbar(tv_wrap, orient="vertical",
                              command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb_tv.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb_tv.pack(side="left", fill="y")

        # Bottom row
        self._divider(panel, (0, 0))
        bot = tk.Frame(panel, bg=_P["panel"])
        bot.pack(fill="x", padx=12, pady=6)
        self.btn_clear = self._flat_btn(bot, "✕ Xóa tất cả", _P["dim"])
        self.btn_clear.pack(side="right")

    # ── Right panel: Log ──────────────────────────────────────────────────────
    def _build_log_panel(self, parent: tk.Frame) -> None:
        panel = tk.Frame(parent, bg=_P["panel"],
                         highlightbackground=_P["border"],
                         highlightthickness=1)
        panel.pack(side="left", fill="both", expand=True)

        # Title bar
        title_row = tk.Frame(panel, bg=_P["panel"])
        title_row.pack(fill="x")
        tk.Label(title_row, text="LOG HOẠT ĐỘNG",
                 bg=_P["panel"], fg=_P["dim"],
                 font=("Segoe UI", 7, "bold"),
                 padx=12, pady=8).pack(side="left")
        self.btn_clear_log = self._flat_btn(title_row, "Xóa log", _P["dim"],
                                            fnt=("Segoe UI", 7, "bold"))
        self.btn_clear_log.pack(side="right", padx=8, pady=5)
        self._divider(panel, (0, 0))

        # Log text
        log_wrap = tk.Frame(panel, bg=_P["surface"])
        log_wrap.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_wrap, relief="flat", bd=0, highlightthickness=0,
            state="disabled", wrap="word",
            font=("Consolas", 9), bg=_P["surface"], fg=_P["muted"],
            padx=14, pady=10, spacing1=3,
        )
        for tag, color, _ in _LOG_TAGS:
            self.log_text.tag_config(tag, foreground=color)

        sb_log = ttk.Scrollbar(log_wrap, orient="vertical",
                               command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb_log.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        sb_log.pack(side="left", fill="y")

    # ── Status bar ────────────────────────────────────────────────────────────
    def _build_statusbar(self) -> None:
        tk.Frame(self, bg=_P["border"], height=1).pack(fill="x")
        sb = tk.Frame(self, bg=_P["panel"])
        sb.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="● Sẵn sàng")
        tk.Label(sb, textvariable=self.status_var,
                 bg=_P["panel"], fg=_P["muted"],
                 font=("Segoe UI", 8), padx=12, pady=5, anchor="w").pack(fill="x")

    # ══════════════════════════════════════════════════════════════════════════
    # PUBLIC HELPERS (used by Controller)
    # ══════════════════════════════════════════════════════════════════════════

    def _val(self, entry: tk.Entry, placeholder: str) -> str:
        v = entry.get()
        return "" if v == placeholder else v

    def get_url(self)    -> str: return self._val(self.e_url,   "https://example.com/login")
    def get_user(self)   -> str: return self._val(self.e_user,  "username")
    def get_old_pw(self) -> str: return self._val(self.e_old_pw, "old password")
    def get_new_pw(self) -> str: return self._val(self.e_new_pw, "new password")

    def clear_add_form(self) -> None:
        for e, ph, mask in (
            (self.e_user,   "username",     ""),
            (self.e_old_pw, "old password", "*"),
            (self.e_new_pw, "new password", "*"),
        ):
            e.config(fg=_P["muted"], show="")
            e.delete(0, "end")
            e.insert(0, ph)

    # ── Treeview helpers ──────────────────────────────────────────────────────
    def tree_append(self, acc: Account) -> str:
        iid = self.tree.insert(
            "", "end",
            values=(acc.username,
                    "•" * len(acc.old_password),
                    "•" * len(acc.new_password),
                    acc.status),
            tags=(acc.status,),
        )
        for tag, color in _STATUS_COLORS.items():
            self.tree.tag_configure(tag, foreground=color)
        self.lbl_count.config(text=str(self.tree_count()))
        return iid

    def tree_update_status(self, iid: str, status: str) -> None:
        self.tree.set(iid, "status", status)
        self.tree.item(iid, tags=(status,))

    def tree_selected_iid(self) -> str | None:
        sel = self.tree.selection()
        return sel[0] if sel else None

    def tree_delete_selected(self) -> None:
        for iid in self.tree.selection():
            self.tree.delete(iid)
        self.lbl_count.config(text=str(self.tree_count()))

    def tree_clear(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.lbl_count.config(text="0")

    def tree_count(self) -> int:
        return len(self.tree.get_children())

    def tree_get_values(self) -> list[tuple]:
        return [self.tree.item(iid)["values"]
                for iid in self.tree.get_children()]

    # ── Log helpers ───────────────────────────────────────────────────────────
    def log(self, msg: str) -> None:
        self.after(0, self._log_append, msg)

    def _log_append(self, msg: str) -> None:
        tag = ""
        for t, _, prefixes in _LOG_TAGS:
            if any(msg.lstrip().startswith(p) for p in prefixes):
                tag = t
                break
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def log_clear(self) -> None:
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    # ── Status & progress ──────────────────────────────────────────────────────
    def set_status(self, msg: str) -> None:
        self.after(0, lambda: self.status_var.set(msg))

    def set_progress(self, done: int, total: int) -> None:
        pct = (done / total * 100) if total else 0
        self.after(0, lambda: self.progress_var.set(pct))
        self.after(0, lambda: self.lbl_progress.config(text=f"{done} / {total}"))


# ══════════════════════════════════════════════════════════════════════════════
# CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════

class AppController:
    def __init__(self) -> None:
        self.model = AppModel()
        self.view  = AppView()
        self._iid_map: dict[str, Account] = {}
        self._bind()

    def _bind(self) -> None:
        v = self.view
        v.btn_add.config(command=self._on_add)
        v.btn_edit.config(command=self._on_edit)
        v.btn_delete.config(command=self._on_delete)
        v.btn_clear.config(command=self._on_clear_list)
        v.btn_import.config(command=self._on_import)
        v.btn_export.config(command=self._on_export)
        v.btn_run.config(command=self._on_run)
        v.btn_stop.config(command=self._on_stop)
        v.btn_clear_log.config(command=v.log_clear)

    # ── Thêm / Sửa / Xóa tài khoản ───────────────────────────────────────────
    def _on_add(self) -> None:
        user   = self.view.get_user()
        old_pw = self.view.get_old_pw()
        new_pw = self.view.get_new_pw()

        if not user:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên tài khoản.")
            return
        if not old_pw:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập mật khẩu cũ.")
            return
        if not new_pw:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập mật khẩu mới.")
            return

        acc = Account(username=user, old_password=old_pw, new_password=new_pw)
        self.model.accounts.append(acc)
        iid = self.view.tree_append(acc)
        self._iid_map[iid] = acc
        self.view.clear_add_form()
        self.view.log(f"✔ Đã thêm tài khoản: {user}")

    def _on_edit(self) -> None:
        iid = self.view.tree_selected_iid()
        if not iid:
            messagebox.showinfo("Chọn tài khoản", "Vui lòng chọn tài khoản cần sửa.")
            return
        acc = self._iid_map.get(iid)
        if not acc:
            return

        user   = self.view.get_user()   or acc.username
        old_pw = self.view.get_old_pw() or acc.old_password
        new_pw = self.view.get_new_pw() or acc.new_password

        acc.username = user; acc.old_password = old_pw
        acc.new_password = new_pw; acc.status = "-"

        self.view.tree.set(iid, "username",     user)
        self.view.tree.set(iid, "old_password", "•" * len(old_pw))
        self.view.tree.set(iid, "new_password", "•" * len(new_pw))
        self.view.tree.set(iid, "status",       "-")
        self.view.tree.item(iid, tags=("-",))
        self.view.clear_add_form()
        self.view.log(f"✔ Đã cập nhật: {user}")

    def _on_delete(self) -> None:
        iids = self.view.tree.selection()
        if not iids:
            return
        for iid in iids:
            acc = self._iid_map.pop(iid, None)
            if acc and acc in self.model.accounts:
                self.model.accounts.remove(acc)
        self.view.tree_delete_selected()

    def _on_clear_list(self) -> None:
        if not messagebox.askyesno("Xác nhận", "Xóa toàn bộ danh sách tài khoản?"):
            return
        self.model.accounts.clear()
        self._iid_map.clear()
        self.view.tree_clear()

    # ── Import / Export ────────────────────────────────────────────────────────
    def _on_import(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn file tài khoản",
            filetypes=[("CSV / Excel", "*.csv *.xlsx *.xls"), ("Tất cả", "*.*")],
        )
        if not path:
            return
        try:
            accounts = load_file(path)
        except Exception as exc:
            messagebox.showerror("Lỗi đọc file", str(exc))
            return

        for acc in accounts:
            self.model.accounts.append(acc)
            iid = self.view.tree_append(acc)
            self._iid_map[iid] = acc

        self.view.log(f"✔ Đã nhập {len(accounts)} tài khoản từ {Path(path).name}")

    def _on_export(self) -> None:
        if not self.model.accounts:
            messagebox.showinfo("Trống", "Chưa có tài khoản nào để xuất.")
            return
        path = filedialog.asksaveasfilename(
            title="Lưu kết quả",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")],
        )
        if not path:
            return
        try:
            save_file(self.model.accounts, path)
            self.view.log(
                f"✔ Đã xuất {len(self.model.accounts)} tài khoản → {Path(path).name}")
        except Exception as exc:
            messagebox.showerror("Lỗi lưu file", str(exc))

    # ── Chạy tự động ──────────────────────────────────────────────────────────
    def _on_run(self) -> None:
        if self.model.running:
            return

        self.model.running = True
        self.view.btn_run.config(state="disabled")
        self.view.set_status("● Đang chạy...")

        def _worker() -> None:
            try:
                open_login_page(
                    stop_flag=self.model.stop_requested,
                    log=self.view.log,
                )
            except Exception as exc:
                self.view.log(f"✗ Lỗi: {exc}")
            finally:
                self.model.running = False
                self.view.after(0, lambda: self.view.btn_run.config(state="normal"))
                self.view.set_status("● Sẵn sàng")

        threading.Thread(target=_worker, daemon=True).start()

    def _on_stop(self) -> None:
        if self.model.running:
            self.model.running = False
            self.view.log("⚠ Yêu cầu dừng...")
            self.view.set_status("● Đang dừng...")

    def run(self) -> None:
        self.view.mainloop()
