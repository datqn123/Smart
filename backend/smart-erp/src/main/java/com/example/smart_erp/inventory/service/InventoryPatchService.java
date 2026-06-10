package com.example.smart_erp.inventory.service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import com.example.smart_erp.auth.repository.SystemLogJdbcRepository;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.patch.InventoryBulkPatchJsonParser;
import com.example.smart_erp.inventory.patch.InventoryBulkPatchJsonParser.BulkWorkItem;
import com.example.smart_erp.inventory.patch.InventoryPatchJsonParser;
import com.example.smart_erp.inventory.patch.ParsedInventoryPatch;
import com.example.smart_erp.inventory.repository.InventoryPatchJdbcRepository;
import com.example.smart_erp.inventory.repository.InventoryPatchJdbcRepository.InventoryLockRow;
import com.example.smart_erp.inventory.response.InventoryBulkPatchData;
import com.example.smart_erp.inventory.response.InventoryListItemData;

/**
 * PATCH meta một dòng tồn — SRS Task007; bulk — Task008 (mỗi dòng một log PATCH_INVENTORY).
 */
@Service
public class InventoryPatchService {

	private static final String CONFLICT_META = "Không thể cập nhật do xung đột trạng thái hoặc trùng lô tại cùng vị trí";

	private final InventoryPatchJdbcRepository patchRepo;
	private final InventoryListService inventoryListService;
	private final SystemLogJdbcRepository systemLogJdbcRepository;
	private final ObjectMapper objectMapper;

	public InventoryPatchService(InventoryPatchJdbcRepository patchRepo, InventoryListService inventoryListService,
			SystemLogJdbcRepository systemLogJdbcRepository, ObjectMapper objectMapper) {
		this.patchRepo = patchRepo;
		this.inventoryListService = inventoryListService;
		this.systemLogJdbcRepository = systemLogJdbcRepository;
		this.objectMapper = objectMapper;
	}

	@Transactional
	public InventoryListItemData patchInventory(long inventoryId, JsonNode body, Jwt jwt) {
		ParsedInventoryPatch p = InventoryPatchJsonParser.parse(body);
		InventoryListItemData data = applyPatchCore(inventoryId, p, jwt);
		notifyOwnersSinglePatch(data, jwt);
		return data;
	}

	@Transactional
	public InventoryBulkPatchData patchBulkInventory(JsonNode root, Jwt jwt) {
		List<BulkWorkItem> works = InventoryBulkPatchJsonParser.parseAndPrepare(root);
		record Ordered(int requestIndex, InventoryListItemData data) {
		}
		var ordered = new ArrayList<Ordered>();
		for (BulkWorkItem w : works) {
			try {
				ordered.add(new Ordered(w.requestIndex(), applyPatchCore(w.inventoryId(), w.patch(), jwt)));
			}
			catch (BusinessException ex) {
				throw remapBulkItemDetails(ex, w.requestIndex());
			}
		}
		ordered.sort(Comparator.comparingInt(Ordered::requestIndex));
		List<InventoryListItemData> updated = ordered.stream().map(Ordered::data).toList();
		notifyOwnersBulkPatch(updated, jwt, works.size());
		return InventoryBulkPatchData.of(updated);
	}

	/**
	 * Khóa dòng, kiểm tra Task007, UPDATE, một dòng SystemLogs PATCH_INVENTORY — không gửi notification.
	 */
	private InventoryListItemData applyPatchCore(long inventoryId, ParsedInventoryPatch p, Jwt jwt) {
		InventoryLockRow row = patchRepo.lockInventoryRow(inventoryId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy dòng tồn kho yêu cầu"));

		if ("Inactive".equalsIgnoreCase(row.productStatus())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, CONFLICT_META);
		}
		if ("Maintenance".equalsIgnoreCase(row.locationStatus())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, CONFLICT_META);
		}

