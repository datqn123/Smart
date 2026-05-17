package com.example.smart_erp.ai.catalogdraft;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import com.example.smart_erp.ai.catalogdraft.dto.CatalogDraftReferenceValidationResult;
import com.example.smart_erp.catalog.repository.CategoryJdbcRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

@Component
public class CatalogDraftReferenceValidator {

	private final NamedParameterJdbcTemplate jdbc;
	private final CategoryJdbcRepository categoryJdbcRepository;

	public CatalogDraftReferenceValidator(
			NamedParameterJdbcTemplate jdbc,
			CategoryJdbcRepository categoryJdbcRepository) {
		this.jdbc = jdbc;
		this.categoryJdbcRepository = categoryJdbcRepository;
	}

	public CatalogDraftReferenceValidationResult validate(CatalogEntityType entityType, ArrayNode rows) {
		List<String> issues = new ArrayList<>();
		Set<String> batchSku = new HashSet<>();
		Set<String> batchCategoryCode = new HashSet<>();
		Set<String> batchCategoryName = new HashSet<>();
		Set<String> batchSupplierCode = new HashSet<>();
		Set<String> batchCustomerCode = new HashSet<>();
		int lineNo = 0;
		for (JsonNode rowNode : rows) {
			if (!rowNode.isObject()) {
				continue;
			}
			lineNo++;
			ObjectNode row = (ObjectNode) rowNode;
			JsonNode valuesNode = row.has("values") && row.get("values").isObject()
					? row.get("values")
					: row;
			if (!valuesNode.isObject()) {
				issues.add("Dòng " + lineNo + ": thiếu values");
				continue;
			}
			ObjectNode values = (ObjectNode) valuesNode;
			switch (entityType) {
				case PRODUCT -> validateProductLine(lineNo, values, issues, batchSku);
				case CATEGORY -> validateCategoryLine(lineNo, values, issues, batchCategoryCode, batchCategoryName);
				case SUPPLIER -> validateSupplierLine(lineNo, values, issues, batchSupplierCode);
				case CUSTOMER -> validateCustomerLine(lineNo, values, issues, batchCustomerCode);
			}
		}
		if (issues.isEmpty()) {
			return CatalogDraftReferenceValidationResult.success();
		}
		return CatalogDraftReferenceValidationResult.failure(issues);
	}

	private void validateProductLine(
			int lineNo,
			ObjectNode values,
			List<String> issues,
			Set<String> batchSku) {
		String sku = text(values, "skuCode");
		if (!StringUtils.hasText(sku)) {
			issues.add("Dòng " + lineNo + ": thiếu mã SKU");
			return;
		}
		String skuKey = sku.toLowerCase(Locale.ROOT);
		if (!batchSku.add(skuKey)) {
			issues.add("Dòng " + lineNo + ": mã SKU \"" + sku + "\" bị trùng trong bảng nháp");
		}
		if (activeProductExists(sku)) {
			issues.add("Dòng " + lineNo + ": mã SKU \"" + sku + "\" đã tồn tại — dùng SKU khác");
		}
		String categoryName = text(values, "categoryName");
		String categoryCode = text(values, "categoryCode");
		if (!StringUtils.hasText(categoryName) && !StringUtils.hasText(categoryCode)) {
			issues.add("Dòng " + lineNo + ": thiếu danh mục sản phẩm (categoryName hoặc categoryCode)");
			return;
		}
		if (StringUtils.hasText(categoryCode)) {
			if (categoryJdbcRepository.findActiveIdByExactCode(categoryCode).isEmpty()) {
				issues.add("Dòng " + lineNo + ": mã danh mục \"" + categoryCode + "\" không có trong hệ thống");
			}
		}
		else if (categoryJdbcRepository.findActiveIdByExactNameIgnoreCase(categoryName).isEmpty()) {
			issues.add("Dòng " + lineNo + ": danh mục \"" + categoryName + "\" không có trong hệ thống");
		}
	}

