package com.example.smart_erp.ai.catalogdraft;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import com.example.smart_erp.ai.catalogdraft.dto.CatalogDraftRowCommitOutcome;
import com.example.smart_erp.catalog.dto.CategoryCreateRequest;
import com.example.smart_erp.catalog.dto.CustomerCreateRequest;
import com.example.smart_erp.catalog.dto.ProductCreateRequest;
import com.example.smart_erp.catalog.dto.SupplierCreateRequest;
import com.example.smart_erp.catalog.repository.CategoryJdbcRepository;
import com.example.smart_erp.catalog.response.CategoryNodeResponse;
import com.example.smart_erp.catalog.response.CustomerData;
import com.example.smart_erp.catalog.response.ProductCreatedData;
import com.example.smart_erp.catalog.response.SupplierDetailData;
import com.example.smart_erp.catalog.service.CategoryService;
import com.example.smart_erp.catalog.service.CustomerService;
import com.example.smart_erp.catalog.service.ProductService;
import com.example.smart_erp.catalog.service.SupplierService;
import com.example.smart_erp.common.exception.BusinessException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

@Component
public class AiCatalogDraftCommitter {

	private final ProductService productService;
	private final CategoryService categoryService;
	private final SupplierService supplierService;
	private final CustomerService customerService;
	private final CategoryJdbcRepository categoryJdbcRepository;
	private final ObjectMapper objectMapper;

	public AiCatalogDraftCommitter(
			ProductService productService,
			CategoryService categoryService,
			SupplierService supplierService,
			CustomerService customerService,
			CategoryJdbcRepository categoryJdbcRepository,
			ObjectMapper objectMapper) {
		this.productService = productService;
		this.categoryService = categoryService;
		this.supplierService = supplierService;
		this.customerService = customerService;
		this.categoryJdbcRepository = categoryJdbcRepository;
		this.objectMapper = objectMapper;
	}

	public List<CatalogDraftRowCommitOutcome> commitRows(CatalogEntityType entityType, ArrayNode rows) {
		List<CatalogDraftRowCommitOutcome> outcomes = new ArrayList<>();
		for (JsonNode rowNode : rows) {
			if (!rowNode.isObject()) {
				continue;
			}
			ObjectNode row = (ObjectNode) rowNode;
			String rowId = textOrDefault(row, "rowId", "");
			if (row.hasNonNull("committedAt")) {
				outcomes.add(new CatalogDraftRowCommitOutcome(rowId, true,
						intOrNullNode(row.get("createdEntityId")), "Đã ghi trước đó", null));
				continue;
			}
			JsonNode values = row.get("values");
			if (values == null || !values.isObject()) {
				outcomes.add(fail(rowId, "Thiếu values cho dòng", null));
				continue;
			}
			try {
				int createdId = switch (entityType) {
					case PRODUCT -> commitProduct((ObjectNode) values);
					case CATEGORY -> commitCategory((ObjectNode) values);
					case SUPPLIER -> commitSupplier((ObjectNode) values);
					case CUSTOMER -> commitCustomer((ObjectNode) values);
				};
				row.put("committedAt", java.time.Instant.now().toString());
				row.put("createdEntityId", createdId);
				row.remove("lastError");
				outcomes.add(new CatalogDraftRowCommitOutcome(rowId, true, createdId, "Đã tạo", null));
			}
			catch (BusinessException be) {
				ObjectNode err = objectMapper.createObjectNode();
				if (be.getDetails() != null) {
					be.getDetails().forEach(err::put);
				}
				row.put("lastError", be.getMessage());
				outcomes.add(new CatalogDraftRowCommitOutcome(rowId, false, null, be.getMessage(),
						err.isEmpty() ? null : err));
			}
			catch (Exception e) {
				row.put("lastError", e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName());
				outcomes.add(fail(rowId, row.get("lastError").asText(), null));
			}
		}
		return outcomes;
	}

