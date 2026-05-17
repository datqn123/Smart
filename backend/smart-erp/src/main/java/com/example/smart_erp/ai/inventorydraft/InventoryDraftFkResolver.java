package com.example.smart_erp.ai.inventorydraft;

import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Component;

import com.example.smart_erp.ai.inventorydraft.dto.DraftReferenceValidationResult;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

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

	/**
	 * Verify supplier and line SKUs exist in DB before showing inventory draft HITL UI.
	 */
	public DraftReferenceValidationResult validateStockReceipt(ObjectNode header, ArrayNode lines) {
		java.util.ArrayList<String> issues = new java.util.ArrayList<>();
		String supplierErr = tryResolveSupplierMessage(
				text(header, "supplierName"),
				text(header, "supplierCode"));
		if (supplierErr != null) {
			issues.add("Nhà cung cấp: " + supplierErr);
		}
		if (lines == null || lines.isEmpty()) {
			issues.add("Phiếu nhập phải có ít nhất một dòng hàng");
			return DraftReferenceValidationResult.failure(issues);
		}
		int lineNo = 0;
		for (JsonNode lineNode : lines) {
			if (!lineNode.isObject()) {
				continue;
			}
			lineNo++;
			ObjectNode line = (ObjectNode) lineNode;
			JsonNode valuesNode = line.has("values") && line.get("values").isObject()
					? line.get("values")
					: line;
			ObjectNode values = (ObjectNode) valuesNode;
			String sku = text(values, "skuCode");
			String productName = text(values, "productName");
			String productErr = tryResolveProductMessage(sku, productName);
			if (productErr != null) {
				String label = (sku != null && !sku.isBlank()) ? sku : (productName != null ? productName : "?");
				issues.add("Dòng " + lineNo + " (" + label + "): " + productErr);
			}
		}
		if (issues.isEmpty()) {
			return DraftReferenceValidationResult.success();
		}
		return DraftReferenceValidationResult.failure(issues);
	}

	private String tryResolveSupplierMessage(String supplierName, String supplierCode) {
		try {
			resolveSupplierId(supplierName, supplierCode);
			return null;
		}
		catch (BusinessException e) {
			return e.getMessage();
		}
	}

	private String tryResolveProductMessage(String skuCode, String productName) {
		try {
			resolveProductId(skuCode, productName);
			return null;
		}
		catch (BusinessException e) {
			return e.getMessage();
		}
	}

	private static String text(ObjectNode node, String field) {
		if (node == null || !node.has(field) || node.get(field).isNull()) {
			return null;
		}
		String s = node.get(field).asText();
		return s != null && !s.isBlank() ? s.trim() : null;
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
