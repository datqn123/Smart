package com.example.smart_erp.settings.tablecolumns.service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.example.smart_erp.auth.repository.SystemLogJdbcRepository;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;
import com.example.smart_erp.settings.tablecolumns.dto.SaveTableColumnSettingsRequest;
import com.example.smart_erp.settings.tablecolumns.model.TableColumnCatalog;
import com.example.smart_erp.settings.tablecolumns.model.TableColumnCatalog.ColumnMeta;
import com.example.smart_erp.settings.tablecolumns.model.TableColumnCatalog.TableKey;
import com.example.smart_erp.settings.tablecolumns.repository.GlobalTableColumnSettingsJdbcRepository;
import com.example.smart_erp.settings.tablecolumns.response.TableColumnSettingsData;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
@SuppressWarnings("null")
public class TableColumnSettingsService {

	private static final TypeReference<List<String>> LIST_OF_STRING = new TypeReference<>() {
	};
	private static final String BAD_PAYLOAD_MESSAGE = "Dữ liệu cấu hình cột không hợp lệ. Vui lòng kiểm tra lại.";
	private static final String FORBIDDEN_GLOBAL_SAVE_MESSAGE = "Bạn không có quyền cấu hình giao diện toàn hệ thống.";

	private final GlobalTableColumnSettingsJdbcRepository repo;
	private final ObjectMapper objectMapper;
	private final SystemLogJdbcRepository systemLogJdbcRepository;

	public TableColumnSettingsService(GlobalTableColumnSettingsJdbcRepository repo, ObjectMapper objectMapper,
			SystemLogJdbcRepository systemLogJdbcRepository) {
		this.repo = repo;
		this.objectMapper = objectMapper;
		this.systemLogJdbcRepository = systemLogJdbcRepository;
	}

	@Transactional(readOnly = true)
	public TableColumnSettingsData getInventoryScope(Jwt jwt) {
		Map<String, GlobalTableColumnSettingsJdbcRepository.Row> byKey = new LinkedHashMap<>();
		for (GlobalTableColumnSettingsJdbcRepository.Row row : repo.findAll()) {
			byKey.put(row.tableKey(), row);
		}
		List<TableColumnSettingsData.ItemData> out = new ArrayList<>();
		for (TableKey tableKey : TableColumnCatalog.inventoryScope()) {
			out.add(toItemData(tableKey, byKey.get(tableKey.key())));
		}
		return new TableColumnSettingsData(out);
	}

