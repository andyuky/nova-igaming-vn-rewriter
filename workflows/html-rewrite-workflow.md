# Quy trình viết lại HTML

Quy trình 3 bước để viết lại trang HTML i-gaming với khả năng khôi phục.

## Yêu cầu

```bash
pip install beautifulsoup4
```

## Bước 1: Phân tích HTML

```bash
python scripts/html-parser.py path/to/page.html
```

**Tạo ra:**
- `page_rewrite.md` - Tệp markdown để viết lại
- `page_meta.json` - Metadata cho bộ cập nhật
- `.nova-backups/page_timestamp.html.bak` - Bản sao lưu

**Trích xuất:**
- Tiêu đề trang (`<title>`)
- Mô tả meta (`<meta name="description">`)
- Nội dung chính (headings, paragraphs, lists)

## Bước 2: Viết lại nội dung

Mở `page_rewrite.md` và điền các phần:

### Cấu trúc tệp markdown

```markdown
# Tiêu đề gốc
[Hiển thị tiêu đề gốc]

# Mô tả gốc
[Hiển thị mô tả gốc]

# Nội dung gốc
[Hiển thị nội dung đã trích xuất]

---

## Kết quả viết lại

### Tiêu đề mới
[VIẾT TIÊU ĐỀ MỚI Ở ĐÂY - tối đa 60 ký tự]

### Mô tả mới
[VIẾT MÔ TẢ MỚI Ở ĐÂY - 150-160 ký tự]

### Nội dung mới
[VIẾT NỘI DUNG MỚI Ở ĐÂY]

### Thông tin quan trọng
- Chỉ dành cho người từ 18 tuổi trở lên
- [Các cảnh báo bổ sung]
```

### Quy tắc viết lại

1. **Áp dụng pipeline Nova đầy đủ** (Δ→Σ→Ω→⊗→NAE→VN_MAP→EGM→SEO)
2. **100% tiếng Việt** (chỉ giữ tên thương hiệu)
3. **Kiểm tra ΣLINT** - không có cụm từ bị cấm
4. **Bắt buộc cảnh báo cờ bạc có trách nhiệm**

## Bước 3: Cập nhật HTML

### Xem trước thay đổi (khuyến nghị)
```bash
python scripts/html-updater.py page_meta.json --dry-run
```

### Áp dụng thay đổi
```bash
python scripts/html-updater.py page_meta.json
```

**Cập nhật:**
- `<title>` với tiêu đề mới
- `<meta name="description">` với mô tả mới
- Nội dung chính với nội dung mới
- Thêm khối cảnh báo cờ bạc có trách nhiệm

## Khôi phục (Rollback)

Nếu cập nhật thất bại hoặc cần quay lại phiên bản gốc:

```bash
python scripts/html-updater.py page_meta.json --rollback
```

**Khôi phục tự động:** Nếu cập nhật gặp lỗi, hệ thống tự động khôi phục từ bản sao lưu.

## Trạng thái trong metadata

| Trạng thái | Ý nghĩa |
|------------|---------|
| `pending_rewrite` | Đang chờ viết lại |
| `updated` | Đã cập nhật thành công |
| `rolled_back` | Đã khôi phục |
| `update_failed_rolled_back` | Cập nhật thất bại, đã khôi phục |

## Ví dụ quy trình hoàn chỉnh

```bash
# 1. Phân tích
python scripts/html-parser.py casino-promo.html

# 2. Viết lại (thủ công trong trình soạn thảo)
# Mở casino-promo_rewrite.md và điền nội dung

# 3. Xem trước
python scripts/html-updater.py casino-promo_meta.json --dry-run

# 4. Áp dụng
python scripts/html-updater.py casino-promo_meta.json

# 5. Nếu cần khôi phục
python scripts/html-updater.py casino-promo_meta.json --rollback
```

## Lưu ý quan trọng

- Bản sao lưu được lưu trong `.nova-backups/` cùng thư mục với tệp HTML
- Mỗi lần phân tích tạo bản sao lưu mới với timestamp
- Metadata JSON theo dõi trạng thái và đường dẫn tệp
- Luôn chạy `--dry-run` trước khi áp dụng thay đổi
