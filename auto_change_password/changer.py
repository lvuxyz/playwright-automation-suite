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

# Selectors đặc thù cho trang VNG Games ID (phân tích từ HTML)
VNG_SELECTORS = {
    # Bước 1 — nhập email/SĐT
    "email_phone":  'input[data-id="input_email_phone"]',
    "btn_continue": 'button[data-id="login_button_continue"]',
    # Bước 2 — nhập mật khẩu
    "password":     'input[data-id="input_password"]',
    "btn_login":    'button[data-id="login_button_continue_and_play"]',
}

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


def _vng_login(page: Page, username: str, password: str, log: LogFn) -> None:
    """Đăng nhập trang VNG Games ID (id.vnggames.app/login).

    Luồng 2 bước:
        Bước 0 (nếu có) — Màn "Chọn tài khoản":
            Nếu trang hiện danh sách tài khoản đã lưu, click
            "Đăng nhập bằng tài khoản khác" để về form email.

        Bước 1 — Email:
            1. Chờ input email/SĐT xuất hiện
            2. Điền email/SĐT
            3. Chờ nút "Tiếp tục" được enable → click

        Bước 2 — Mật khẩu:
            4. Chờ input password visible (hiện sau khi qua bước 1)
            5. Điền mật khẩu
            6. Chờ nút "Đăng nhập" được enable → click
            7. Chờ URL thoát khỏi /login = thành công
    """
    timeout = BROWSER.get("timeout", 15_000)

    # ── Bước 1: Nhập email / SĐT ─────────────────────────────────────────────
    page.wait_for_selector(VNG_SELECTORS["email_phone"], state="visible", timeout=timeout)

    log(f"  → Điền email/SĐT: {username}")
    page.click(VNG_SELECTORS["email_phone"])
    page.fill(VNG_SELECTORS["email_phone"], username)

    log("  → Chờ nút Tiếp tục được kích hoạt...")
    page.wait_for_selector(
        f'{VNG_SELECTORS["btn_continue"]}:not([disabled])',
        state="visible",
        timeout=10_000,
    )
    log("  → Bấm Tiếp tục")
    page.click(VNG_SELECTORS["btn_continue"])

    # ── Bước 2: Nhập mật khẩu ────────────────────────────────────────────────
    log("  → Chờ trường mật khẩu xuất hiện...")
    page.wait_for_selector(VNG_SELECTORS["password"], state="visible", timeout=timeout)

    log("  → Điền mật khẩu")
    page.click(VNG_SELECTORS["password"])
    page.fill(VNG_SELECTORS["password"], password)

    log("  → Chờ nút Đăng nhập được kích hoạt...")
    page.wait_for_selector(
        f'{VNG_SELECTORS["btn_login"]}:not([disabled])',
        state="visible",
        timeout=10_000,
    )
    log("  → Bấm Đăng nhập")
    page.click(VNG_SELECTORS["btn_login"])

    # ── Bước 3: Xử lý sau đăng nhập ──────────────────────────────────────────
    # Sau khi bấm "Đăng nhập", có 2 kịch bản:
    #   A) Chuyển thẳng tới trang game/callback  → hoàn tất
    #   B) Redirect sang trang "Chọn tài khoản đăng nhập" (SSO callback)
    #      → cần bấm vào tài khoản hiển thị để hoàn tất đăng nhập

    # Chờ URL thoát khỏi /login trước
    page.wait_for_url(
        lambda url: "id.vnggames.app/login" not in url,
        timeout=20_000,
    )

    # Kiểm tra kịch bản B: trang "Chọn tài khoản"
    try:
        page.wait_for_selector('div[data-id="div_user_info"]', state="visible", timeout=4_000)
        log("  → Phát hiện trang 'Chọn tài khoản đăng nhập' sau login")

        # Chuẩn hoá username để so khớp text dạng "User 04499148800"
        # "04499148800" → "4499148800" | "+84499148800" → "499148800"
        norm = username.lstrip("+").lstrip("84").lstrip("0") if username else ""

        matched = False
        for card in page.locator('div[data-id="div_user_info"]').all():
            card_text = card.inner_text().strip()
            if username in card_text or (norm and norm in card_text):
                log(f"  → Khớp tài khoản [{card_text}] → bấm vào")
                card.click()
                matched = True
                break

        if not matched:
            # Không tìm thấy tài khoản khớp — bấm vào card đầu tiên
            first_card = page.locator('div[data-id="div_user_info"]').first
            card_text = first_card.inner_text().strip()
            log(f"  → Không khớp, bấm vào tài khoản đầu tiên: [{card_text}]")
            first_card.click()

        # Chờ điều hướng cuối cùng sau khi chọn tài khoản
        page.wait_for_load_state("domcontentloaded", timeout=timeout)

    except Exception:
        pass  # Kịch bản A: đã vào thẳng trang đích, không cần xử lý thêm


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
    target_url = (url or BASE_URL).strip()
    if target_url and not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url
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


# ── Đăng nhập một tài khoản VNG ───────────────────────────────────────────

