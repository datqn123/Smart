package com.example.smart_erp.settings.tablecolumns.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Metadata source of truth for table column settings.
 */
public final class TableColumnCatalog {

	private TableColumnCatalog() {
	}

	public enum TableKey {
		INVENTORY_STOCK("inventory_stock", "Tồn kho"),
		INVENTORY_RECEIPTS("inventory_receipts", "Phiếu nhập kho"),
		INVENTORY_DISPATCH("inventory_dispatch", "Xuất kho & Điều phối"),
		PRODUCT_CATEGORIES("product_categories", "Danh mục sản phẩm"),
		PRODUCT_LIST("product_list", "Sản phẩm"),
		PRODUCT_SUPPLIERS("product_suppliers", "Nhà cung cấp"),
		PRODUCT_CUSTOMERS("product_customers", "Khách hàng");

		private final String key;
		private final String label;

		TableKey(String key, String label) {
			this.key = key;
			this.label = label;
		}

		public String key() {
			return key;
		}

		public String label() {
			return label;
		}

		public static TableKey fromWire(String wire) {
			for (TableKey t : values()) {
				if (t.key.equals(wire)) {
					return t;
				}
			}
			return null;
		}
	}

	public record ColumnMeta(String key, String label, boolean required, int defaultOrder) {
	}

	public static List<ColumnMeta> columns(TableKey tableKey) {
		return switch (tableKey) {
			case INVENTORY_STOCK -> List.of(
					new ColumnMeta("skuCode", "Mã SP", true, 0),
					new ColumnMeta("productName", "Tên sản phẩm", true, 1),
					new ColumnMeta("location", "Vị trí", false, 2),
					new ColumnMeta("quantity", "Tồn kho", false, 3),
					new ColumnMeta("expiryDate", "Hạn SD", false, 4),
					new ColumnMeta("status", "Trạng thái", false, 5));
			case INVENTORY_RECEIPTS -> List.of(
					new ColumnMeta("receiptCode", "Mã phiếu", true, 0),
					new ColumnMeta("supplierName", "Nhà cung cấp", false, 1),
					new ColumnMeta("receiptDate", "Ngày nhập", false, 2),
					new ColumnMeta("staffName", "Người tạo", false, 3),
					new ColumnMeta("invoiceNumber", "Số hóa đơn", false, 4),
					new ColumnMeta("lineCount", "Số dòng hàng", false, 5),
					new ColumnMeta("totalAmount", "Tổng tiền", false, 6),
					new ColumnMeta("status", "Trạng thái", false, 7));
			case INVENTORY_DISPATCH -> List.of(
					new ColumnMeta("dispatchCode", "Mã phiếu", true, 0),
					new ColumnMeta("orderCode", "Mã đơn hàng", false, 1),
					new ColumnMeta("customerName", "Khách hàng", false, 2),
					new ColumnMeta("dispatchDate", "Ngày xuất", false, 3),
					new ColumnMeta("userName", "Người xuất", false, 4),
					new ColumnMeta("itemCount", "Số lượng", false, 5),
					new ColumnMeta("status", "Trạng thái", false, 6));
			case PRODUCT_CATEGORIES -> List.of(
					new ColumnMeta("categoryCode", "Mã phân loại", true, 0),
					new ColumnMeta("categoryName", "Tên danh mục", true, 1),
					new ColumnMeta("productCount", "Số sản phẩm", false, 2),
					new ColumnMeta("description", "Mô tả", false, 3),
					new ColumnMeta("status", "Trạng thái", false, 4));
			case PRODUCT_LIST -> List.of(
					new ColumnMeta("skuCode", "Mã sản phẩm", true, 0),
					new ColumnMeta("productName", "Tên sản phẩm", true, 1),
					new ColumnMeta("categoryName", "Danh mục", false, 2),
					new ColumnMeta("stock", "Tồn kho", false, 3),
					new ColumnMeta("price", "Giá bán", false, 4),
					new ColumnMeta("status", "Trạng thái", false, 5));
			case PRODUCT_SUPPLIERS -> List.of(
					new ColumnMeta("supplierCode", "Mã nhà cung cấp", true, 0),
					new ColumnMeta("supplierName", "Nhà cung cấp", true, 1),
					new ColumnMeta("contactName", "Người liên hệ", false, 2),
					new ColumnMeta("email", "Email", false, 3),
					new ColumnMeta("address", "Địa chỉ", false, 4),
					new ColumnMeta("status", "Trạng thái", false, 5));
			case PRODUCT_CUSTOMERS -> List.of(
					new ColumnMeta("customerCode", "Mã khách hàng", true, 0),
					new ColumnMeta("customerName", "Khách hàng", true, 1),
					new ColumnMeta("phone", "Số điện thoại", false, 2),
					new ColumnMeta("email", "Email", false, 3),
					new ColumnMeta("orderCount", "Số đơn hàng", false, 4),
					new ColumnMeta("status", "Trạng thái", false, 5));
		};
	}

	public static List<TableKey> inventoryScope() {
		List<TableKey> out = new ArrayList<>();
		out.add(TableKey.INVENTORY_STOCK);
		out.add(TableKey.INVENTORY_RECEIPTS);
		out.add(TableKey.INVENTORY_DISPATCH);
		return out;
	}

	public static List<TableKey> productScope() {
		List<TableKey> out = new ArrayList<>();
		out.add(TableKey.PRODUCT_CATEGORIES);
		out.add(TableKey.PRODUCT_LIST);
		out.add(TableKey.PRODUCT_SUPPLIERS);
		out.add(TableKey.PRODUCT_CUSTOMERS);
		return out;
	}

	public static List<TableKey> allScope() {
		List<TableKey> out = new ArrayList<>();
		out.addAll(inventoryScope());
		out.addAll(productScope());
		return out;
	}
}
