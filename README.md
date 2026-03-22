# Playwright Automation Suite

Bộ công cụ tự động hóa trình duyệt web dựa trên **Python + Playwright**, giao diện đồ họa **Tkinter**.

---

## Các dự án

### [`auto_change_password`](./auto_change_password/README.md)
Tự động đổi mật khẩu hàng loạt cho tài khoản web.  
Hỗ trợ nhập danh sách tài khoản từ **CSV**, **Excel**, và **TXT**, sau đó tự động đăng nhập và thực hiện quy trình đổi mật khẩu qua trình duyệt Chromium.

### [`auto_web_ghost`](./auto_web_ghost/README.md)
Công cụ tự động hóa luồng thao tác trên web.  
Điều hướng đến URL mục tiêu, thực hiện các bước đăng nhập / tương tác có thể cấu hình, và chụp ảnh màn hình — phù hợp để kiểm thử nhanh hoặc tự động hóa các tác vụ lặp lại trên trình duyệt.

---

## Yêu cầu

- Python 3.10+
- [Playwright](https://playwright.dev/python/) — `pip install playwright && playwright install chromium`
- Xem `requirements.txt` của từng dự án con để biết đầy đủ thư viện cần thiết.

---

## Bắt đầu nhanh

```powershell
# Clone repository
git clone https://github.com/lvuxyz/playwright-automation-suite.git
cd playwright-automation-suite

# Tạo và kích hoạt môi trường ảo
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Cài đặt thư viện cho dự án con (ví dụ: auto_change_password)
pip install -r auto_change_password/requirements.txt
playwright install chromium

# Sao chép file cấu hình mẫu và chỉnh sửa
copy auto_change_password\config.example.py auto_change_password\config.py

# Chạy ứng dụng
python auto_change_password/main.py
```

---

## Giấy phép

MIT
