package com.example.smart_erp.finance.ledger;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.time.LocalDate;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.example.smart_erp.sales.repository.SalesOrderJdbcRepository.OrderFinancialRow;

@ExtendWith(MockitoExtension.class)
class BusinessFinanceLedgerPostingServiceTest {

	@Mock
	private FinanceLedgerPostingJdbcRepository postingRepo;

	private BusinessFinanceLedgerPostingService service;

	@BeforeEach
	void setUp() {
		service = new BusinessFinanceLedgerPostingService(postingRepo);
	}

	@Test
	void postWholesaleRevenue_requiresPaidAndDelivered() {
		var pending = new OrderFinancialRow(1, "Wholesale", "SO-1", "Pending", "Paid", BigDecimal.TEN, BigDecimal.ZERO);
		service.postWholesaleSalesRevenueIfComplete(pending, 9);
		verify(postingRepo, never()).insertPosting(any(), any(), any(), any(Integer.class), any(), any(), any(Integer.class));

		var complete = new OrderFinancialRow(1, "Wholesale", "SO-1", "Delivered", "Paid", BigDecimal.TEN, BigDecimal.ZERO);
		when(postingRepo.existsPosting("SalesOrder", 1, "SalesRevenue")).thenReturn(false);
		service.postWholesaleSalesRevenueIfComplete(complete, 9);
		verify(postingRepo).insertPosting(any(LocalDate.class), eq("SalesRevenue"), eq("SalesOrder"), eq(1),
				eq(BigDecimal.TEN), any(), eq(9));
	}

	@Test
	void postStockReceiptPurchaseCost_isIdempotent() {
		when(postingRepo.existsPosting("StockReceipt", 5, "PurchaseCost")).thenReturn(true);
		service.postStockReceiptPurchaseCostIfAbsent(LocalDate.of(2026, 5, 16), 5, new BigDecimal("100"), "PN-1", 1);
		verify(postingRepo, never()).insertPosting(any(), any(), any(), any(Integer.class), any(), any(), any(Integer.class));
	}

	@Test
	void postRetailRevenue_skipsWhenUnpaid() {
		var unpaid = new OrderFinancialRow(2, "Retail", "SO-2", "Delivered", "Unpaid", BigDecimal.ONE, BigDecimal.ZERO);
		service.postRetailSalesRevenueIfAbsent(unpaid, 1);
		verify(postingRepo, never()).insertPosting(any(), any(), any(), any(Integer.class), any(), any(), any(Integer.class));
	}
}
