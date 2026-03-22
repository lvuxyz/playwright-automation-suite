# Sao chép thành config.py và điền thông tin thật.
# KHÔNG commit file config.py lên git nếu chứa mật khẩu thật.

# ── URL ────────────────────────────────────────────────────────────────────
BASE_URL = "https://example.com"

# URL trang đổi mật khẩu (để trống nếu dùng SELECTORS["change_pw_link"])
CHANGE_PASSWORD_URL = ""

# ── Selectors đăng nhập ────────────────────────────────────────────────────
# Ưu tiên: data-testid > id > name > CSS class
LOGIN_SELECTORS = {
    "username":     'input[name="username"]',
    "password":     'input[name="password"]',
    "submit":       'button[type="submit"]',

    # Selector xác nhận đăng nhập thành công (tuỳ trang)
    "login_success": None,          # vd: 'text=Xin chào' hoặc '.dashboard'
}

# ── Selectors trang đổi mật khẩu ───────────────────────────────────────────
CHANGE_PW_SELECTORS = {
    # Link / nút dẫn đến trang đổi mật khẩu (bỏ qua nếu dùng CHANGE_PASSWORD_URL)
    "change_pw_link":   None,       # vd: 'a:has-text("Đổi mật khẩu")'

    "old_password":     'input[name="current_password"]',
    "new_password":     'input[name="new_password"]',
    "confirm_password": 'input[name="confirm_password"]',
    "submit":           'button[type="submit"]',

    # Selector thông báo đổi thành công (dùng để xác nhận kết quả)
    "success_message":  None,       # vd: 'text=Đổi mật khẩu thành công'
}

# ── Cài đặt trình duyệt ────────────────────────────────────────────────────
BROWSER = {
    "headless":     False,          # True = ẩn trình duyệt
    "slow_mo":      0,              # ms — làm chậm mỗi thao tác (debug)
    "timeout":      15_000,         # ms — timeout mặc định cho mỗi thao tác
    "viewport":     {"width": 1280, "height": 720},
    "locale":       "vi-VN",
}
