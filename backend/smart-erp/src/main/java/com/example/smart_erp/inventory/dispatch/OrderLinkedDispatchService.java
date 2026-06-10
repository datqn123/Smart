package com.example.smart_erp.inventory.dispatch;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.dispatch.response.StockDispatchCreatedData;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;
import com.example.smart_erp.sales.repository.SalesOrderJdbcRepository;

@Service
public class OrderLinkedDispatchService {

	private final StockDispatchJdbcRepository dispatchRepo;
	private final SalesOrderJdbcRepository salesOrderRepo;
	private final StockDispatchNotifier dispatchNotifier;
	private final ApplicationEventPublisher eventPublisher;

	public OrderLinkedDispatchService(StockDispatchJdbcRepository dispatchRepo,
			SalesOrderJdbcRepository salesOrderRepo, StockDispatchNotifier dispatchNotifier,
			ApplicationEventPublisher eventPublisher) {
		this.dispatchRepo = dispatchRepo;
		this.salesOrderRepo = salesOrderRepo;
		this.dispatchNotifier = dispatchNotifier;
		this.eventPublisher = eventPublisher;
	}

	@Transactional
	public StockDispatchCreatedData createFromOrder(StockDispatchFromOrderRequest req, Jwt jwt) {
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		if (req.lines() == null || req.lines().isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Cần ít nhất một dòng xuất kho.");
		}
		Map<String, String> errors = new LinkedHashMap<>();
		for (int i = 0; i < req.lines().size(); i++) {
			var line = req.lines().get(i);
			if (line.quantity() <= 0) {
				errors.put("lines[" + i + "].quantity", "Số lượng phải > 0");
			}
		}
		if (!errors.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ.", errors);
		}

		Set<Long> invSeen = new HashSet<>();
		for (var line : req.lines()) {
			if (!invSeen.add(line.inventoryId())) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST,
						"Không được trùng cùng một dòng tồn (inventory) trong phiếu.");
			}
		}

		var order = salesOrderRepo.lockOrderForUpdate(req.orderId())
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đơn hàng."));
		if (order.status() != null && order.status().equalsIgnoreCase("Cancelled")) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Đơn hàng đã hủy — không lập phiếu xuất.");
		}

		List<String> shortageLines = new ArrayList<>();
		for (var line : req.lines()) {
			var lockedInv = dispatchRepo.lockInventoryRowForUpdate(line.inventoryId())
					.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND,
							"Không tìm thấy dòng tồn kho id=" + line.inventoryId()));
			if (line.quantity() > lockedInv.quantity()) {
				int miss = line.quantity() - lockedInv.quantity();
				String pname = StringUtils.hasText(lockedInv.productName()) ? lockedInv.productName() : "—";
				String sku = StringUtils.hasText(lockedInv.skuCode()) ? lockedInv.skuCode() : "—";
				shortageLines.add(pname + " (" + sku + "): yêu cầu " + line.quantity() + ", tồn "
						+ lockedInv.quantity() + " (thiếu " + miss + ")");
			}
		}

		String initialStatus = shortageLines.isEmpty() ? "Pending" : "Partial";
		String tmpCode = "TMP-" + UUID.randomUUID().toString().replace("-", "");
		String notes = req.notes() == null ? "" : req.notes().trim();
		long dispatchId = dispatchRepo.insertDispatchHeader(tmpCode, Integer.valueOf(req.orderId()), userId,
				req.dispatchDate(), initialStatus, notes, null);

		for (var line : req.lines()) {
			dispatchRepo.insertDispatchLine(dispatchId, line.inventoryId(), line.quantity(), line.unitPriceSnapshot());
		}

		String finalCode = buildDispatchCode(dispatchId);
		dispatchRepo.updateDispatchCode(dispatchId, finalCode);

		String orderCode = salesOrderRepo.findOrderCode(req.orderId()).orElse("đơn #" + req.orderId());
		if (!shortageLines.isEmpty()) {
			eventPublisher.publishEvent(new StockDispatchShortageEvent(userId, dispatchId, finalCode, shortageLines));
		}
		else {
			eventPublisher.publishEvent(new OrderDispatchWaitingApprovalEvent(userId, dispatchId, orderCode));
		}

		return new StockDispatchCreatedData(dispatchId, finalCode, req.dispatchDate(), initialStatus, null);
	}

	private static String buildDispatchCode(long dispatchId) {
		int year = java.time.Year.now(java.time.ZoneId.systemDefault()).getValue();
		return "PX-" + year + "-" + String.format("%06d", dispatchId);
	}
}