		if (p.locationId().isPresent()) {
			int newLoc = p.locationId().get();
			String st = patchRepo.findWarehouseLocationStatus(newLoc)
					.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
							Map.of("locationId", "Vị trí kho không tồn tại")));
			if (!"Active".equalsIgnoreCase(st)) {
				throw new BusinessException(ApiErrorCode.CONFLICT, CONFLICT_META);
			}
		}

		if (p.unitId().isPresent()) {
			Optional<Integer> inner = p.unitId().get();
			if (inner.isPresent()) {
				int uid = inner.get();
				if (!patchRepo.productUnitBelongsToProduct(uid, row.productId())) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
							Map.of("unitId", "Đơn vị không thuộc sản phẩm của dòng tồn này"));
				}
			}
		}

		int effectiveLocation = p.locationId().orElse(row.locationId());
		String effectiveBatch = row.batchNumber();
		if (p.batchNumber().isPresent()) {
			effectiveBatch = p.batchNumber().get().orElse(null);
		}
		String batchKeyForDup = effectiveBatch == null ? "" : effectiveBatch;

		int dup = patchRepo.countDuplicateOtherLine(row.productId(), effectiveLocation, batchKeyForDup, inventoryId);
		if (dup > 0) {
			throw new BusinessException(ApiErrorCode.CONFLICT, CONFLICT_META);
		}

		boolean setLocation = p.locationId().isPresent();
		boolean setMin = p.minQuantity().isPresent();
		boolean setBatch = p.batchNumber().isPresent();
		boolean setExpiry = p.expiryDate().isPresent();
		boolean setUnit = p.unitId().isPresent();

		Integer unitArg = null;
		if (setUnit) {
			unitArg = p.unitId().get().orElse(null);
		}

		patchRepo.updateInventory(
				inventoryId,
				setLocation,
				setLocation ? p.locationId().get() : 0,
				setMin,
				setMin ? p.minQuantity().get() : 0,
				setBatch,
				setBatch ? p.batchNumber().get().orElse(null) : null,
				setExpiry,
				setExpiry ? p.expiryDate().get().orElse(null) : null,
				setUnit,
				unitArg);

		int userId = parseUserId(jwt);
		Map<String, Object> before = snapshotMeta(row);
		Map<String, Object> after = mergeAfter(row, p);
		String contextJson = writeContextJson(inventoryId, before, after);
		systemLogJdbcRepository.insertInventoryPatch(userId, contextJson);

		return inventoryListService.loadListItemForInventoryId(inventoryId);
	}

	private static BusinessException remapBulkItemDetails(BusinessException ex, int requestIndex) {
		Map<String, String> d = ex.getDetails();
		if (d == null || d.isEmpty()) {
			return ex;
		}
		String prefix = "items[" + requestIndex + "].";
		return new BusinessException(ex.getCode(), ex.getMessage(),
				InventoryBulkPatchJsonParser.prefixedDetails(ex, prefix));
	}

	private void notifyOwnersSinglePatch(InventoryListItemData data, Jwt jwt) {
		if (!shouldNotifyOwners(jwt)) {
			return;
		}
		long inventoryId = data.id();
		String actorName = jwt.hasClaim("name") ? Objects.toString(jwt.getClaim("name"), "user") : "user";
		String sku = StringUtils.hasText(data.skuCode()) ? data.skuCode() : "—";
		String title = "Nhân viên cập nhật tồn kho";
		String message = actorName + " vừa cập nhật meta tồn kho SKU " + sku + " (id=" + inventoryId + ").";
		int userId = parseUserId(jwt);
		patchRepo.insertNotificationsForOwners(title, message, (int) inventoryId, userId);
	}

	private void notifyOwnersBulkPatch(List<InventoryListItemData> updated, Jwt jwt, int rowCount) {
		if (!shouldNotifyOwners(jwt) || updated.isEmpty()) {
			return;
		}
		String actorName = jwt.hasClaim("name") ? Objects.toString(jwt.getClaim("name"), "user") : "user";
		String title = "Nhân viên cập nhật tồn kho";
		String message = actorName + " vừa cập nhật meta " + rowCount + " dòng tồn kho (hàng loạt).";
		int refId = (int) updated.get(0).id();
		int userId = parseUserId(jwt);
		patchRepo.insertNotificationsForOwners(title, message, refId, userId);
	}

	private static boolean shouldNotifyOwners(Jwt jwt) {
		String role = jwt.getClaimAsString("role");
		if (!StringUtils.hasText(role)) {
			return true;
		}
		return !"Owner".equalsIgnoreCase(role.trim());
	}

	private static int parseUserId(Jwt jwt) {
		try {
			return Integer.parseInt(jwt.getSubject());
		}
		catch (NumberFormatException e) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, "Phiên đăng nhập không hợp lệ");
		}
	}

	private static Map<String, Object> snapshotMeta(InventoryLockRow row) {
		var m = new LinkedHashMap<String, Object>();
		m.put("locationId", row.locationId());
		m.put("minQuantity", row.minQuantity());
		m.put("batchNumber", row.batchNumber());
		m.put("expiryDate", row.expiryDate() != null ? row.expiryDate().toString() : null);
		m.put("unitId", row.unitId());
		return m;
	}

	private static Map<String, Object> mergeAfter(InventoryLockRow row, ParsedInventoryPatch p) {
		int loc = p.locationId().orElse(row.locationId());
		int min = p.minQuantity().orElse(row.minQuantity());
		String batch = row.batchNumber();
		if (p.batchNumber().isPresent()) {
			batch = p.batchNumber().get().orElse(null);
		}
		String exp = row.expiryDate() != null ? row.expiryDate().toString() : null;
		if (p.expiryDate().isPresent()) {
			exp = p.expiryDate().get().map(java.time.LocalDate::toString).orElse(null);
		}
		Integer unit = row.unitId();
		if (p.unitId().isPresent()) {
			unit = p.unitId().get().orElse(null);
		}
		var m = new LinkedHashMap<String, Object>();
		m.put("locationId", loc);
		m.put("minQuantity", min);
		m.put("batchNumber", batch);
		m.put("expiryDate", exp);
		m.put("unitId", unit);
		return m;
	}

	private String writeContextJson(long inventoryId, Map<String, Object> before, Map<String, Object> after) {
		var root = new LinkedHashMap<String, Object>();
		root.put("inventoryId", inventoryId);
		root.put("before", before);
		root.put("after", after);
		try {
			return objectMapper.writeValueAsString(root);
		}
		catch (JsonProcessingException e) {
			throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Không thể ghi nhật ký hệ thống");
		}
	}
}