	private void validateCategoryLine(
			int lineNo,
			ObjectNode values,
			List<String> issues,
			Set<String> batchCategoryCode,
			Set<String> batchCategoryName) {
		String code = text(values, "categoryCode");
		String name = text(values, "name");
		if (!StringUtils.hasText(code)) {
			issues.add("Dòng " + lineNo + ": thiếu mã danh mục (categoryCode)");
		}
		if (!StringUtils.hasText(name)) {
			issues.add("Dòng " + lineNo + ": thiếu tên danh mục (name)");
		}
		if (!StringUtils.hasText(code) || !StringUtils.hasText(name)) {
			return;
		}
		String codeKey = code.toLowerCase(Locale.ROOT);
		if (!batchCategoryCode.add(codeKey)) {
			issues.add("Dòng " + lineNo + ": mã danh mục \"" + code + "\" bị trùng trong bảng nháp");
		}
		if (activeCategoryCodeExists(code)) {
			issues.add("Dòng " + lineNo + ": mã danh mục \"" + code + "\" đã tồn tại trong hệ thống");
		}
		String nameKey = name.toLowerCase(Locale.ROOT);
		if (!batchCategoryName.add(nameKey)) {
			issues.add("Dòng " + lineNo + ": tên danh mục \"" + name + "\" bị trùng trong bảng nháp");
		}
		if (categoryJdbcRepository.existsActiveWithNameIgnoreCase(name)) {
			issues.add("Dòng " + lineNo + ": tên danh mục \"" + name + "\" đã tồn tại trong hệ thống");
		}
		String parentName = text(values, "parentName");
		if (StringUtils.hasText(parentName)) {
			if (parentName.equalsIgnoreCase(name)) {
				issues.add("Dòng " + lineNo + ": danh mục cha không thể trùng tên danh mục con");
			}
			else if (categoryJdbcRepository.findActiveIdByExactNameIgnoreCase(parentName).isEmpty()) {
				issues.add("Dòng " + lineNo + ": danh mục cha \"" + parentName + "\" không có trong hệ thống");
			}
		}
	}

	private void validateSupplierLine(int lineNo, ObjectNode values, List<String> issues, Set<String> batchCodes) {
		String code = text(values, "supplierCode");
		if (!StringUtils.hasText(code)) {
			issues.add("Dòng " + lineNo + ": thiếu mã NCC (supplierCode)");
			return;
		}
		String codeKey = code.toLowerCase(Locale.ROOT);
		if (!batchCodes.add(codeKey)) {
			issues.add("Dòng " + lineNo + ": mã NCC \"" + code + "\" bị trùng trong bảng nháp");
		}
		if (activeSupplierCodeExists(code)) {
			issues.add("Dòng " + lineNo + ": mã NCC \"" + code + "\" đã tồn tại trong hệ thống");
		}
	}

	private void validateCustomerLine(int lineNo, ObjectNode values, List<String> issues, Set<String> batchCodes) {
		String code = text(values, "customerCode");
		if (!StringUtils.hasText(code)) {
			issues.add("Dòng " + lineNo + ": thiếu mã khách hàng (customerCode)");
			return;
		}
		String codeKey = code.toLowerCase(Locale.ROOT);
		if (!batchCodes.add(codeKey)) {
			issues.add("Dòng " + lineNo + ": mã khách hàng \"" + code + "\" bị trùng trong bảng nháp");
		}
		if (activeCustomerCodeExists(code)) {
			issues.add("Dòng " + lineNo + ": mã khách hàng \"" + code + "\" đã tồn tại trong hệ thống");
		}
	}

	private boolean activeProductExists(String skuCode) {
		Integer count = jdbc.queryForObject(
				"""
						SELECT COUNT(*)::int FROM products
						WHERE status = 'Active' AND sku_code = :sku
						""",
				Map.of("sku", skuCode.trim()),
				Integer.class);
		return count != null && count > 0;
	}

	private boolean activeCategoryCodeExists(String categoryCode) {
		return categoryJdbcRepository.existsActiveWithCode(categoryCode.trim());
	}

	private boolean activeSupplierCodeExists(String supplierCode) {
		Integer count = jdbc.queryForObject(
				"""
						SELECT COUNT(*)::int FROM suppliers
						WHERE status = 'Active' AND supplier_code = :c
						""",
				Map.of("c", supplierCode.trim()),
				Integer.class);
		return count != null && count > 0;
	}

	private boolean activeCustomerCodeExists(String customerCode) {
		Integer count = jdbc.queryForObject(
				"""
						SELECT COUNT(*)::int FROM customers
						WHERE status = 'Active' AND customer_code = :c
						""",
				Map.of("c", customerCode.trim()),
				Integer.class);
		return count != null && count > 0;
	}

	private static String text(ObjectNode node, String field) {
		if (node == null || !node.has(field) || node.get(field).isNull()) {
			return null;
		}
		String s = node.get(field).asText();
		return StringUtils.hasText(s) ? s.trim() : null;
	}
}
