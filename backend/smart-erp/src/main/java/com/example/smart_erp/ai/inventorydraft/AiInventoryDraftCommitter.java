package com.example.smart_erp.ai.inventorydraft;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptCreateRequest;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptDetailRequest;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptLifecycleService;
import com.example.smart_erp.inventory.receipts.response.StockReceiptViewData;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

@Component
public class AiInventoryDraftCommitter {

	private final InventoryDraftFkResolver fkResolver;
	private final StockReceiptLifecycleService receiptLifecycleService;

	public AiInventoryDraftCommitter(
			InventoryDraftFkResolver fkResolver,
			StockReceiptLifecycleService receiptLifecycleService) {
		this.fkResolver = fkResolver;
		this.receiptLifecycleService = receiptLifecycleService;
	}

	public StockReceiptViewData commitStockReceipt(ObjectNode header, ArrayNode lines, Jwt jwt) {
		int supplierId = fkResolver.resolveSupplierId(
				text(header, "supplierName"),
				text(header, "supplierCode"));
		String receiptDate = requireText(header, "receiptDate", 10);
		try {
			LocalDate.parse(receiptDate);
		}
		catch (DateTimeParseException e) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "receiptDate không hợp lệ (YYYY-MM-DD)");
		}
		String saveMode = textOrDefault(header, "saveMode", "draft");
		if (!"draft".equals(saveMode) && !"pending".equals(saveMode)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "saveMode phải là draft hoặc pending");
		}
		if (lines == null || lines.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Phiếu nhập phải có ít nhất một dòng");
		}
		List<StockReceiptDetailRequest> details = new ArrayList<>();
		Set<String> batchKeys = new HashSet<>();
		for (JsonNode lineNode : lines) {
			if (!lineNode.isObject()) {
				continue;
			}
			ObjectNode line = (ObjectNode) lineNode;
			JsonNode values = line.has("values") && line.get("values").isObject()
					? line.get("values")
					: line;
			int productId = fkResolver.resolveProductId(
					text((ObjectNode) values, "skuCode"),
					text((ObjectNode) values, "productName"));
			int unitId = fkResolver.resolveBaseUnitId(productId);
			int quantity = intPositive(values, "quantity");
			BigDecimal costPrice = decimalNonNegative(values, "costPrice");
			String batchNumber = blankToNull(text((ObjectNode) values, "batchNumber"));
			if (batchNumber != null) {
				String key = productId + "|" + batchNumber;
				if (!batchKeys.add(key)) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST,
							"Trùng lô (product + batchNumber) trong cùng phiếu");
				}
			}
			String expiryDate = blankToNull(text((ObjectNode) values, "expiryDate"));
			if (expiryDate != null) {
				LocalDate exp = LocalDate.parse(expiryDate);
				LocalDate rd = LocalDate.parse(receiptDate);
				if (exp.isBefore(rd)) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST,
							"Hạn sử dụng không được nhỏ hơn ngày nhập");
				}
			}
			details.add(new StockReceiptDetailRequest(
					productId, unitId, quantity, costPrice, batchNumber, expiryDate));
		}
		if (details.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Không có dòng hợp lệ");
		}
		StockReceiptCreateRequest req = new StockReceiptCreateRequest(
				supplierId,
				receiptDate,
				blankToNull(text(header, "invoiceNumber")),
				blankToNull(text(header, "notes")),
				saveMode,
				details);
		return receiptLifecycleService.create(req, jwt);
	}

	private static String text(ObjectNode node, String field) {
		if (node == null || !node.has(field) || node.get(field).isNull()) {
			return null;
		}
		String s = node.get(field).asText();
		return s == null || s.isBlank() ? null : s.trim();
	}

	private static String textOrDefault(ObjectNode node, String field, String def) {
		String t = text(node, field);
		return t == null ? def : t;
	}

	private static String requireText(ObjectNode node, String field, int maxLen) {
		String t = text(node, field);
		if (t == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Thiếu " + field);
		}
		if (t.length() > maxLen) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, field + " quá dài");
		}
		return t;
	}

	private static int intPositive(JsonNode values, String field) {
		if (values == null || !values.has(field) || values.get(field).isNull()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Thiếu " + field);
		}
		int n = values.get(field).asInt(0);
		if (n <= 0) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, field + " phải > 0");
		}
		return n;
	}

	private static BigDecimal decimalNonNegative(JsonNode values, String field) {
		if (values == null || !values.has(field) || values.get(field).isNull()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Thiếu " + field);
		}
		BigDecimal d = values.get(field).decimalValue();
		if (d.compareTo(BigDecimal.ZERO) < 0) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, field + " phải >= 0");
		}
		return d;
	}

	private static String blankToNull(String s) {
		return StringUtils.hasText(s) ? s.trim() : null;
	}
}
