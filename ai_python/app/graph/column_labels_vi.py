"""Vietnamese display labels for SQL result column keys (query table UI)."""

from __future__ import annotations

# Common ERP columns — keys normalized to lowercase snake_case.
_COLUMN_LABELS_VI: dict[str, str] = {
    "id": "ID",
    "tenant_id": "Mã tenant",
    "category_id": "Mã danh mục",
    "product_id": "Mã sản phẩm",
    "customer_id": "Mã khách hàng",
    "supplier_id": "Mã nhà cung cấp",
    "order_id": "Mã đơn hàng",
    "receipt_id": "Mã phiếu nhập",
    "dispatch_id": "Mã phiếu xuất",
    "inventory_id": "Mã tồn kho",
    "unit_id": "Mã đơn vị",
    "location_id": "Mã vị trí",
    "voucher_id": "Mã voucher",
    "sku_code": "Mã SKU",
    "sku": "Mã SKU",
    "barcode": "Mã vạch",
    "code": "Mã",
    "receipt_code": "Mã phiếu nhập",
    "dispatch_code": "Mã phiếu xuất",
    "order_code": "Mã đơn hàng",
    "category_code": "Mã danh mục",
    "supplier_code": "Mã NCC",
    "customer_code": "Mã khách hàng",
    "name": "Tên",
    "product_name": "Tên sản phẩm",
    "category_name": "Tên danh mục",
    "customer_name": "Tên khách hàng",
    "supplier_name": "Tên nhà cung cấp",
    "description": "Mô tả",
    "image_url": "Ảnh (URL)",
    "weight": "Khối lượng (g)",
    "status": "Trạng thái",
    "quantity": "Số lượng",
    "qty": "Số lượng",
    "reserved_quantity": "Số lượng giữ",
    "amount": "Số tiền",
    "total_amount": "Tổng giá trị",
    "total_value": "Tổng giá trị",
    "total_inventory_value": "Tổng giá trị tồn kho",
    "cost_price": "Giá vốn",
    "selling_price": "Giá bán",
    "unit_price": "Đơn giá",
    "revenue": "Doanh thu",
    "total_revenue": "Tổng doanh thu",
    "cost": "Chi phí",
    "profit": "Lợi nhuận",
    "debt": "Công nợ",
    "balance": "Số dư",
    "discount": "Giảm giá",
    "tax": "Thuế",
    "tax_code": "Mã số thuế",
    "phone": "Số điện thoại",
    "email": "Email",
    "address": "Địa chỉ",
    "channel": "Kênh bán",
    "order_type": "Loại đơn",
    "payment_method": "Hình thức thanh toán",
    "payment_status": "Trạng thái thanh toán",
    "batch_number": "Số lô",
    "location_code": "Mã vị trí kho",
    "unit_name": "Đơn vị tính",
    "note": "Ghi chú",
    "notes": "Ghi chú",
    "created_at": "Ngày tạo",
    "updated_at": "Ngày cập nhật",
    "order_date": "Ngày đơn",
    "receipt_date": "Ngày nhập",
    "dispatch_date": "Ngày xuất",
    "due_date": "Hạn thanh toán",
    "expiry_date": "Hạn dùng",
    "month": "Tháng",
    "year": "Năm",
    "day": "Ngày",
    "count": "Số lượng",
    "coalesce": "Giá trị tổng hợp",
    "sum": "Tổng giá trị",
    "avg": "Trung bình",
    "min": "Thấp nhất",
    "max": "Cao nhất",
    "?column?": "Giá trị",
    "row_count": "Số dòng",
    "inv_id": "Mã tồn kho",
}

_WORD_VI: dict[str, str] = {
    "total": "tổng",
    "value": "giá trị",
    "amount": "số tiền",
    "inventory": "tồn kho",
    "capital": "vốn",
    "receipt": "phiếu nhập",
    "dispatch": "phiếu xuất",
    "order": "đơn",
    "product": "sản phẩm",
    "customer": "khách hàng",
    "supplier": "nhà cung cấp",
    "category": "danh mục",
    "quantity": "số lượng",
    "price": "giá",
    "cost": "giá vốn",
    "revenue": "doanh thu",
    "status": "trạng thái",
    "name": "tên",
    "code": "mã",
    "date": "ngày",
    "created": "tạo",
    "updated": "cập nhật",
    "number": "số",
    "count": "số lượng",
    "image": "ảnh",
    "url": "URL",
    "description": "mô tả",
    "weight": "khối lượng",
    "barcode": "mã vạch",
    "sku": "SKU",
    "channel": "kênh",
    "type": "loại",
    "unit": "đơn vị",
    "batch": "lô",
    "location": "vị trí",
    "phone": "điện thoại",
    "email": "email",
    "address": "địa chỉ",
    "note": "ghi chú",
    "max": "cao nhất",
    "min": "thấp nhất",
    "avg": "trung bình",
    "sum": "tổng",
}


def _looks_like_raw_key(label: str, key: str) -> bool:
    a = label.strip().replace(" ", "_").lower()
    b = key.strip().lower()
    if a == b:
        return True
    return label.strip().upper() == key.strip().upper()


def column_label_vi(key: str) -> str:
    """Map SQL column key to a short Vietnamese header."""
    k = key.strip().lower()
    if not k:
        return key
    if k in _COLUMN_LABELS_VI:
        return _COLUMN_LABELS_VI[k]
    if k.endswith("_id") and k != "id":
        base = k[:-3].replace("_", " ")
        return f"Mã {base}"
    parts = k.split("_")
    if len(parts) >= 2 and parts[-1] == "at" and parts[-2] in ("created", "updated"):
        action = "tạo" if parts[-2] == "created" else "cập nhật"
        return f"Ngày {action}"
    translated = [_WORD_VI.get(p, p) for p in parts if p]
    if all(p in _WORD_VI or p in _COLUMN_LABELS_VI for p in parts):
        return " ".join(translated).capitalize()
    return key.replace("_", " ").upper() if key.isupper() else key.replace("_", " ").title()


def resolve_column_label(key: str, explicit: str | None = None) -> str:
    """Prefer explicit label from executor meta when it is already Vietnamese."""
    if explicit and explicit.strip() and not _looks_like_raw_key(explicit, key):
        return explicit.strip()
    return column_label_vi(key)
