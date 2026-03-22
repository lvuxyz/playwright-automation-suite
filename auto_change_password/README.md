# Auto Change Password

Công cụ tự động đổi mật khẩu hàng loạt tài khoản web, sử dụng **Playwright** (tự động hóa trình duyệt) và **tkinter** (giao diện đồ họa).

---

## Cấu trúc file

```
auto_change_password/
├── main.py              ← Chạy file này để khởi động ứng dụng
├── gui.py               ← Giao diện tkinter (Model / View / Controller)
├── changer.py           ← Logic Playwright: login → đổi mật khẩu → đóng phiên
├── account_loader.py    ← Đọc / ghi danh sách tài khoản (CSV, Excel)
├── config.example.py    ← Cấu hình mẫu — sao chép thành config.py
├── requirements.txt     ← Thư viện cần thiết
└── README.md
```

---

## Cài đặt

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## Cấu hình

1. Sao chép `config.example.py` thành `config.py`
2. Điền `BASE_URL` (URL trang cần đổi mật khẩu)
3. Điền `LOGIN_SELECTORS` (CSS selector form đăng nhập)
4. Điền `CHANGE_PW_SELECTORS` (CSS selector form đổi mật khẩu)
5. **Không commit** `config.py` nếu chứa thông tin thật

---

## Định dạng file tài khoản (CSV)

```csv
username,old_password,new_password,status,note
user1,matkhau_cu_1,matkhau_moi_1,-,
user2,matkhau_cu_2,matkhau_moi_2,-,
```

Cột `status` và `note` là tuỳ chọn (tự động thêm nếu thiếu).

---

## Chạy

```bash
python main.py
```

### Trong giao diện:
1. Nhập URL trang web (hoặc để trống nếu đã cấu hình trong `config.py`)
2. Thêm tài khoản thủ công hoặc nhập từ file CSV / Excel
3. Bấm **▶ Bắt đầu đổi mật khẩu**
4. Theo dõi kết quả trong bảng tài khoản và cửa sổ log
5. Xuất kết quả ra CSV / Excel để lưu trữ

---

## Lưu ý

- Mỗi tài khoản chạy trong **context trình duyệt riêng biệt** để tránh xung đột phiên
- Bấm **■ Dừng** để ngắt vòng lặp sau khi hoàn thành tài khoản hiện tại
- Cột `status` sau khi chạy: `ok` (thành công) hoặc `fail` (thất bại)
