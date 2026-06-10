package com.example.smart_erp.sales.stock;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.Year;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.finance.ledger.dispatch.DispatchLedgerPostingService;
import com.example.smart_erp.sales.dto.SalesOrderLineRequest;

@Service
public class RetailStockService {

	private static final Pattern INV_ID_PATTERN = Pattern.compile("\\binvId=(\\d+)\\b");

	private final RetailStockJdbcRepository repo;
	private final DispatchLedgerPostingService dispatchLedgerPostingService;

	public RetailStockService(RetailStockJdbcRepository repo, DispatchLedgerPostingService dispatchLedgerPostingService) {
		this.repo = repo;
		this.dispatchLedgerPostingService = dispatchLedgerPostingService;
	}

	@Transactional(readOnly = true)
	public int requireDefaultRetailLocationId() {
		int locationId = repo.findDefaultRetailLocationId()
				.orElseThrow(() -> new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR,
						"Chưa cấu hình kho mặc định cho POS. Vui lòng cập nhật StoreProfiles."));
		if (locationId <= 0) {
			throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR,
					"Chưa cấu hình kho mặc định cho POS. Vui lòng cập nhật StoreProfiles.");
		}
		return locationId;
	}

	@Transactional
	public long deductStockForRetailCheckout(int orderId, String orderCode, int userId, List<SalesOrderLineRequest> lines) {
		int locationId = requireDefaultRetailLocationId();

		Map<Integer, Integer> requiredBaseByProduct = computeRequiredBaseByProduct(lines);

		Map<Integer, Integer> baseUnitIds = repo.findBaseUnitIds(new ArrayList<>(requiredBaseByProduct.keySet()));
		List<RetailStockJdbcRepository.InventoryBucketRow> allBuckets = repo
				.lockInventoryBucketsFefoBatch(new ArrayList<>(requiredBaseByProduct.keySet()), locationId);
		Map<Integer, List<RetailStockJdbcRepository.InventoryBucketRow>> bucketsByProduct = allBuckets.stream()
				.collect(Collectors.groupingBy(RetailStockJdbcRepository.InventoryBucketRow::productId));

		// Lock + kiểm tra tồn
		Map<String, String> insufficient = new LinkedHashMap<>();
		for (var e : requiredBaseByProduct.entrySet()) {
			int productId = e.getKey();
			int required = e.getValue();
			List<RetailStockJdbcRepository.InventoryBucketRow> buckets = bucketsByProduct.getOrDefault(productId,
					List.of());
			int avail = buckets.stream().mapToInt(RetailStockJdbcRepository.InventoryBucketRow::quantityBase).sum();
			if (avail < required) {
				insufficient.put("productId:" + productId, "Không đủ tồn. Còn " + avail + ", cần " + required + ".");
			}
		}
		if (!insufficient.isEmpty()) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không đủ tồn kho để thanh toán.", insufficient);
		}

		LocalDate today = LocalDate.now(ZoneId.systemDefault());
		String tmpCode = "TMP-" + java.util.UUID.randomUUID().toString().replace("-", "");
		long dispatchId = repo.insertStockDispatchTempCode(tmpCode, orderId, userId, today, "Full",
				"POS checkout " + orderCode);
		repo.updateStockDispatchCode(dispatchId, buildDispatchCode(dispatchId));

		// Cấp phát FEFO + ghi log
		Map<Long, Integer> idToDeduct = new LinkedHashMap<>();
		List<RetailStockJdbcRepository.LogEntry> logEntries = new ArrayList<>();
		for (var e : requiredBaseByProduct.entrySet()) {
			int productId = e.getKey();
			int required = e.getValue();
			Integer baseUnitId = baseUnitIds.get(productId);
			if (baseUnitId == null) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST,
						"Sản phẩm không có đơn vị cơ sở: " + productId);
			}
			int remain = required;
			for (var b : bucketsByProduct.getOrDefault(productId, List.of())) {
				if (remain <= 0) break;
				int take = Math.min(remain, b.quantityBase());
				idToDeduct.merge(b.inventoryId(), take, Integer::sum);
				String note = "POS_CHECKOUT orderId=" + orderId + " invId=" + b.inventoryId();
				logEntries.add(new RetailStockJdbcRepository.LogEntry(productId, take, baseUnitId, userId, dispatchId,
						locationId, note));
				remain -= take;
			}
			if (remain != 0) {
				// Defensive: đã check đủ tồn trước đó; nếu còn → rollback.
				throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR,
						"Không thể cấp phát tồn kho cho sản phẩm: " + productId);
			}
		}
		repo.deductInventoryQuantitiesBatch(idToDeduct);
		repo.batchInsertInventoryLogOutbound(logEntries);

		repo.markOrderLinesDispatchedAll(orderId);
		dispatchLedgerPostingService.postPrimaryCogsIfAbsent(dispatchId, userId);
		return dispatchId;
	}

	@Transactional
	public void reverseDeductionForRetailCancel(int orderId, int userId) {
		List<Long> dispatchIds = repo.lockActiveDispatchIdsByOrder(orderId);
		if (dispatchIds.isEmpty()) {
			// Idempotent: không có phiếu xuất → coi như không cần hoàn kho.
			repo.resetOrderLinesDispatched(orderId);
			return;
		}
		for (long did : dispatchIds) {
			var logs = repo.loadOutboundLogsByDispatch(did);
			for (var l : logs) {
				if (l.fromLocationId() == null) {
					throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR,
							"Thiếu thông tin vị trí kho để hoàn tồn.");
				}
				int delta = Math.abs(l.quantityChange());
				long invId = parseInventoryIdFromNote(l.referenceNote())
						.orElseThrow(() -> new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR,
								"Thiếu thông tin tồn kho để hoàn kho. Vui lòng liên hệ quản trị."));
				repo.addInventory(invId, delta);
				String note = "POS_CANCEL orderId=" + orderId + " fromLogId=" + l.logId();
				repo.insertInventoryLogInbound(l.productId(), delta, l.unitId(), userId, did, l.fromLocationId(), note);
			}
			dispatchLedgerPostingService.reverseNetCogsIfNonZero(did, userId, "POS hủy đơn");
			repo.cancelDispatch(did, "Cancelled via SalesOrder cancel (POS reverse)");
		}
		repo.resetOrderLinesDispatched(orderId);
	}

	private Map<Integer, Integer> computeRequiredBaseByProduct(List<SalesOrderLineRequest> lines) {
		Map<Integer, Integer> m = new LinkedHashMap<>();
		for (var line : lines) {
			BigDecimal rate = repo.findConversionRate(line.unitId()).orElseThrow(
					() -> new BusinessException(ApiErrorCode.BAD_REQUEST, "Đơn vị không hợp lệ"));
			BigDecimal baseBd = rate.multiply(BigDecimal.valueOf(line.quantity())).setScale(0, RoundingMode.HALF_UP);
			if (baseBd.compareTo(BigDecimal.valueOf(Integer.MAX_VALUE)) > 0 || baseBd.signum() <= 0) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Số lượng quy đổi không hợp lệ");
			}
			int baseQty = baseBd.intValueExact();
			m.merge(line.productId(), baseQty, (a, b) -> {
				long sum = (long) a + (long) b;
				if (sum > Integer.MAX_VALUE) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Số lượng quy đổi không hợp lệ");
				}
				return (int) sum;
			});
		}
		return m;
	}

	private static String buildDispatchCode(long dispatchId) {
		int year = Year.now(ZoneId.systemDefault()).getValue();
		return "PX-" + year + "-" + String.format("%06d", dispatchId);
	}

	private static java.util.OptionalLong parseInventoryIdFromNote(String note) {
		if (note == null) return java.util.OptionalLong.empty();
		Matcher m = INV_ID_PATTERN.matcher(note);
		if (!m.find()) return java.util.OptionalLong.empty();
		try {
			return java.util.OptionalLong.of(Long.parseLong(m.group(1)));
		} catch (NumberFormatException e) {
			return java.util.OptionalLong.empty();
		}
	}
}

