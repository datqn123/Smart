package com.example.smart_erp.ai.inventorydraft;

import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Component;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;

@Component
public class InventoryDraftFkResolver {

	private final NamedParameterJdbcTemplate jdbc;

	public InventoryDraftFkResolver(NamedParameterJdbcTemplate jdbc) {
		this.jdbc = jdbc;
	}

	public int resolveSupplierId(String supplierName, String supplierCode) {
		String code = blankToNull(supplierCode);
		String name = blankToNull(supplierName);
		if (code != null) {
			return uniqueId("""
					SELECT id FROM suppliers
					WHERE status = 'Active' AND supplier_code = :c
					""", Map.of("c", code), "Mã NCC");
		}
		if (name != null) {
			return uniqueId("""
					SELECT id FROM suppliers
					WHERE status = 'Active' AND name ILIKE :n
					""", Map.of("n", name.trim()), "Tên NCC");
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Thiếu supplierName hoặc supplierCode");
	}

	public int resolveProductId(String skuCode, String productName) {
		String sku = blankToNull(skuCode);
		if (sku != null) {
			return uniqueId("""
					SELECT id FROM products
					WHERE status = 'Active' AND sku_code = :s
					""", Map.of("s", sku), "Mã SKU");
		}
		String name = blankToNull(productName);
		if (name != null) {
			return uniqueId("""
					SELECT id FROM products
					WHERE status = 'Active' AND name ILIKE :n
					""", Map.of("n", name.trim()), "Tên sản phẩm");
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Thiếu skuCode hoặc productName");
	}

	public int resolveBaseUnitId(int productId) {
		List<Integer> ids = jdbc.query(
				"""
						SELECT id FROM productunits
						WHERE product_id = :pid AND is_base_unit = TRUE
						LIMIT 2
						""",
				Map.of("pid", productId),
				(rs, rn) -> rs.getInt("id"));
		if (ids.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST,
					"Sản phẩm id=" + productId + " không có đơn vị cơ sở");
		}
		return ids.getFirst();
	}

	private int uniqueId(String sql, Map<String, ?> params, String label) {
		List<Integer> ids = jdbc.query(sql, params, (rs, rn) -> rs.getInt("id"));
		if (ids.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Không tìm thấy " + label + " trong hệ thống");
		}
		if (ids.size() > 1) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST,
					label + " không duy nhất — hãy dùng mã thay vì tên");
		}
		return ids.getFirst();
	}

	private static String blankToNull(String s) {
		if (s == null || s.isBlank()) {
			return null;
		}
		return s.trim();
	}
}