	@Transactional
	public TableColumnSettingsData saveInventoryScope(Jwt jwt, SaveTableColumnSettingsRequest request) {
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		assertCanManageGlobalScope(jwt);
		if (request == null || request.items() == null || request.items().isEmpty() || request.items().size() > 3) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_PAYLOAD_MESSAGE, Map.of("items", "Danh sách items phải có từ 1 đến 3 phần tử"));
		}
		Set<String> seenTableKey = new LinkedHashSet<>();
		for (int i = 0; i < request.items().size(); i++) {
			SaveTableColumnSettingsRequest.Item item = request.items().get(i);
			TableKey tableKey = parseTableKey(item.tableKey(), i);
			if (!seenTableKey.add(tableKey.key())) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_PAYLOAD_MESSAGE,
						Map.of("items[" + i + "].tableKey", "tableKey bị trùng"));
			}
			Normalized normalized = normalizePayload(item, tableKey, i);
			repo.upsert(tableKey.key(), asJson(normalized.hiddenColumns()), asJson(normalized.columnOrder()), userId);
		}
		systemLogJdbcRepository.insertInventoryPatch(userId, "{\"entity\":\"GlobalTableColumnSettings\",\"scope\":\"inventory\"}");
		return getInventoryScope(jwt);
	}

	private TableKey parseTableKey(String value, int index) {
		TableKey tableKey = TableColumnCatalog.TableKey.fromWire(value);
		if (tableKey == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_PAYLOAD_MESSAGE,
					Map.of("items[" + index + "].tableKey", "tableKey không hợp lệ"));
		}
		return tableKey;
	}

	private Normalized normalizePayload(SaveTableColumnSettingsRequest.Item item, TableKey tableKey, int index) {
		List<ColumnMeta> metas = TableColumnCatalog.columns(tableKey);
		Set<String> known = metas.stream().map(ColumnMeta::key).collect(java.util.stream.Collectors.toCollection(LinkedHashSet::new));
		Set<String> required = metas.stream().filter(ColumnMeta::required).map(ColumnMeta::key)
				.collect(java.util.stream.Collectors.toCollection(LinkedHashSet::new));

		List<String> hiddenColumns = item.hiddenColumns() == null ? List.of() : item.hiddenColumns();
		Set<String> hiddenNorm = new LinkedHashSet<>();
		for (String col : hiddenColumns) {
			String key = normalizeKey(col);
			if (!known.contains(key)) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_PAYLOAD_MESSAGE,
						Map.of("items[" + index + "].hiddenColumns", "Có cột không hợp lệ: " + key));
			}
			if (required.contains(key)) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_PAYLOAD_MESSAGE,
						Map.of("items[" + index + "].hiddenColumns", "Cột bắt buộc " + key + " không thể bị ẩn."));
			}
			hiddenNorm.add(key);
		}

		List<String> orderInput = item.columnOrder() == null ? List.of() : item.columnOrder();
		List<String> orderNorm = new ArrayList<>();
		Set<String> seen = new LinkedHashSet<>();
		for (String col : orderInput) {
			String key = normalizeKey(col);
			if (!known.contains(key)) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_PAYLOAD_MESSAGE,
						Map.of("items[" + index + "].columnOrder", "Có cột không hợp lệ: " + key));
			}
			if (!seen.add(key)) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_PAYLOAD_MESSAGE,
						Map.of("items[" + index + "].columnOrder", "columnOrder có cột bị trùng: " + key));
			}
			orderNorm.add(key);
		}
		for (ColumnMeta meta : metas) {
			if (!seen.contains(meta.key())) {
				orderNorm.add(meta.key());
			}
		}
		return new Normalized(List.copyOf(hiddenNorm), List.copyOf(orderNorm));
	}

	private TableColumnSettingsData.ItemData toItemData(TableKey tableKey, GlobalTableColumnSettingsJdbcRepository.Row row) {
		List<ColumnMeta> defaults = TableColumnCatalog.columns(tableKey);
		Set<String> known = defaults.stream().map(ColumnMeta::key).collect(java.util.stream.Collectors.toCollection(LinkedHashSet::new));
		Set<String> required = defaults.stream().filter(ColumnMeta::required).map(ColumnMeta::key)
				.collect(java.util.stream.Collectors.toCollection(LinkedHashSet::new));
		Set<String> hidden = new LinkedHashSet<>();
		List<String> order = defaults.stream().map(ColumnMeta::key).toList();
		java.time.Instant updatedAt = null;
		String updatedBy = null;
		if (row != null) {
			hidden = parseKnownSet(row.hiddenColumnsJson(), known);
			hidden.removeAll(required);
			order = normalizeStoredOrder(row.columnOrderJson(), defaults, known);
			updatedAt = row.updatedAt();
			updatedBy = row.updatedByName();
		}
		Map<String, Integer> orderMap = new LinkedHashMap<>();
		for (int i = 0; i < order.size(); i++) {
			orderMap.put(order.get(i), i);
		}
		final Set<String> finalHidden = hidden;
		List<TableColumnSettingsData.ColumnData> cols = defaults.stream()
				.map(meta -> new TableColumnSettingsData.ColumnData(
						meta.key(),
						meta.label(),
						meta.required(),
						meta.required() || !finalHidden.contains(meta.key()),
						orderMap.getOrDefault(meta.key(), meta.defaultOrder())))
				.sorted(java.util.Comparator.comparingInt(TableColumnSettingsData.ColumnData::order))
				.toList();
		return new TableColumnSettingsData.ItemData(tableKey.key(), tableKey.label(), cols, updatedAt, updatedBy);
	}

	private Set<String> parseKnownSet(String json, Set<String> known) {
		List<String> parsed = parseStringList(json);
		Set<String> out = new LinkedHashSet<>();
		for (String key : parsed) {
			String n = normalizeKey(key);
			if (known.contains(n)) {
				out.add(n);
			}
		}
		return out;
	}

	private List<String> normalizeStoredOrder(String json, List<ColumnMeta> defaults, Set<String> known) {
		List<String> parsed = parseStringList(json);
		List<String> out = new ArrayList<>();
		Set<String> seen = new LinkedHashSet<>();
		for (String key : parsed) {
			String n = normalizeKey(key);
			if (known.contains(n) && seen.add(n)) {
				out.add(n);
			}
		}
		for (ColumnMeta meta : defaults) {
			if (!seen.contains(meta.key())) {
				out.add(meta.key());
			}
		}
		return out;
	}

	private List<String> parseStringList(String json) {
		if (!StringUtils.hasText(json)) {
			return List.of();
		}
		try {
			List<String> parsed = objectMapper.readValue(json, LIST_OF_STRING);
			return parsed == null ? List.of() : parsed;
		}
		catch (Exception ex) {
			return List.of();
		}
	}

	private static String normalizeKey(String value) {
		if (!StringUtils.hasText(value)) {
			return "";
		}
		return value.trim();
	}

	private String asJson(Object value) {
		try {
			return objectMapper.writeValueAsString(value);
		}
		catch (Exception ex) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_PAYLOAD_MESSAGE);
		}
	}

	private static void assertCanManageGlobalScope(Jwt jwt) {
		String role = jwt.getClaimAsString("role");
		if (!StringUtils.hasText(role)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, FORBIDDEN_GLOBAL_SAVE_MESSAGE);
		}
		String normalized = role.trim();
		if (!"Owner".equalsIgnoreCase(normalized) && !"Admin".equalsIgnoreCase(normalized)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, FORBIDDEN_GLOBAL_SAVE_MESSAGE);
		}
	}

	private record Normalized(List<String> hiddenColumns, List<String> columnOrder) {
	}
}
