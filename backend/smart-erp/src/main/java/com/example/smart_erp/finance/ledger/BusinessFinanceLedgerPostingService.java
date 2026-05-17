package com.example.smart_erp.finance.ledger;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.ZoneId;

import org.springframework.stereotype.Service;

import com.example.smart_erp.sales.repository.SalesOrderJdbcRepository.OrderFinancialRow;

/**
 * Ghi sổ cái khi nghiệp vụ <strong>hoàn tất</strong> (cùng transaction với tầng gọi).
 * Thứ tự: cập nhật bảng nghiệp vụ trước → gọi service này sau.
 */
@Service
public class BusinessFinanceLedgerPostingService {

	private static final ZoneId LEDGER_DATE_ZONE = ZoneId.of("Asia/Ho_Chi_Minh");

	private final FinanceLedgerPostingJdbcRepository postingRepo;

	public BusinessFinanceLedgerPostingService(FinanceLedgerPostingJdbcRepository postingRepo) {
		this.postingRepo = postingRepo;
	}

	/** Phiếu nhập đã Approved — chi phí mua hàng (âm). */
	public void postStockReceiptPurchaseCostIfAbsent(LocalDate receiptDate, int receiptId, BigDecimal totalAmount,
			String receiptCode, int userId) {
		if (postingRepo.existsPosting("StockReceipt", receiptId, "PurchaseCost")) {
			return;
		}
		BigDecimal signed = totalAmount.negate();
		if (signed.signum() == 0) {
			return;
		}
		String desc = "Nhập kho " + receiptCode;
		postingRepo.insertPosting(receiptDate, "PurchaseCost", "StockReceipt", receiptId, signed, desc, userId);
	}

	/**
	 * Đơn bán buôn: ghi doanh thu khi <strong>Đã giao</strong> và <strong>Đã thanh toán</strong>.
	 */
	public void postWholesaleSalesRevenueIfComplete(OrderFinancialRow order, int userId) {
		if (order == null || !"Wholesale".equalsIgnoreCase(order.orderChannel())) {
			return;
		}
		if (!isOrderFinanciallyComplete(order)) {
			return;
		}
		if (postingRepo.existsPosting("SalesOrder", order.id(), "SalesRevenue")) {
			return;
		}
		BigDecimal fin = order.totalAmount().subtract(order.discountAmount()).max(BigDecimal.ZERO);
		if (fin.signum() <= 0) {
			return;
		}
		String code = order.orderCode() != null && !order.orderCode().isBlank() ? order.orderCode()
				: ("#" + order.id());
		LocalDate td = LocalDate.now(LEDGER_DATE_ZONE);
		postingRepo.insertPosting(td, "SalesRevenue", "SalesOrder", order.id(), fin, "Thu tiền bán buôn " + code, userId);
	}

	/** POS / bán lẻ: ghi doanh thu khi checkout hoàn tất và đã thanh toán. */
	public void postRetailSalesRevenueIfAbsent(OrderFinancialRow order, int userId) {
		if (order == null || !"Retail".equalsIgnoreCase(order.orderChannel())) {
			return;
		}
		if (!"Paid".equalsIgnoreCase(order.paymentStatus())) {
			return;
		}
		if (postingRepo.existsPosting("SalesOrder", order.id(), "SalesRevenue")) {
			return;
		}
		BigDecimal fin = order.totalAmount().subtract(order.discountAmount()).max(BigDecimal.ZERO);
		if (fin.signum() <= 0) {
			return;
		}
		String code = order.orderCode() != null && !order.orderCode().isBlank() ? order.orderCode()
				: ("#" + order.id());
		LocalDate td = LocalDate.now(LEDGER_DATE_ZONE);
		postingRepo.insertPosting(td, "SalesRevenue", "SalesOrder", order.id(), fin, "Doanh thu bán lẻ " + code, userId);
	}

	/** Đơn trả hàng — hoàn tiền (âm) khi đã thanh toán. */
	public void postReturnRefundIfComplete(OrderFinancialRow order, int userId) {
		if (order == null || !"Return".equalsIgnoreCase(order.orderChannel())) {
			return;
		}
		if (!"Paid".equalsIgnoreCase(order.paymentStatus())) {
			return;
		}
		if (postingRepo.existsPosting("SalesOrder", order.id(), "Refund")) {
			return;
		}
		BigDecimal fin = order.totalAmount().subtract(order.discountAmount()).max(BigDecimal.ZERO);
		if (fin.signum() <= 0) {
			return;
		}
		String code = order.orderCode() != null && !order.orderCode().isBlank() ? order.orderCode()
				: ("#" + order.id());
		LocalDate td = LocalDate.now(LEDGER_DATE_ZONE);
		postingRepo.insertPosting(td, "Refund", "SalesOrder", order.id(), fin.negate(), "Hoàn tiền đơn trả " + code,
				userId);
	}

	/** Huỷ bán lẻ — đảo doanh thu nếu đã ghi. */
	public void postRetailRefundIfAbsent(OrderFinancialRow order, int userId) {
		if (order == null || !"Retail".equalsIgnoreCase(order.orderChannel())) {
			return;
		}
		if (!postingRepo.existsPosting("SalesOrder", order.id(), "SalesRevenue")) {
			return;
		}
		if (postingRepo.existsPosting("SalesOrder", order.id(), "Refund")) {
			return;
		}
		BigDecimal fin = order.totalAmount().subtract(order.discountAmount()).max(BigDecimal.ZERO);
		if (fin.signum() <= 0) {
			return;
		}
		String code = order.orderCode() != null && !order.orderCode().isBlank() ? order.orderCode()
				: ("#" + order.id());
		LocalDate td = LocalDate.now(LEDGER_DATE_ZONE);
		postingRepo.insertPosting(td, "Refund", "SalesOrder", order.id(), fin.negate(), "Huỷ bán lẻ — đảo doanh thu " + code,
				userId);
	}

	public void tryPostOrderLedgerOnFinancialState(OrderFinancialRow order, int userId) {
		if (order == null) {
			return;
		}
		if ("Wholesale".equalsIgnoreCase(order.orderChannel())) {
			postWholesaleSalesRevenueIfComplete(order, userId);
		}
		else if ("Return".equalsIgnoreCase(order.orderChannel())) {
			postReturnRefundIfComplete(order, userId);
		}
		else if ("Retail".equalsIgnoreCase(order.orderChannel())) {
			postRetailSalesRevenueIfAbsent(order, userId);
		}
	}

	private static boolean isOrderFinanciallyComplete(OrderFinancialRow order) {
		return "Paid".equalsIgnoreCase(order.paymentStatus()) && "Delivered".equalsIgnoreCase(order.status());
	}
}