	private int commitProduct(ObjectNode v) {
		Integer categoryId = intOrNullNode(v.get("categoryId"));
		if (categoryId == null) {
			String catName = textOrNull(v, "categoryName");
			if (StringUtils.hasText(catName)) {
				categoryId = categoryJdbcRepository.findActiveIdByExactNameIgnoreCase(catName)
						.map(Long::intValue)
						.orElseThrow(() -> new BusinessException(
								com.example.smart_erp.common.api.ApiErrorCode.BAD_REQUEST,
								"Không tìm thấy danh mục theo tên",
								Map.of("categoryName", "Không khớp danh mục đang hoạt động")));
			}
		}
		BigDecimal cost = decimalRequired(v, "costPrice");
		BigDecimal sale = decimalRequired(v, "salePrice");
		String skuCode = required(v, "skuCode");
		java.util.Optional<Integer> existingIdOpt = productService.findIdBySku(skuCode);
		if (existingIdOpt.isPresent()) {
			int pid = existingIdOpt.get();
			ObjectNode patchBody = objectMapper.createObjectNode();
			patchBody.put("skuCode", skuCode);
			patchBody.put("name", required(v, "name"));
			if (categoryId != null) {
				patchBody.put("categoryId", categoryId);
			} else {
				patchBody.putNull("categoryId");
			}
			if (v.hasNonNull("barcode")) {
				patchBody.put("barcode", v.get("barcode").asText());
			}
			if (v.hasNonNull("description")) {
				patchBody.put("description", v.get("description").asText());
			}
			if (v.hasNonNull("weight")) {
				patchBody.put("weight", v.get("weight").decimalValue());
			}
			patchBody.put("status", textOrDefault(v, "status", "Active"));
			patchBody.put("costPrice", cost);
			patchBody.put("salePrice", sale);
			if (v.hasNonNull("priceEffectiveDate")) {
				patchBody.put("priceEffectiveDate", v.get("priceEffectiveDate").asText());
			}
			com.example.smart_erp.catalog.response.ProductDetailData updated = productService.patch(pid, patchBody);
			return updated.id();
		} else {
			ProductCreateRequest req = new ProductCreateRequest(
					skuCode,
					textOrNull(v, "barcode"),
					required(v, "name"),
					categoryId,
					textOrNull(v, "description"),
					decimalOptional(v, "weight"),
					textOrDefault(v, "status", "Active"),
					null,
					required(v, "baseUnitName", "Cái"),
					cost,
					sale,
					textOrNull(v, "priceEffectiveDate"));
			com.example.smart_erp.catalog.response.ProductCreatedData created = productService.create(req);
			return created.id();
		}
	}

	private int commitCategory(ObjectNode v) {
		Long parentId = longOrNullNode(v.get("parentId"));
		if (parentId == null) {
			String parentName = textOrNull(v, "parentName");
			if (StringUtils.hasText(parentName)) {
				parentId = categoryJdbcRepository.findActiveIdByExactNameIgnoreCase(parentName)
						.map(Long::valueOf)
						.orElseThrow(() -> new BusinessException(
								com.example.smart_erp.common.api.ApiErrorCode.BAD_REQUEST,
								"Không tìm thấy danh mục cha theo tên",
								Map.of("parentName", "Không khớp danh mục đang hoạt động")));
			}
		}
		Integer sortOrder = intOrNullNode(v.get("sortOrder"));
		String categoryCode = required(v, "categoryCode");
		java.util.Optional<Long> existingIdOpt = categoryService.findIdByCategoryCode(categoryCode);
		if (existingIdOpt.isPresent()) {
			long cid = existingIdOpt.get();
			ObjectNode patchBody = objectMapper.createObjectNode();
			patchBody.put("categoryCode", categoryCode);
			patchBody.put("name", required(v, "name"));
			if (v.hasNonNull("description")) {
				patchBody.put("description", v.get("description").asText());
			}
			if (parentId != null) {
				patchBody.put("parentId", parentId);
			} else {
				patchBody.putNull("parentId");
			}
			if (sortOrder != null) {
				patchBody.put("sortOrder", sortOrder);
			}
			patchBody.put("status", textOrDefault(v, "status", "Active"));
			CategoryNodeResponse updated = categoryService.patch(cid, patchBody);
			return Math.toIntExact(updated.id());
		} else {
			CategoryCreateRequest req = new CategoryCreateRequest(
					categoryCode,
					required(v, "name"),
					textOrNull(v, "description"),
					parentId,
					sortOrder,
					textOrDefault(v, "status", "Active"));
			CategoryNodeResponse created = categoryService.create(req);
			return Math.toIntExact(created.id());
		}
	}

	private int commitSupplier(ObjectNode v) {
		String supplierCode = required(v, "supplierCode");
		java.util.Optional<Integer> existingIdOpt = supplierService.findIdBySupplierCode(supplierCode);
		if (existingIdOpt.isPresent()) {
			int sid = existingIdOpt.get();
			ObjectNode patchBody = objectMapper.createObjectNode();
			patchBody.put("supplierCode", supplierCode);
			patchBody.put("name", required(v, "name"));
			patchBody.put("contactPerson", required(v, "contactPerson"));
			patchBody.put("phone", required(v, "phone"));
			if (v.hasNonNull("email")) {
				patchBody.put("email", v.get("email").asText());
			}
			if (v.hasNonNull("address")) {
				patchBody.put("address", v.get("address").asText());
			}
			if (v.hasNonNull("taxCode")) {
				patchBody.put("taxCode", v.get("taxCode").asText());
			}
			patchBody.put("status", textOrDefault(v, "status", "Active"));
			SupplierDetailData updated = supplierService.patch(sid, patchBody);
			return updated.id();
		} else {
			SupplierCreateRequest req = new SupplierCreateRequest(
					supplierCode,
					required(v, "name"),
					required(v, "contactPerson"),
					required(v, "phone"),
					textOrNull(v, "email"),
					textOrNull(v, "address"),
					textOrNull(v, "taxCode"),
					textOrDefault(v, "status", "Active"));
			SupplierDetailData created = supplierService.create(req);
			return created.id();
		}
	}