def login_account(
    browser: Browser,
    account: Account,
    url: str = "",
    log: LogFn = _log_noop,
) -> ChangeResult:
    """Mở context riêng, đăng nhập một tài khoản VNG và trả về kết quả.

    Luôn đóng context sau khi xong (dùng cho mục đích kiểm tra đơn lẻ).
    Để giữ tab mở sau đăng nhập, dùng ``run_login_batch``.
    """
    target_url = (url or VNG_LOGIN_URL).strip()
    if target_url and not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url
    context: BrowserContext | None = None

    try:
        context = browser.new_context(
            viewport=BROWSER.get("viewport", {"width": 1280, "height": 720}),
            locale=BROWSER.get("locale", "vi-VN"),
        )
        page = context.new_page()
        page.set_default_timeout(BROWSER.get("timeout", 15_000))

        log(f"▶ [{account.username}] Mở trang đăng nhập...")
        page.goto(target_url, wait_until="domcontentloaded")

        log(f"▶ [{account.username}] Đang đăng nhập...")
        _vng_login(page, account.username, account.old_password, log)

        final_url = page.url
        short_url = final_url[:70] + ("..." if len(final_url) > 70 else "")
        log(f"✔ [{account.username}] Đăng nhập thành công → {short_url}")
        return ChangeResult(account.username, True, f"OK → {short_url}")

    except Exception as exc:
        msg = str(exc).splitlines()[0]
        log(f"✗ [{account.username}] Lỗi đăng nhập: {msg}")
        return ChangeResult(account.username, False, msg)

    finally:
        if context:
            context.close()


def run_login_batch(
    accounts: list[Account],
    url: str = "",
    log: LogFn = _log_noop,
    on_result: Callable[[int, ChangeResult], None] | None = None,
    stop_flag: Callable[[], bool] | None = None,
) -> list[ChangeResult]:
    """Chạy đăng nhập tuần tự cho toàn bộ danh sách tài khoản.

    Mỗi tài khoản được mở trong một tiến trình Chrome **hoàn toàn mới**
    (không chia sẻ cookie, cache, autofill với nhau).
    Các cửa sổ đăng nhập thành công được giữ mở cho đến khi người dùng
    bấm Dừng (stop_flag) hoặc tự đóng trình duyệt.

    Args:
        accounts:   Danh sách tài khoản (dùng ``old_password`` để login).
        url:        URL trang đăng nhập (mặc định: VNG_LOGIN_URL).
        log:        Hàm ghi log được gọi thread-safe từ GUI.
        on_result:  Callback ``(index, ChangeResult)`` sau mỗi tài khoản.
        stop_flag:  Hàm trả về ``True`` khi người dùng bấm Dừng.
    """
    target_url = (url or VNG_LOGIN_URL).strip()
    if target_url and not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    results: list[ChangeResult] = []
    # Mỗi phần tử: (browser, context) của tài khoản đăng nhập thành công
    open_browsers: list[tuple] = []

    with sync_playwright() as pw:
        try:
            for i, acc in enumerate(accounts):
                if stop_flag and stop_flag():
                    log("⚠ Đã dừng theo yêu cầu người dùng.")
                    break

                browser = None
                context = None
                try:
                    # Mỗi tài khoản = một Chromium process riêng, không có profile user
                    # (bỏ channel="chrome" để tránh dùng profile Chrome thật của máy)
                    browser = pw.chromium.launch(
                        headless=BROWSER.get("headless", False),
                        slow_mo=BROWSER.get("slow_mo", 0),
                    )
                    context = browser.new_context(
                        viewport=BROWSER.get("viewport", {"width": 1280, "height": 720}),
                        locale=BROWSER.get("locale", "vi-VN"),
                    )
                    page = context.new_page()
                    page.set_default_timeout(BROWSER.get("timeout", 15_000))

                    log(f"▶ [{acc.username}] Mở Chrome mới...")
                    page.goto(target_url, wait_until="domcontentloaded")

                    log(f"▶ [{acc.username}] Đang đăng nhập...")
                    _vng_login(page, acc.username, acc.old_password, log)

                    final_url = page.url
                    short_url = final_url[:70] + ("..." if len(final_url) > 70 else "")
                    log(f"✔ [{acc.username}] Đăng nhập thành công → {short_url}")
                    result = ChangeResult(acc.username, True, f"OK → {short_url}")

                    # Giữ browser + context mở
                    open_browsers.append((browser, context))
                    browser = None  # Chuyển ownership — không đóng trong finally bên dưới

                except Exception as exc:
                    msg = str(exc).splitlines()[0]
                    log(f"✗ [{acc.username}] Lỗi đăng nhập: {msg}")
                    result = ChangeResult(acc.username, False, msg)
                    if context:
                        try:
                            context.close()
                        except Exception:
                            pass
                    if browser and browser.is_connected():
                        try:
                            browser.close()
                        except Exception:
                            pass

                results.append(result)
                if on_result:
                    on_result(i, result)

                time.sleep(0.5)

            # ── Giữ tất cả Chrome mở cho đến khi bấm Dừng ────────────────
            if open_browsers:
                log(
                    f"✔ Đã đăng nhập {len(open_browsers)} tài khoản — "
                    "giữ Chrome mở. Bấm Dừng để đóng tất cả."
                )
                while not (stop_flag and stop_flag()):
                    # Dừng sớm nếu người dùng đóng tay hết tất cả cửa sổ
                    if all(not b.is_connected() for b, _ in open_browsers):
                        break
                    time.sleep(0.5)

        finally:
            for b, ctx in open_browsers:
                try:
                    ctx.close()
                except Exception:
                    pass
                try:
                    if b.is_connected():
                        b.close()
                except Exception:
                    pass

    return results


# ── Mở Chrome đến trang đăng nhập (bước khởi động) ────────────────────────

def open_login_page(
    stop_flag: Callable[[], bool] = lambda: False,
    log: LogFn = _log_noop,
) -> None:
    """Mở Chrome và điều hướng đến trang đăng nhập VNG Games.

    Giữ trình duyệt mở cho đến khi người dùng đóng hoặc bấm Dừng.
    """
    log(f"▶ Đang mở trình duyệt → {VNG_LOGIN_URL[:60]}...")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
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
