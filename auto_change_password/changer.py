"""
Logic tự động đổi mật khẩu dùng Playwright.

Luồng mỗi tài khoản:
    1. Mở trang BASE_URL
    2. Đăng nhập (username + old_password)
    3. Điều hướng đến trang đổi mật khẩu
    4. Điền old_password / new_password / confirm_password
    5. Submit → kiểm tra thành công
    6. Đóng context (tự động đăng xuất phiên)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from account_loader import Account

VNG_LOGIN_URL = (
    "https://id.vnggames.app/login"
    "?back=https%3A%2F%2Fsso.vnggames.com%2Fsso%2Fbridge%2Fcallback"
    "%3Fr_state%3DnfsSBaomtr4o5svyktmwEmmNk81zkM0NkJWLat-pOom3UNMeYhj9MBP0PAMuGqRjje"
    "_05SdKN_Tlq3LsmC0fdryYfEXQc0x6UJdf8oI-dYGxBNqktZys7VCPUIIXdQdOQjBq4Zu1QMt_GxZR"
    "1a1eSW7drcbm3nshH8fDwZ7aJ7Z4pLETeMS28GwgYUa5Vy5MwhoEb4MHiUds-ugEKG_AJKIw8-D5Ek"
    "6xhIpzVrIxQsL7POBVpaZb9fnq8BrowltyHeuwVPnviJ-bPJ1u3P4a50bTPOZXBUxUFa_6wVUVBKiOj"
    "pNkMKx5N_4Qr5_mwDb5x6gXbdGotJiuydV5qvD67QyFO05lunQ"
    "&client_id=0&ggid=3275c55fbd63e981&lang=vi"
)

# Nạp config nếu có, không thì dùng giá trị rỗng
try:
    from config import BASE_URL, BROWSER, CHANGE_PASSWORD_URL  # type: ignore
    from config import CHANGE_PW_SELECTORS, LOGIN_SELECTORS    # type: ignore
except ImportError:
    BASE_URL = "https://example.com"
    CHANGE_PASSWORD_URL = ""
    BROWSER = {
        "headless": False,
        "slow_mo": 0,
        "timeout": 15_000,
        "viewport": {"width": 1280, "height": 720},
        "locale": "vi-VN",
    }
    LOGIN_SELECTORS = {
        "username":     'input[name="username"]',
        "password":     'input[name="password"]',
        "submit":       'button[type="submit"]',
        "login_success": None,
    }
    CHANGE_PW_SELECTORS = {
        "change_pw_link":   None,
        "old_password":     'input[name="current_password"]',
        "new_password":     'input[name="new_password"]',
        "confirm_password": 'input[name="confirm_password"]',
        "submit":           'button[type="submit"]',
        "success_message":  None,
    }


# ── Kiểu kết quả ──────────────────────────────────────────────────────────

@dataclass
class ChangeResult:
    username: str
    success:  bool
    message:  str = ""


# ── Hàm thao tác từng bước ────────────────────────────────────────────────

LogFn = Callable[[str], None]


def _log_noop(msg: str) -> None:
    pass


def _login(page: Page, username: str, password: str, log: LogFn) -> None:
    log(f"  → Điền username: {username}")
    page.fill(LOGIN_SELECTORS["username"], username)
    page.fill(LOGIN_SELECTORS["password"], password)

    log("  → Bấm đăng nhập")
    page.click(LOGIN_SELECTORS["submit"])
    page.wait_for_load_state("networkidle")

    if sel := LOGIN_SELECTORS.get("login_success"):
        page.wait_for_selector(sel, timeout=BROWSER["timeout"])


def _navigate_to_change_pw(page: Page, log: LogFn) -> None:
    if CHANGE_PASSWORD_URL:
        log(f"  → Mở trang đổi mật khẩu: {CHANGE_PASSWORD_URL}")
        page.goto(CHANGE_PASSWORD_URL, wait_until="domcontentloaded")
    elif sel := CHANGE_PW_SELECTORS.get("change_pw_link"):
        log("  → Bấm liên kết đổi mật khẩu")
        page.click(sel)
        page.wait_for_load_state("networkidle")
    else:
        raise RuntimeError(
            "Chưa cấu hình CHANGE_PASSWORD_URL hoặc CHANGE_PW_SELECTORS['change_pw_link']."
        )


def _fill_change_form(page: Page, old_pw: str, new_pw: str, log: LogFn) -> None:
    if sel := CHANGE_PW_SELECTORS.get("old_password"):
        log("  → Điền mật khẩu cũ")
        page.fill(sel, old_pw)

    log("  → Điền mật khẩu mới")
    page.fill(CHANGE_PW_SELECTORS["new_password"], new_pw)

    if sel := CHANGE_PW_SELECTORS.get("confirm_password"):
        log("  → Xác nhận mật khẩu mới")
        page.fill(sel, new_pw)

    log("  → Bấm xác nhận đổi mật khẩu")
    page.click(CHANGE_PW_SELECTORS["submit"])
    page.wait_for_load_state("networkidle")


def _verify_success(page: Page) -> bool:
    if sel := CHANGE_PW_SELECTORS.get("success_message"):
        try:
            page.wait_for_selector(sel, timeout=5_000)
            return True
        except Exception:
            return False
    return True  # Không có selector xác nhận → coi như thành công


# ── Hàm chính đổi 1 tài khoản ─────────────────────────────────────────────

def change_password_for_account(
    browser: Browser,
    account: Account,
    url: str = "",
    log: LogFn = _log_noop,
) -> ChangeResult:
    """
    Mở context riêng biệt cho mỗi tài khoản để tránh xung đột phiên.
    Trả về ChangeResult với success=True/False và thông báo chi tiết.
    """
    target_url = url or BASE_URL
    context: BrowserContext | None = None

    try:
        context = browser.new_context(
            viewport=BROWSER["viewport"],
            locale=BROWSER["locale"],
        )
        page = context.new_page()
        page.set_default_timeout(BROWSER["timeout"])

        log(f"▶ [{account.username}] Mở trang: {target_url}")
        page.goto(target_url, wait_until="domcontentloaded")

        log(f"▶ [{account.username}] Đăng nhập...")
        _login(page, account.username, account.old_password, log)

        log(f"▶ [{account.username}] Điều hướng đổi mật khẩu...")
        _navigate_to_change_pw(page, log)

        log(f"▶ [{account.username}] Điền form đổi mật khẩu...")
        _fill_change_form(page, account.old_password, account.new_password, log)

        ok = _verify_success(page)
        if ok:
            log(f"✔ [{account.username}] Đổi mật khẩu thành công")
            return ChangeResult(account.username, True, "Thành công")
        else:
            log(f"✗ [{account.username}] Không tìm thấy thông báo thành công")
            return ChangeResult(account.username, False, "Không xác nhận được kết quả")

    except Exception as exc:
        msg = str(exc).splitlines()[0]
        log(f"✗ [{account.username}] Lỗi: {msg}")
        return ChangeResult(account.username, False, msg)

    finally:
        if context:
            context.close()


# ── Chạy hàng loạt (dùng từ GUI qua thread) ───────────────────────────────

def run_batch(
    accounts: list[Account],
    url: str = "",
    log: LogFn = _log_noop,
    on_result: Callable[[int, ChangeResult], None] | None = None,
    stop_flag: Callable[[], bool] | None = None,
) -> list[ChangeResult]:
    """
    Chạy đổi mật khẩu tuần tự cho danh sách tài khoản.

    Args:
        accounts:   Danh sách tài khoản cần xử lý.
        url:        URL trang web (ghi đè BASE_URL trong config).
        log:        Hàm ghi log — được gọi thread-safe từ GUI.
        on_result:  Callback (index, result) sau mỗi tài khoản.
        stop_flag:  Hàm trả về True khi người dùng bấm Dừng.
    """
    results: list[ChangeResult] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=BROWSER["headless"],
            slow_mo=BROWSER["slow_mo"],
        )
        try:
            for i, acc in enumerate(accounts):
                if stop_flag and stop_flag():
                    log("⚠ Đã dừng theo yêu cầu người dùng.")
                    break

                result = change_password_for_account(browser, acc, url=url, log=log)
                results.append(result)

                if on_result:
                    on_result(i, result)

                # Nghỉ ngắn giữa các tài khoản để tránh bị chặn
                time.sleep(0.5)

        finally:
            browser.close()

    return results


# ── Mở Chrome đến trang đăng nhập (bước khởi động) ────────────────────────

def open_login_page(
    stop_flag: Callable[[], bool] = lambda: False,
    log: LogFn = _log_noop,
) -> None:
    """Mở Chrome và điều hướng đến trang đăng nhập VNG Games.

    Giữ trình duyệt mở cho đến khi người dùng đóng hoặc bấm Dừng.
    """
    log(f"▶ Đang mở Chrome → {VNG_LOGIN_URL[:60]}...")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            channel="chrome",
            headless=False,
            slow_mo=BROWSER.get("slow_mo", 0),
        )
        try:
            page = browser.new_page(
                viewport=BROWSER.get("viewport", {"width": 1280, "height": 720}),
                locale=BROWSER.get("locale", "vi-VN"),
            )
            page.goto(VNG_LOGIN_URL, wait_until="domcontentloaded")
            log("✔ Đã mở trang đăng nhập VNG Games.")

            while not stop_flag() and browser.is_connected():
                time.sleep(0.5)
        finally:
            if browser.is_connected():
                browser.close()
