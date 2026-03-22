"""
Luồng tự động: mở trang → đăng nhập → thao tác → đăng xuất (tùy chỉnh trong run_flow).
Chạy: python web_flow.py
"""

from pathlib import Path

from playwright.sync_api import Page, sync_playwright

# Dùng config.py nếu có, không thì dùng giá trị mẫu.
try:
    from config import BASE_URL, SELECTORS, TEST_USER
except ImportError:
    BASE_URL = "https://example.com"
    SELECTORS = {
        "username": 'input[name="username"]',
        "password": 'input[name="password"]',
        "login_button": 'button[type="submit"]',
        "logout_button": 'button:has-text("Đăng xuất")',
    }
    TEST_USER = {"username": "", "password": ""}


def run_flow(page: Page) -> None:
    page.goto(BASE_URL, wait_until="domcontentloaded")

    # --- Đăng nhập (bỏ qua nếu trang không có form) ---
    if TEST_USER.get("username"):
        page.fill(SELECTORS["username"], TEST_USER["username"])
        page.fill(SELECTORS["password"], TEST_USER["password"])
        page.click(SELECTORS["login_button"])
        page.wait_for_load_state("networkidle")

    # --- Thêm bước bấm theo thứ tự tại đây ---
    # page.click('text=Menu')
    # page.click('[data-testid="reports"]')

    # --- Đăng xuất ---
    # page.click(SELECTORS["logout_button"])


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "artifacts"
    out_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="vi-VN",
        )
        page = context.new_page()
        page.set_default_timeout(15_000)

        try:
            run_flow(page)
            page.screenshot(path=str(out_dir / "after_flow.png"), full_page=True)
            print("Xong. Ảnh: artifacts/after_flow.png")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
