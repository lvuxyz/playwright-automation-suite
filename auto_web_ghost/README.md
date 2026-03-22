# Auto click / test trang web (Playwright + Python)

## Cài đặt

```powershell
cd d:\Code\auto
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

## Cấu hình

1. Sao chép `config.example.py` → `config.py`.
2. Sửa `BASE_URL`, `SELECTORS`, `TEST_USER` cho đúng trang của bạn.

## Chạy

```powershell
python web_flow.py
```

Trình duyệt mở (`headless=False`), thực hiện `run_flow`, chụp ảnh `artifacts/after_flow.png`.

## Cách lấy selector ổn định

- Ưu tiên: `data-testid`, `id`, `name` trên input/button.
- Playwright khuyến nghị: [locators](https://playwright.dev/python/docs/locators) — `get_by_role`, `get_by_test_id`.

Ví dụ trong code:

```python
page.get_by_role("button", name="Đăng nhập").click()
page.get_by_label("Email").fill("a@b.com")
```

## Ghi test chính thức (tùy chọn)

```powershell
pip install pytest pytest-playwright
pytest --headed
```

---

*Nếu bạn gửi URL (staging) và mô tả nút (hoặc HTML snippet), có thể chỉnh `run_flow` cụ thể cho trang đó.*
