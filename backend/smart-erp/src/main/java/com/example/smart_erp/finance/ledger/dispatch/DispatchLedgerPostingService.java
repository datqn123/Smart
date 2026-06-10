package com.example.smart_erp.finance.ledger.dispatch;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.StringJoiner;

import org.springframework.stereotype.Service;

import com.example.smart_erp.catalog.repository.ProductJdbcRepository;
import com.example.smart_erp.inventory.dispatch.ManualDispatchStatuses;
import com.example.smart_erp.inventory.dispatch.StockDispatchJdbcRepository;
import com.example.smart_erp.sales.stock.RetailStockJdbcRepository;

/**
 * Tính COGS và ghi {@code financeledger} cho phiếu xuất hoàn tất (SRS PRD finance-ledger-unified-business-postings).
 */
@SuppressWarnings("null")
@Service
public class DispatchLedgerPostingService {

	private static final String COGS_MISSING_PREFIX = "[COGS: thiếu giá vốn]";
	private static final String REVERSAL_DESC_PREFIX = "Hoàn COGS";

	private final StockDispatchJdbcRepository dispatchRepo;
	private final RetailStockJdbcRepository retailRepo;
	private final ProductJdbcRepository productRepo;
	private final FinanceLedgerDispatchPostingJdbcRepository postingRepo;

	public DispatchLedgerPostingService(StockDispatchJdbcRepository dispatchRepo, RetailStockJdbcRepository retailRepo,
			ProductJdbcRepository productRepo, FinanceLedgerDispatchPostingJdbcRepository postingRepo) {
		this.dispatchRepo = dispatchRepo;
		this.retailRepo = retailRepo;
		this.productRepo = productRepo;
		this.postingRepo = postingRepo;
	}

	/**
	 * Ghi một bút COGS “chính” nếu phiếu đã hoàn tất và chưa có bút tương ứng.
	 */
	public void postPrimaryCogsIfAbsent(long dispatchId, int userId) {
		int ref = Math.toIntExact(dispatchId);
		if (postingRepo.existsPrimaryCogsPosting(ref)) {
			return;
		}
		var meta = dispatchRepo.loadDispatchLedgerMeta(dispatchId).orElse(null);
		if (meta == null || !isCompletedDispatchStatus(meta.status())) {
			return;
		}
		CogsBuild built = computePrimaryCogs(dispatchId, meta.dispatchCode());
		if (built == null) {
			return;
		}
		postingRepo.insertOperatingExpenseStockDispatch(meta.dispatchDate(), ref, built.signedAmount(), built.description(),
				userId);
	}

	/** Bù số dư COGS (không xóa dòng cũ) khi hủy POS / đảo vốn. */
	public void reverseNetCogsIfNonZero(long dispatchId, int userId, String reasonShort) {
		int ref = Math.toIntExact(dispatchId);
		BigDecimal net = postingRepo.sumNetAmountForDispatch(ref);
		if (net.signum() == 0) {
			return;
		}
		var meta = dispatchRepo.loadDispatchLedgerMeta(dispatchId).orElse(null);
		if (meta == null) {
			return;
		}
		BigDecimal reversal = net.negate().setScale(2, RoundingMode.HALF_UP);
		String code = meta.dispatchCode() != null ? meta.dispatchCode() : ("id=" + ref);
		String desc = REVERSAL_DESC_PREFIX + " (" + reasonShort + ") " + code;
		postingRepo.insertOperatingExpenseStockDispatch(meta.dispatchDate(), ref, reversal, desc, userId);
	}

	private static boolean isCompletedDispatchStatus(String status) {
		if (status == null) {
			return false;
		}
		return ManualDispatchStatuses.DELIVERED.equalsIgnoreCase(status) || "Full".equalsIgnoreCase(status);
	}

