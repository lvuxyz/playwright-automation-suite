"""Auto Tool — Playwright + tkinter (MVC)."""

import threading
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import filedialog, messagebox


# ── Model ─────────────────────────────────────────────────────────────
@dataclass
class AppModel:
    url: str = ""
    accounts: list[tuple[str, str]] = field(default_factory=list)


# ── View ──────────────────────────────────────────────────────────────
class AppView(tk.Tk):
    _BG       = "#0F1923"   # app background
    _PANEL    = "#162230"   # card / panel
    _SURFACE  = "#1C2E3F"   # input / listbox surface
    _BORDER   = "#263545"   # subtle border
    _HDR      = "#0A1520"   # header strip
    _ACCENT   = "#1976D2"   # primary blue accent

    _COLORS: dict[str, dict] = {
        "green":  {"bg": "#2E7D32", "ab": "#1B5E20", "fg": "white"},
        "blue":   {"bg": "#1565C0", "ab": "#0D47A1", "fg": "white"},
        "red":    {"bg": "#C62828", "ab": "#7F0000", "fg": "white"},
        "orange": {"bg": "#E65100", "ab": "#BF360C", "fg": "white"},
        "purple": {"bg": "#6A1B9A", "ab": "#4A148C", "fg": "white"},
        "teal":   {"bg": "#00695C", "ab": "#004D40", "fg": "white"},
        "gray":   {"bg": "#37474F", "ab": "#263238", "fg": "white"},
    }

    # Log tag → (text_color, prefix_triggers)
    _LOG_TAGS: list[tuple[str, str, tuple]] = [
        ("ok",    "#66BB6A", ("✔",)),
        ("err",   "#EF5350", ("✗", "  ✗")),
        ("warn",  "#FFA726", ("⚠", "  ⚠")),
        ("start", "#42A5F5", ("▶",)),
        ("acct",  "#CE93D8", ("[",)),
        ("step",  "#455A64", ("  →", "→")),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.title("Auto Tool")
        self.minsize(720, 600)
        self.configure(bg=self._BG)
        self._build()
        self.update_idletasks()
        w, h = 860, 660
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")

    # ------------------------------------------------------------------
    def _entry(self, parent, placeholder: str, mask: str = "") -> tk.Entry:
        e = tk.Entry(
            parent, width=26, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=self._BORDER,
            highlightcolor=self._ACCENT, font=("Segoe UI", 10),
            bg=self._SURFACE, fg="#607D8B", insertbackground="#90A4AE",
        )
        e.insert(0, placeholder)
        e.bind("<FocusIn>",  lambda _: (e.delete(0, "end"), e.config(fg="#ECEFF1", show=mask))
                                       if e.get() == placeholder else None)
        e.bind("<FocusOut>", lambda _: (e.config(fg="#607D8B", show=""), e.insert(0, placeholder))
                                       if not e.get() else None)
        return e

    def _btn(self, parent, text: str, color: str = "gray",
             width: int | None = None) -> tk.Button:
        c = self._COLORS[color]
        kw: dict = dict(
            text=text, bg=c["bg"], fg=c["fg"],
            activebackground=c["ab"], activeforeground="white",
            relief="flat", cursor="hand2",
            padx=12, pady=6,
            font=("Segoe UI", 9, "bold"), bd=0,
        )
        if width:
            kw["width"] = width
        b = tk.Button(parent, **kw)
        b.bind("<Enter>", lambda _: b.config(bg=c["ab"]))
        b.bind("<Leave>", lambda _: b.config(bg=c["bg"]))
        return b

    def _sep(self, parent) -> None:
        tk.Frame(parent, bg=self._BORDER, height=1).pack(fill="x", padx=10, pady=4)

    # ------------------------------------------------------------------
    def _build(self) -> None:
        # ── Header ──────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=self._HDR)
        hdr.pack(fill="x")
        # left: title + subtitle
        hl = tk.Frame(hdr, bg=self._HDR)
        hl.pack(side="left", padx=16, pady=10)
        tk.Label(hl, text="⚙  Auto Tool", bg=self._HDR, fg="#ECEFF1",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(hl, text="Công cụ tự động đăng nhập Playwright",
                 bg=self._HDR, fg="#455A64",
                 font=("Segoe UI", 8)).pack(anchor="w")
        # right: badge
        tk.Label(hdr, text=" v1.0 ", bg=self._ACCENT, fg="white",
                 font=("Segoe UI", 8, "bold"),
                 padx=6, pady=2).pack(side="right", padx=14, pady=14)
        # accent bar below header
        tk.Frame(self, bg=self._ACCENT, height=2).pack(fill="x")

        # ── Body (2 columns) ────────────────────────────────────────
        body = tk.Frame(self, bg=self._BG)
        body.pack(fill="both", expand=True, padx=12, pady=10)

        # ── LEFT COLUMN ─────────────────────────────────────────────
        lc = tk.Frame(body, bg=self._BG)
        lc.pack(side="left", fill="both")

        # Input panel
        inp = tk.Frame(lc, bg=self._PANEL,
                       highlightbackground=self._BORDER, highlightthickness=1)
        inp.pack(fill="x", pady=(0, 8))

        def field_lbl(parent, text: str) -> None:
            tk.Label(parent, text=text, bg=self._PANEL, fg="#546E7A",
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(
                fill="x", padx=12, pady=(8, 2))

        def irow() -> tk.Frame:
            f = tk.Frame(inp, bg=self._PANEL)
            f.pack(fill="x", padx=12, pady=(0, 6))
            return f

        field_lbl(inp, "URL TRANG WEB")
        r0 = irow()
        self.e_url = self._entry(r0, "https://")
        self.e_url.pack(side="left", ipady=5, ipadx=4, fill="x", expand=True)
        self.btn_open = self._btn(r0, "Chrome", "purple")
        self.btn_open.pack(side="left", padx=(6, 0))

        self._sep(inp)

        field_lbl(inp, "TÀI KHOẢN")
        r1 = irow()
        self.e_user = self._entry(r1, "tài khoản")
        self.e_user.pack(side="left", ipady=5, ipadx=4)
        self.btn_add = self._btn(r1, "+ Thêm", "green")
        self.btn_add.pack(side="left", padx=(6, 0))

        field_lbl(inp, "MẬT KHẨU")
        r2 = irow()
        self.e_pass = self._entry(r2, "mật khẩu", mask="*")
        self.e_pass.pack(side="left", ipady=5, ipadx=4)
        self.btn_run = self._btn(r2, "▶  Chạy Auto", "blue")
        self.btn_run.pack(side="left", padx=(6, 0))

        # Account list panel
        list_pan = tk.Frame(lc, bg=self._PANEL,
                            highlightbackground=self._BORDER, highlightthickness=1)
        list_pan.pack(fill="both", expand=True, pady=(0, 8))

        # list header bar
        lh = tk.Frame(list_pan, bg=self._HDR)
        lh.pack(fill="x")
        tk.Label(lh, text="DANH SÁCH TÀI KHOẢN", bg=self._HDR, fg="#546E7A",
                 font=("Segoe UI", 8, "bold"), padx=10, pady=7).pack(side="left")
        self.lbl_count = tk.Label(lh, text="0", bg=self._ACCENT, fg="white",
                                  font=("Segoe UI", 8, "bold"), padx=8, pady=3)
        self.lbl_count.pack(side="right", padx=8, pady=6)

        self.listbox = tk.Listbox(
            list_pan, relief="flat", bd=0, highlightthickness=0,
            selectbackground=self._ACCENT, selectforeground="#FFFFFF",
            activestyle="none", font=("Segoe UI", 9),
            bg=self._PANEL, fg="#90A4AE",
        )
        sb_l = tk.Scrollbar(list_pan, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb_l.set)
        self.listbox.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=4)
        sb_l.pack(side="left", fill="y", pady=4)

        # list action buttons
        la = tk.Frame(list_pan, bg=self._HDR)
        la.pack(fill="x")
        self.btn_edit   = self._btn(la, "✎ Sửa",      "orange")
        self.btn_delete = self._btn(la, "✕ Xóa",      "red")
        self.btn_clear  = self._btn(la, "Xóa tất cả", "gray")
        for b in (self.btn_edit, self.btn_delete, self.btn_clear):
            b.pack(side="left", padx=4, pady=6)

        # import / export row
        io = tk.Frame(lc, bg=self._BG)
        io.pack(fill="x")
        self.btn_import = self._btn(io, "↑ Nhập .txt", "teal")
        self.btn_export = self._btn(io, "↓ Xuất .txt", "teal")
        self.btn_import.pack(side="left", padx=(0, 4))
        self.btn_export.pack(side="left")

        # ── RIGHT COLUMN — Log ──────────────────────────────────────
        rc = tk.Frame(body, bg=self._BG)
        rc.pack(side="left", fill="both", expand=True, padx=(10, 0))

        log_pan = tk.Frame(rc, bg=self._HDR,
                           highlightbackground=self._BORDER, highlightthickness=1)
        log_pan.pack(fill="both", expand=True)

        # log header bar
        rh = tk.Frame(log_pan, bg=self._HDR)
        rh.pack(fill="x")
        tk.Label(rh, text="LOG HOẠT ĐỘNG", bg=self._HDR, fg="#546E7A",
                 font=("Segoe UI", 8, "bold"), padx=10, pady=7).pack(side="left")
        self.btn_clear_log = self._btn(rh, "Xóa log", "gray")
        self.btn_clear_log.pack(side="right", padx=6, pady=4)
        tk.Frame(log_pan, bg=self._BORDER, height=1).pack(fill="x")

        self.log = tk.Text(
            log_pan, relief="flat", bd=0, highlightthickness=0,
            state="disabled", wrap="word",
            font=("Consolas", 9), bg=self._HDR, fg="#455A64",
            padx=10, pady=8, spacing1=2,
        )
        for tag, color, _ in self._LOG_TAGS:
            self.log.tag_config(tag, foreground=color)
        sb_r = tk.Scrollbar(log_pan, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=sb_r.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb_r.pack(side="left", fill="y")

        # ── Status bar ──────────────────────────────────────────────
        tk.Frame(self, bg=self._BORDER, height=1).pack(fill="x")
        sb_frame = tk.Frame(self, bg=self._HDR)
        sb_frame.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="● Sẵn sàng")
        tk.Label(sb_frame, textvariable=self.status_var,
                 bg=self._HDR, fg="#37474F",
                 font=("Segoe UI", 8), padx=12, pady=4, anchor="w").pack(fill="x")

    # ------------------------------------------------------------------
    def get_url(self)  -> str: return "" if (v := self.e_url.get())  == "https://"  else v
    def get_user(self) -> str: return "" if (v := self.e_user.get()) == "tài khoản" else v
    def get_pass(self) -> str: return "" if (v := self.e_pass.get()) == "mật khẩu"  else v

    def clear_inputs(self) -> None:
        for e, ph in ((self.e_user, "tài khoản"), (self.e_pass, "mật khẩu")):
            e.config(fg="#607D8B", show="")
            e.delete(0, "end")
            e.insert(0, ph)

    def append_list(self, text: str) -> None:
        self.listbox.insert("end", text)

    def update_count(self) -> None:
        n = self.listbox.size()
        self.lbl_count.config(text=str(n))

    def set_status(self, msg: str, color: str = "#37474F") -> None:
        self.after(0, lambda: self.status_var.set(msg))
        self.after(0, lambda: self.nametowidget(
            self.status_var.get()   # dummy — use direct widget ref below
        ) if False else None)
        # update label color via a stored reference
        if not hasattr(self, "_status_lbl"):
            for w in self.winfo_children():
                if isinstance(w, tk.Frame):
                    for child in w.winfo_children():
                        if isinstance(child, tk.Label) and child.cget("textvariable"):
                            self._status_lbl = child
        if hasattr(self, "_status_lbl"):
            self.after(0, lambda c=color: self._status_lbl.config(fg=c))

    def write_log(self, msg: str) -> None:
        def _tag() -> str:
            for tag, _, prefixes in self._LOG_TAGS:
                if any(msg.startswith(p) for p in prefixes):
                    return tag
            return ""

        def _w() -> None:
            self.log.config(state="normal")
            t = _tag()
            if t:
                self.log.insert("end", msg + "\n", t)
            else:
                self.log.insert("end", msg + "\n")
            self.log.see("end")
            self.log.config(state="disabled")
        self.after(0, _w)

    def clear_log(self) -> None:
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")


# ── Controller ────────────────────────────────────────────────────────
class AppController:
    def __init__(self, model: AppModel, view: AppView) -> None:
        self.m, self.v = model, view
        view.btn_add.config(command=self.add_account)
        view.btn_run.config(command=self.run_auto)
        view.btn_open.config(command=self.open_chrome)
        view.btn_import.config(command=self.import_file)
        view.btn_export.config(command=self.export_file)
        view.btn_delete.config(command=self.delete_account)
        view.btn_edit.config(command=self.edit_account)
        view.btn_clear.config(command=self.clear_accounts)
        view.btn_clear_log.config(command=self.v.clear_log)
        self._load_test_data()

    def _load_test_data(self) -> None:
        try:
            from config import BASE_URL, TEST_ACCOUNTS
        except ImportError:
            return
        self.v.e_url.delete(0, "end")
        self.v.e_url.config(fg="#ECEFF1")
        self.v.e_url.insert(0, BASE_URL)
        for user, pwd in TEST_ACCOUNTS:
            self.m.accounts.append((user, pwd))
            self.v.append_list(f"{user}  |  {'*' * len(pwd)}")
        self.v.update_count()

    def open_chrome(self) -> None:
        url = self.v.get_url()
        if not url:
            self.v.write_log("⚠ Vui lòng nhập URL trước.")
            return
        self.v.btn_open.config(state="disabled", text="đang mở…")
        self.v.set_status("⏳ Đang mở Chrome…", "#42A5F5")
        threading.Thread(target=self._open_worker, args=(url,), daemon=True).start()

    def _open_worker(self, url: str) -> None:
        log = self.v.write_log
        log(f"▶ Mở Chrome: {url}")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                page.wait_for_load_state("networkidle", timeout=15_000)
                log("✔ Trang đã load xong.")
                _save_url_to_config(url)
                log("✔ Đã lưu URL vào config.py")
                self.v.set_status("✔ Chrome đã mở", "#66BB6A")
            except Exception as exc:
                log(f"✗ Lỗi: {exc}")
                self.v.set_status("✗ Lỗi mở Chrome", "#EF5350")
            finally:
                browser.close()
        self.v.after(0, lambda: self.v.btn_open.config(state="normal", text="Chrome"))

    def add_account(self) -> None:
        user, pwd = self.v.get_user(), self.v.get_pass()
        if not user:
            self.v.write_log("⚠ Vui lòng nhập tài khoản.")
            return
        self.m.accounts.append((user, pwd))
        self.v.append_list(f"{user}  |  {'*' * len(pwd)}")
        self.v.write_log(f"✔ Đã thêm: {user}")
        self.v.clear_inputs()
        self.v.update_count()

    def delete_account(self) -> None:
        sel = self.v.listbox.curselection()
        if not sel:
            self.v.write_log("⚠ Chọn tài khoản cần xóa.")
            return
        idx = sel[0]
        user, _ = self.m.accounts[idx]
        self.m.accounts.pop(idx)
        self.v.listbox.delete(idx)
        self.v.write_log(f"✔ Đã xóa: {user}")
        self.v.update_count()

    def edit_account(self) -> None:
        sel = self.v.listbox.curselection()
        if not sel:
            self.v.write_log("⚠ Chọn tài khoản cần sửa.")
            return
        idx = sel[0]
        user, pwd = self.m.accounts[idx]

        v = self.v
        dlg = tk.Toplevel(v)
        dlg.title("Sửa tài khoản")
        dlg.resizable(False, False)
        dlg.configure(bg=v._PANEL)
        dlg.grab_set()
        w, h = 360, 230
        dlg.geometry(f"{w}x{h}+{(dlg.winfo_screenwidth()-w)//2}+{(dlg.winfo_screenheight()-h)//2}")

        # dialog header
        dh = tk.Frame(dlg, bg=v._HDR)
        dh.pack(fill="x")
        tk.Label(dh, text="Sửa tài khoản", bg=v._HDR, fg="#90CAF9",
                 font=("Segoe UI", 10, "bold"), padx=14, pady=8).pack(side="left")
        tk.Frame(dlg, bg=v._BORDER, height=1).pack(fill="x")

        body = tk.Frame(dlg, bg=v._PANEL, padx=16, pady=12)
        body.pack(fill="both", expand=True)

        def field_row(label: str) -> tk.Entry:
            tk.Label(body, text=label, bg=v._PANEL, fg="#546E7A",
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(6, 2))
            e = tk.Entry(body, font=("Segoe UI", 10), relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=v._BORDER,
                         highlightcolor=v._ACCENT,
                         bg=v._SURFACE, fg="#ECEFF1", insertbackground="#90A4AE")
            e.pack(fill="x", ipady=5)
            return e

        e_u = field_row("Tài khoản")
        e_u.insert(0, user)
        e_p = field_row("Mật khẩu")
        e_p.config(show="*")
        e_p.insert(0, pwd)

        def save() -> None:
            new_user = e_u.get().strip()
            new_pwd  = e_p.get()
            if not new_user:
                return
            self.m.accounts[idx] = (new_user, new_pwd)
            self.v.listbox.delete(idx)
            self.v.listbox.insert(idx, f"{new_user}  |  {'*' * len(new_pwd)}")
            self.v.listbox.selection_set(idx)
            self.v.write_log(f"✔ Đã sửa: {user} → {new_user}")
            dlg.destroy()

        tk.Frame(dlg, bg=v._BORDER, height=1).pack(fill="x")
        btn_row = tk.Frame(dlg, bg=v._HDR, padx=12, pady=8)
        btn_row.pack(fill="x")
        v._btn(btn_row, "  Lưu  ", "green").pack(side="left", padx=(0, 6))
        v._btn(btn_row, "  Hủy  ", "gray").pack(side="left")
        btn_row.winfo_children()[0].config(command=save)
        btn_row.winfo_children()[1].config(command=dlg.destroy)

        dlg.bind("<Return>", lambda _: save())
        dlg.bind("<Escape>", lambda _: dlg.destroy())
        e_u.focus_set()

    def clear_accounts(self) -> None:
        if not self.m.accounts:
            self.v.write_log("⚠ Danh sách đã trống.")
            return
        if messagebox.askyesno("Xác nhận", "Xóa toàn bộ danh sách tài khoản?", parent=self.v):
            count = len(self.m.accounts)
            self.m.accounts.clear()
            self.v.listbox.delete(0, "end")
            self.v.write_log(f"✔ Đã xóa {count} tài khoản.")
            self.v.update_count()

    def import_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn file tài khoản",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        added = skipped = 0
        # utf-8-sig tự bỏ BOM nếu file được lưu từ Notepad Windows
        for raw in open(path, encoding="utf-8-sig", errors="replace"):
            line = raw.strip()
            if not line:
                continue
            sep = line.find("|")
            if sep == -1:
                skipped += 1
                continue
            user = line[:sep].strip()
            pwd  = line[sep + 1:]          # không strip password — tránh cắt khoảng trắng hợp lệ
            if not user:
                skipped += 1
                continue
            self.m.accounts.append((user, pwd))
            self.v.append_list(f"{user}  |  {'*' * len(pwd)}")
            added += 1

        msg = f"✔ Đã nhập {added} tài khoản từ file."
        if skipped:
            msg += f" ({skipped} dòng không hợp lệ bị bỏ qua)"
        self.v.write_log(msg)
        self.v.update_count()

    def export_file(self) -> None:
        if not self.m.accounts:
            self.v.write_log("⚠ Danh sách trống, không có gì để xuất.")
            return
        path = filedialog.asksaveasfilename(
            title="Lưu file tài khoản",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="accounts.txt",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            for user, pwd in self.m.accounts:
                f.write(f"{user}|{pwd}\n")
        self.v.write_log(f"✔ Đã xuất {len(self.m.accounts)} tài khoản → {path}")

    def run_auto(self) -> None:
        if not self.m.accounts:
            self.v.write_log("⚠ Chưa có tài khoản nào trong danh sách.")
            return
        if not (url := self.v.get_url()):
            self.v.write_log("⚠ Vui lòng nhập URL trang web.")
            return
        self.m.url = url
        self.v.btn_run.config(state="disabled", text="đang chạy…")
        self.v.set_status(f"⏳ Đang chạy {len(self.m.accounts)} tài khoản…", "#42A5F5")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self) -> None:
        log, accs, url = self.v.write_log, self.m.accounts, self.m.url
        log(f"▶ Bắt đầu {len(accs)} tài khoản — {url}")
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=False)
        for i, (user, pwd) in enumerate(accs, 1):
            log(f"[{i}/{len(accs)}] {user}")
            self.v.set_status(f"⏳ [{i}/{len(accs)}] {user}", "#42A5F5")
            ctx = browser.new_context()
            try:
                run_flow(ctx.new_page(), url, user, pwd, log)
            except Exception as exc:
                log(f"  ✗ {exc}")
            finally:
                ctx.close()
                log(f"  → Đã đóng tab: {user}")
        log("✔ Hoàn thành tất cả tài khoản.")
        self.v.set_status("✔ Hoàn thành", "#66BB6A")
        self.v.after(0, lambda: self.v.btn_run.config(state="normal", text="▶  Chạy Auto"))


# ── Automation flow (chỉnh tại đây) ──────────────────────────────────
def run_flow(page, url: str, username: str, password: str, log) -> None:
    try:
        from config import SELECTORS
    except ImportError:
        log("  ⚠ Chưa có config.py — bỏ qua luồng thật.")
        return

    page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_load_state("networkidle", timeout=15_000)

    # ── Bước 1: Click nút Đăng Nhập (trong iframe event) ──────────────
    event_frame = next((f for f in page.frames if "event.vnggames.com" in f.url), None)
    if not event_frame:
        log("  ✗ Không tìm thấy iframe event — kiểm tra URL.")
        return
    event_frame.click(SELECTORS["iframe_login_btn"])
    page.wait_for_timeout(1500)
    log("  → Đã bấm Đăng Nhập")

    # ── Bước 2: Chọn Email trong modal (Frame0) ───────────────────────
    main = page.frames[0]
    main.click(SELECTORS["email_method"])
    page.wait_for_timeout(1000)
    log("  → Đã chọn Email")

    # ── Bước 3: Nhập email → Continue ────────────────────────────────
    main.fill(SELECTORS["email_input"], username)
    main.click(SELECTORS["continue_btn"])
    log("  → Đã nhập email, bấm Continue")

    # ── Bước 4: Chờ ô mật khẩu → nhập → Submit ───────────────────────
    main.wait_for_selector(SELECTORS["password_input"], state="visible", timeout=10_000)
    main.fill(SELECTORS["password_input"], password)
    main.click(SELECTORS["submit_btn"])
    page.wait_for_load_state("networkidle", timeout=15_000)
    log(f"  ✔ Đăng nhập: {username}")

    # ── Bước 5: Reload lấy lại event_frame sau khi login ─────────────
    # Sau khi đăng nhập, trang có thể reload → cần lấy lại frame
    page.wait_for_timeout(2_000)
    event_frame = next((f for f in page.frames if "event.vnggames.com" in f.url), None)
    if not event_frame:
        log("  ✗ Không tìm thấy iframe event sau đăng nhập.")
        return

    log(f"  ✔ Hoàn thành đăng nhập: {username}")

    # ── Bước 6: Click nút "Nhận lượt" (mở modal danh sách nhiệm vụ) ──
    log("  → [Bước 6] Tìm nút mở modal nhiệm vụ (a.btn-show-all)...")
    try:
        btn = event_frame.wait_for_selector(SELECTORS["nhan_luot_btn"], state="attached", timeout=10_000)
        log("  → [Bước 6] Tìm thấy nút, đang dispatch click...")
        btn.dispatch_event("click")
        page.wait_for_timeout(1_500)
        log("  ✔ [Bước 6] Đã bấm mở modal nhiệm vụ")
    except Exception as e:
        log(f"  ✗ [Bước 6] Không tìm thấy nút mở modal: {e}")
        return

    # ── Bước 7: Chờ modal danh sách nhiệm vụ xuất hiện ───────────────
    log("  → [Bước 7] Chờ modal .MS__content xuất hiện...")
    try:
        event_frame.wait_for_selector(".MS__content", state="visible", timeout=10_000)
        log("  ✔ [Bước 7] Modal nhiệm vụ đã mở")
    except Exception as e:
        log(f"  ✗ [Bước 7] Modal không xuất hiện: {e}")
        return

    # ── Bước 8-13: Lặp qua tất cả 6 nhiệm vụ ────────────────────────
    log("  → [Bước 8] Bắt đầu xử lý 6 nhiệm vụ...")
    for task_idx in range(1, 7):
        log(f"\n  ── Nhiệm vụ {task_idx}/6 " + "─" * 30)
        _handle_task(event_frame, page, log, task_idx)
        page.wait_for_timeout(800)

    # Đóng popup_getlist sau khi xong
    log("  → Đóng danh sách nhiệm vụ...")
    _close_popup(event_frame, page, log)
    log(f"  ✔ Hoàn thành tất cả 6 nhiệm vụ cho: {username}")

    # ── Bước 14: Rút lượt tự động ─────────────────────────────────────
    page.wait_for_timeout(2_000)   # đợi DOM cập nhật số lượt sau khi đóng popup
    _spin_all(event_frame, page, log)


def _handle_task(event_frame, page, log, task_idx: int) -> None:
    """Xử lý một nhiệm vụ trong danh sách #popup_getlist.

    Luồng:
      click Nhận Lượt
        → popup_condition mở  → click Xác nhận → kiểm tra kết quả → đóng về getlist
        → popup_inform mở     → đọc thông báo                      → đóng về getlist
    """
    btn_sel  = (f"#popup_getlist .table_history tbody"
                f" tr:nth-child({task_idx}) a.pm__menu-ajax-custom")
    name_sel = (f"#popup_getlist .table_history tbody"
                f" tr:nth-child({task_idx}) td:nth-child(2)")

    # ── Đọc tên nhiệm vụ ──────────────────────────────────────────────
    try:
        name_el = event_frame.query_selector(name_sel)
        name = name_el.inner_text().strip().replace("\n", " ") if name_el else f"Task {task_idx}"
    except Exception:
        name = f"Task {task_idx}"
    log(f"  → Nhiệm vụ: {name}")

    # ── Click "Nhận Lượt" ─────────────────────────────────────────────
    log(f"  → Click Nhận Lượt...")
    try:
        btn = event_frame.wait_for_selector(btn_sel, state="attached", timeout=5_000)
        btn.click()
        page.wait_for_timeout(2_000)
    except Exception as e:
        log(f"  ✗ Không click được nút: {e}")
        return

    # ── Xác định popup nào đang nổi lên ──────────────────────────────
    try:
        active_id = event_frame.evaluate("""() => {
            const all = document.querySelectorAll('.MS__popup.active');
            return all.length ? all[all.length - 1].id : '';
        }""")
    except Exception:
        active_id = ""
    log(f"  → Popup active: #{active_id}")

    # ── Trường hợp: popup_inform mở ngay (đã nhận / chưa đủ ĐK) ─────
    if active_id == "popup_inform":
        try:
            inform_el = event_frame.query_selector(".pm__inform-text")
            txt = inform_el.inner_text().strip().replace("\n", " ") if inform_el else ""
            log(f"  ⚠ Thông báo trực tiếp: {txt}")
        except Exception:
            pass
        _close_popup(event_frame, page, log)   # đóng popup_inform → về getlist
        return

    # ── Trường hợp lạ (không phải popup_condition) ───────────────────
    if active_id != "popup_condition":
        log(f"  ⚠ Popup không nhận dạng được ({active_id}) — đóng và bỏ qua")
        if active_id:
            _close_popup(event_frame, page, log)
        return

    # ── popup_condition: kiểm tra captcha ────────────────────────────
    captcha_visible = False
    try:
        img = event_frame.query_selector("#captcha-image")
        if img:
            captcha_visible = "display: none" not in (img.get_attribute("style") or "")
    except Exception:
        pass
    log(f"  → Captcha: {'có' if captcha_visible else 'không'}")

    if captcha_visible:
        log("  ⚠ Captcha hiện → bỏ qua, đóng modal")
        _close_popup(event_frame, page, log)   # đóng popup_condition → về getlist
        return

    # ── Click "Xác nhận" ─────────────────────────────────────────────
    log("  → Click Xác nhận...")
    try:
        xac_nhan = event_frame.wait_for_selector(
            'form#pm__condition-form button[type="submit"]',
            state="visible", timeout=5_000,
        )
        xac_nhan.click()
        page.wait_for_timeout(2_000)
    except Exception as e:
        log(f"  ✗ Không click được Xác nhận: {e}")
        _close_popup(event_frame, page, log)
        return

    # ── Đọc kết quả ──────────────────────────────────────────────────
    page.wait_for_timeout(1_000)
    try:
        active_after = event_frame.evaluate("""() => {
            const all = document.querySelectorAll('.MS__popup.active');
            return all.length ? all[all.length - 1].id : '';
        }""")
    except Exception:
        active_after = ""
    log(f"  → Popup sau Xác nhận: #{active_after}")

    if active_after == "popup_inform":
        try:
            inform_el = event_frame.query_selector(".pm__inform-text")
            txt = inform_el.inner_text().strip().replace("\n", " ") if inform_el else ""
            log(f"  ⚠ Kết quả: {txt}")
        except Exception:
            pass
        _close_popup(event_frame, page, log)   # đóng popup_inform
        page.wait_for_timeout(500)
        _close_popup(event_frame, page, log)   # đóng popup_condition → về getlist
    else:
        log("  ✔ Nhận lượt thành công!")
        _close_popup(event_frame, page, log)   # đóng popup_condition → về getlist


def _spin_all(event_frame, page, log) -> None:
    """Rút 1 lần liên tục cho đến khi hết lượt (bao gồm lượt sẵn có + lượt vừa nhận).

    Selector số lượt: span.pm__point  (HTML: <span class="spoint pm__point">N</span>)
    Nút rút:         a.pm__rut[data-value="1"]  — dùng dispatch_event vì là JS listener.

    Vòng lặp kiểm tra DOM TRƯỚC MỖI LẦN rút, không dựa vào giá trị đọc 1 lần ban đầu.
    Dừng khi: DOM = 0 (sau ít nhất 1 lần thử), popup báo hết lượt, hoặc nút không có.
    """
    try:
        from config import SELECTORS
    except ImportError:
        log("  ⚠ [Rút] Chưa có config.py — bỏ qua.")
        return

    turns_sel = SELECTORS.get("turns_count", "span.pm__point")
    spin_sel  = 'a.pm__rut[data-value="1"]'

    def _read_turns() -> int:
        """Trả về số lượt từ DOM. -1 nếu không đọc được selector."""
        try:
            el = event_frame.query_selector(turns_sel)
            raw = el.inner_text().strip() if el else ""
            return int("".join(ch for ch in raw if ch.isdigit()) or "0")
        except Exception:
            return -1

    # ── Đọc số lượt ban đầu có retry (DOM có thể chưa cập nhật ngay) ─
    initial = -1
    for attempt in range(1, 4):
        initial = _read_turns()
        if initial > 0:
            break
        log(f"  → [Rút] Đọc lượt lần {attempt}: {initial} — chờ DOM cập nhật...")
        page.wait_for_timeout(1_500)

    log(f"  → [Rút] Số lượt đọc được ban đầu: {initial}")

    # ── Vòng lặp rút: kiểm tra DOM trước mỗi lần, dừng khi hết ──────
    spun = 0
    while True:
        current = _read_turns()

        # Dừng: DOM xác nhận 0 lượt (và đã thử ít nhất 1 lần, hoặc đọc ban đầu = 0)
        if current == 0:
            if spun == 0:
                log("  ⚠ [Rút] DOM báo 0 lượt sau retry — không có lượt để rút.")
            else:
                log(f"  ✔ [Rút] DOM xác nhận hết lượt sau {spun} lần rút — dừng.")
            break

        # Nếu không đọc được selector nhưng chưa rút lần nào → bỏ qua
        if current < 0 and spun == 0:
            log("  ⚠ [Rút] Không đọc được selector số lượt — bỏ qua.")
            break

        spun += 1
        display = f"{current}" if current > 0 else "?"
        log(f"  → [Rút {spun}] Lượt còn lại: {display} — đang bấm Rút 1 lần...")

        # ── Dispatch click ───────────────────────────────────────────
        try:
            btn = event_frame.wait_for_selector(spin_sel, state="attached", timeout=5_000)
            btn.dispatch_event("click")
            page.wait_for_timeout(2_500)
        except Exception as e:
            log(f"  ✗ [Rút {spun}] Không tìm thấy / click được nút rút: {e}")
            break

        # ── Đọc và xử lý popup kết quả ──────────────────────────────
        try:
            active_id = event_frame.evaluate("""() => {
                const all = document.querySelectorAll('.MS__popup.active');
                return all.length ? all[all.length - 1].id : '';
            }""")
        except Exception:
            active_id = ""

        if active_id:
            result_txt = ""
            try:
                el = event_frame.query_selector(".pm__inform-text")
                result_txt = el.inner_text().strip().replace("\n", " ") if el else ""
            except Exception:
                pass
            if result_txt:
                log(f"  → [Rút {spun}] Thông báo: {result_txt}")

            lowered = result_txt.lower()
            if any(kw in lowered for kw in ("hết lượt", "không có lượt", "không đủ lượt", "out of turn")):
                log("  ⚠ [Rút] Popup báo hết lượt — đóng và dừng.")
                _close_popup(event_frame, page, log)
                break

            _close_popup(event_frame, page, log)
            page.wait_for_timeout(700)
        else:
            log(f"  → [Rút {spun}] Không có popup phản hồi.")

    log(f"  ✔ [Rút] Hoàn thành — tổng đã rút {spun} lần.")


def _close_two_modals(event_frame, page, log) -> None:
    """Đóng 3 modal liên tiếp, mỗi lần dùng _close_popup."""
    log("  → [Bước 13] Đóng lần 1 (Thông báo)...")
    _close_popup(event_frame, page, log)

    page.wait_for_timeout(700)
    log("  → [Bước 13] Đóng lần 2 (Nhiệm vụ nhận lượt)...")
    _close_popup(event_frame, page, log)

    page.wait_for_timeout(700)
    log("  → [Bước 13] Đóng lần 3 → về màn hình 'Nhiệm vụ' chính...")
    _close_popup(event_frame, page, log)
    log("  ✔ [Bước 13] Đã về màn hình 'Nhiệm vụ' chính")


def _close_popup(event_frame, page, log) -> None:
    """Đóng popup hiện tại bằng cách xóa class 'active' trực tiếp qua JS.

    Cơ chế thật của trang: mỗi popup là một <section class="MS__popup">.
    Hiển thị / ẩn được kiểm soát hoàn toàn bằng CSS class 'active'.
    Nút X chỉ gọi jQuery để remove class đó — ta bỏ qua nút, làm thẳng.
    """
    log("  → [Đóng] Xóa class 'active' khỏi .MS__popup đang nổi trên cùng...")
    try:
        result = event_frame.evaluate("""() => {
            const popups = document.querySelectorAll('.MS__popup.active');
            if (!popups.length) return 'no_active_popup';
            // Popup cuối cùng trong DOM = nổi trên cùng (z-index / render order)
            const top = popups[popups.length - 1];
            const id  = top.id || top.className;
            top.classList.remove('active');
            return 'closed:' + id;
        }""")
        log(f"  → [Đóng] JS kết quả: {result}")
        page.wait_for_timeout(500)
        if result and result != "no_active_popup":
            log("  ✔ [Đóng] Thành công")
        else:
            log("  ⚠ [Đóng] Không có popup nào đang active")
    except Exception as e:
        log(f"  ✗ [Đóng] JS thất bại: {e}")

# ── Config helper ─────────────────────────────────────────────────────
def _save_url_to_config(url: str) -> None:
    import re
    from pathlib import Path

    config_path = Path(__file__).parent / "config.py"
    example_path = Path(__file__).parent / "config.example.py"

    if config_path.exists():
        text = config_path.read_text(encoding="utf-8")
        # Thay thế dòng BASE_URL = "..." dù dùng nháy đơn hay đôi
        new_text = re.sub(r'^BASE_URL\s*=\s*["\'].*?["\']',
                          f'BASE_URL = "{url}"', text, flags=re.MULTILINE)
        config_path.write_text(new_text, encoding="utf-8")
    else:
        # Tạo config.py mới từ example, chỉ đổi BASE_URL
        template = example_path.read_text(encoding="utf-8") if example_path.exists() else (
            'BASE_URL = ""\n\nSELECTORS = {\n'
            '    "username": \'input[name="username"]\',\n'
            '    "password": \'input[name="password"]\',\n'
            '    "login_button": \'button[type="submit"]\',\n'
            '    "logout_button": \'button:has-text("Đăng xuất")\',\n'
            '}\n'
        )
        new_text = re.sub(r'^BASE_URL\s*=\s*["\'].*?["\']',
                          f'BASE_URL = "{url}"', template, flags=re.MULTILINE)
        config_path.write_text(new_text, encoding="utf-8")


# ── Entry ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    view = AppView()
    AppController(AppModel(), view)
    view.mainloop()
