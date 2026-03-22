# Sao chép thành config.py và điền thông tin thật (không commit config.py nếu có mật khẩu).

BASE_URL = "https://example.com"

# Selector: dùng data-testid, id, hoặc role — ưu tiên ổn định nhất trên trang của bạn.
SELECTORS = {
    "username": 'input[name="username"]',
    "password": 'input[name="password"]',
    "login_button": 'button[type="submit"]',
    "logout_button": 'button:has-text("Đăng xuất")',

    # Selector hiển thị số lượt hiện có (dùng cho tính năng tự động rút)
    # HTML: <span class="spoint pm__point">N</span>
    "turns_count": "span.pm__point",
}

TEST_USER = {"username": "demo", "password": "demo"}