	private CogsBuild computePrimaryCogs(long dispatchId, String dispatchCode) {
		List<StockDispatchJdbcRepository.DispatchCogsLineRow> lines = dispatchRepo.loadDispatchLinesForCogs(dispatchId);
		BigDecimal sumKnown = BigDecimal.ZERO;
		List<String> missing = new ArrayList<>();

		if (!lines.isEmpty()) {
			for (var line : lines) {
				BigDecimal unitCost = resolveUnitCost(line);
				if (unitCost == null) {
					missing.add(missingTagForLine(line));
				} else {
					sumKnown = sumKnown.add(unitCost.multiply(BigDecimal.valueOf(line.quantity())));
				}
			}
		} else {
			List<RetailStockJdbcRepository.ProductOutboundBaseQtyRow> agg = retailRepo.sumOutboundBaseQtyByProduct(dispatchId);
			if (agg.isEmpty()) {
				return null;
			}
			List<Integer> productIds = agg.stream().map(RetailStockJdbcRepository.ProductOutboundBaseQtyRow::productId)
					.toList();
			Map<Integer, Integer> baseUnitIds = retailRepo.findBaseUnitIds(productIds);
			List<RetailStockJdbcRepository.ProductUnitPair> costPairs = new ArrayList<>();
			for (var row : agg) {
				Integer baseUnitId = baseUnitIds.get(row.productId());
				if (baseUnitId != null) {
					costPairs.add(new RetailStockJdbcRepository.ProductUnitPair(row.productId(), baseUnitId));
				}
			}
			Map<RetailStockJdbcRepository.ProductUnitPair, BigDecimal> costPrices = retailRepo
					.findCurrentCostPrices(costPairs);
			for (var row : agg) {
				Integer baseUnitId = baseUnitIds.get(row.productId());
				if (baseUnitId == null) {
					missing.add("productId=" + row.productId());
					continue;
				}
				BigDecimal unitCost = costPrices.get(new RetailStockJdbcRepository.ProductUnitPair(row.productId(), baseUnitId));
				if (unitCost == null || unitCost.signum() <= 0) {
					missing.add("productId=" + row.productId());
				} else {
					sumKnown = sumKnown.add(unitCost.multiply(BigDecimal.valueOf(row.baseQty())));
				}
			}
		}

		sumKnown = sumKnown.setScale(2, RoundingMode.HALF_UP);
		String code = dispatchCode != null ? dispatchCode : ("id=" + dispatchId);

		if (!missing.isEmpty() && sumKnown.signum() == 0) {
			StringJoiner j = new StringJoiner(", ");
			missing.forEach(j::add);
			return new CogsBuild(BigDecimal.ZERO,
					COGS_MISSING_PREFIX + " " + code + " | " + j);
		}
		if (sumKnown.signum() > 0) {
			String desc = "Giá vốn xuất kho " + code;
			if (!missing.isEmpty()) {
				StringJoiner j = new StringJoiner(", ");
				missing.forEach(j::add);
				desc = desc + " | thiếu vốn: " + j;
			}
			return new CogsBuild(sumKnown.negate(), desc);
		}
		// Đủ dữ liệu nhưng vốn quy ra 0
		return new CogsBuild(BigDecimal.ZERO, "Giá vốn xuất kho " + code + " (vốn=0)");
	}

	private BigDecimal resolveUnitCost(StockDispatchJdbcRepository.DispatchCogsLineRow line) {
		if (line.unitPriceSnapshot() != null && line.unitPriceSnapshot().signum() > 0) {
			return line.unitPriceSnapshot();
		}
		return productRepo.findCurrentCostPrice(line.productId(), line.lineUnitId()).filter(c -> c.signum() > 0)
				.orElse(null);
	}

	private static String missingTagForLine(StockDispatchJdbcRepository.DispatchCogsLineRow line) {
		if (line.skuCode() != null && !line.skuCode().isBlank()) {
			return "sku=" + line.skuCode();
		}
		return "productId=" + line.productId() + " inv=" + line.inventoryId();
	}

	private record CogsBuild(BigDecimal signedAmount, String description) {
	}
}