	private int commitCustomer(ObjectNode v) {
		String customerCode = required(v, "customerCode");
		java.util.Optional<Integer> existingIdOpt = customerService.findIdByCustomerCode(customerCode);
		if (existingIdOpt.isPresent()) {
			int cid = existingIdOpt.get();
			ObjectNode patchBody = objectMapper.createObjectNode();
			patchBody.put("customerCode", customerCode);
			patchBody.put("name", required(v, "name"));
			patchBody.put("phone", required(v, "phone"));
			if (v.hasNonNull("email")) {
				patchBody.put("email", v.get("email").asText());
			}
			if (v.hasNonNull("address")) {
				patchBody.put("address", v.get("address").asText());
			}
			patchBody.put("status", textOrDefault(v, "status", "Active"));
			CustomerData updated = customerService.patch(cid, patchBody);
			return updated.id();
		} else {
			CustomerCreateRequest req = new CustomerCreateRequest(
					customerCode,
					required(v, "name"),
					required(v, "phone"),
					textOrNull(v, "email"),
					textOrNull(v, "address"),
					textOrDefault(v, "status", "Active"));
			CustomerData created = customerService.create(req);
			return created.id();
		}
	}

	private static CatalogDraftRowCommitOutcome fail(String rowId, String message, JsonNode fieldErrors) {
		return new CatalogDraftRowCommitOutcome(rowId, false, null, message, fieldErrors);
	}

	private static String required(ObjectNode v, String key) {
		return required(v, key, null);
	}

	private static String required(ObjectNode v, String key, String defaultIfBlank) {
		String s = textOrNull(v, key);
		if (!StringUtils.hasText(s)) {
			if (defaultIfBlank != null) {
				return defaultIfBlank;
			}
			throw new BusinessException(com.example.smart_erp.common.api.ApiErrorCode.BAD_REQUEST,
					"Thiếu trường bắt buộc: " + key, Map.of(key, "Bắt buộc"));
		}
		return s.trim();
	}

	private static String textOrNull(ObjectNode v, String key) {
		JsonNode n = v.get(key);
		if (n == null || n.isNull()) {
			return null;
		}
		String s = n.asText().trim();
		return s.isEmpty() ? null : s;
	}

	private static String textOrDefault(ObjectNode row, String key, String defaultValue) {
		String s = textOrNull(row, key);
		return s != null ? s : defaultValue;
	}

	private static Integer intOrNullNode(JsonNode n) {
		if (n == null || n.isNull()) {
			return null;
		}
		if (n.isNumber()) {
			return n.intValue();
		}
		String s = n.asText().trim();
		if (s.isEmpty()) {
			return null;
		}
		try {
			return Integer.parseInt(s);
		}
		catch (NumberFormatException e) {
			return null;
		}
	}

	private static Long longOrNullNode(JsonNode n) {
		Integer i = intOrNullNode(n);
		return i == null ? null : i.longValue();
	}

	private static BigDecimal decimalRequired(ObjectNode v, String key) {
		BigDecimal d = decimalOptional(v, key);
		if (d == null) {
			throw new BusinessException(com.example.smart_erp.common.api.ApiErrorCode.BAD_REQUEST,
					"Thiếu trường bắt buộc: " + key, Map.of(key, "Bắt buộc"));
		}
		return d;
	}

	private static BigDecimal decimalOptional(ObjectNode v, String key) {
		JsonNode n = v.get(key);
		if (n == null || n.isNull()) {
			return null;
		}
		if (n.isNumber()) {
			return n.decimalValue();
		}
		String s = n.asText().trim();
		if (s.isEmpty()) {
			return null;
		}
		try {
			return new BigDecimal(s.replace(",", ""));
		}
		catch (NumberFormatException e) {
			throw new BusinessException(com.example.smart_erp.common.api.ApiErrorCode.BAD_REQUEST,
					key + " không phải số hợp lệ", Map.of(key, "Số không hợp lệ"));
		}
	}

}
