package com.example.smart_erp.inventory.service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.query.InventoryListQuery;
import com.example.smart_erp.inventory.repository.InventoryListJdbcRepository;
import com.example.smart_erp.inventory.repository.InventoryListJdbcRepository.InventoryListRow;
import com.example.smart_erp.inventory.repository.InventoryListJdbcRepository.InventoryRelatedLineRow;
import com.example.smart_erp.inventory.repository.InventoryListJdbcRepository.InventorySummaryWithCount;
import com.example.smart_erp.inventory.response.InventoryByIdData;
import com.example.smart_erp.inventory.response.InventoryListItemData;
import com.example.smart_erp.inventory.response.InventoryListPageData;
import com.example.smart_erp.inventory.response.InventoryRelatedLineData;
import com.example.smart_erp.inventory.response.InventorySummaryData;

/**
 * Tổng hợp 3 tầng đọc + tính read-model — SRS Task005.
 */
@Service
public class InventoryListService {

	private static final int EXPIRY_SOON_DAYS = 30;

	private final InventoryListJdbcRepository listRepo;

	public InventoryListService(InventoryListJdbcRepository listRepo) {
		this.listRepo = listRepo;
	}

	/** Task009 — chỉ KPI; cùng SQL aggregate + WHERE như {@link #list}. */
	@Transactional(readOnly = true)
	public InventorySummaryData summary(InventoryListQuery q) {
		return listRepo.loadSummary(q);
	}

	@Transactional(readOnly = true)
	public InventoryListPageData list(InventoryListQuery q) {
		InventorySummaryWithCount sc = listRepo.loadSummaryWithCount(q);
		List<InventoryListRow> rows = listRepo.loadPage(q);
		LocalDate thirtyAhead = LocalDate.now(ZoneOffset.UTC).plusDays(EXPIRY_SOON_DAYS);
		var items = rows.stream().map(r -> toItem(r, thirtyAhead)).collect(Collectors.toList());
		return new InventoryListPageData(sc.summary(), items, q.page(), q.limit(), sc.total());
	}

	/** Task007 — đọc lại một dòng list sau PATCH (cùng read-model Task005). */
	@Transactional(readOnly = true)
	public InventoryListItemData loadListItemForInventoryId(long inventoryId) {
		var row = listRepo.findById(inventoryId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy dòng tồn kho yêu cầu"));
		LocalDate thirtyAhead = LocalDate.now(ZoneOffset.UTC).plusDays(EXPIRY_SOON_DAYS);
		return toItem(row, thirtyAhead);
	}

	/** Task006 — chi tiết một dòng; {@code includeRelatedLines} theo query {@code include=relatedLines}. */
	@Transactional(readOnly = true)
	public InventoryByIdData getById(long inventoryId, boolean includeRelatedLines) {
		var row = listRepo.findById(inventoryId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy dòng tồn kho yêu cầu"));
		LocalDate thirtyAhead = LocalDate.now(ZoneOffset.UTC).plusDays(EXPIRY_SOON_DAYS);
		InventoryListItemData item = toItem(row, thirtyAhead);
		List<InventoryRelatedLineData> related = includeRelatedLines
				? listRepo.findRelatedLines(row.productId(), inventoryId).stream().map(InventoryListService::toRelatedLine)
						.collect(Collectors.toList())
				: List.of();
		return InventoryByIdData.fromItem(item, related);
	}

	private static InventoryRelatedLineData toRelatedLine(InventoryRelatedLineRow r) {
		return new InventoryRelatedLineData(
				r.id(),
				r.batchNumber(),
				r.quantity(),
				r.expiryDate(),
				r.warehouseCode(),
				r.shelfCode());
	}

	private static InventoryListItemData toItem(InventoryListRow r, LocalDate thirtyAhead) {
		int qn = r.quantity();
		int min = r.minQuantity();
		boolean isLow = qn > 0 && qn <= min;
		var exp = r.expiryDate();
		boolean isExp = exp != null && !exp.isAfter(thirtyAhead) && qn > 0;
		BigDecimal cost = r.costPrice() != null ? r.costPrice() : BigDecimal.ZERO;
		BigDecimal lineVal = cost.multiply(BigDecimal.valueOf(qn)).setScale(2, RoundingMode.HALF_UP);
		Instant upd = r.updatedAt() != null ? r.updatedAt() : Instant.EPOCH;
		return new InventoryListItemData(
				r.id(),
				r.productId(),
				r.productName(),
				r.skuCode(),
				r.barcode(),
				r.locationId(),
				r.warehouseCode(),
				r.shelfCode(),
				r.batchNumber(),
				r.expiryDate(),
				r.quantity(),
				r.minQuantity(),
				r.unitId(),
				r.unitName(),
				cost,
				upd,
				isLow,
				isExp,
				lineVal);
	}
}
