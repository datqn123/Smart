package com.example.smart_erp.inventory.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import com.example.smart_erp.inventory.query.InventoryListQuery;
import com.example.smart_erp.inventory.query.InventoryListSortOrder;
import com.example.smart_erp.inventory.query.InventoryStockLevel;
import com.example.smart_erp.inventory.repository.InventoryListJdbcRepository;
import com.example.smart_erp.inventory.repository.InventoryListJdbcRepository.InventoryListRow;
import com.example.smart_erp.inventory.repository.InventoryListJdbcRepository.InventorySummaryWithCount;
import com.example.smart_erp.inventory.response.InventoryListItemData;
import com.example.smart_erp.inventory.response.InventoryListPageData;
import com.example.smart_erp.inventory.response.InventorySummaryData;

class InventoryListServiceTest {

	private final InventoryListJdbcRepository repo = Mockito.mock(InventoryListJdbcRepository.class);

	private final InventoryListService service = new InventoryListService(repo);

	private static InventoryListQuery sampleQuery() {
		return new InventoryListQuery("p", InventoryStockLevel.ALL, null, null, null, 1, 20,
				InventoryListSortOrder.parseOrDefault(null));
	}

	private static InventoryListRow sampleRow() {
		return new InventoryListRow(
				1L, 10L, "P", "SKU", null, 1, "W", "A", null, null, 5, 1, 1, "u",
				BigDecimal.ONE,
				Instant.parse("2026-01-01T00:00:00Z"));
	}

	@Test
	void list_usesCombinedSummaryWithCountInsteadOfSeparateCalls() {
		InventoryListQuery q = sampleQuery();
		InventorySummaryWithCount sc = new InventorySummaryWithCount(
				new InventorySummaryData(7L, BigDecimal.valueOf(500), 2L, 1L), 7L);
		when(repo.loadSummaryWithCount(q)).thenReturn(sc);
		when(repo.loadPage(q)).thenReturn(List.of(sampleRow()));

		InventoryListPageData result = service.list(q);

		assertThat(result.summary().totalSkus()).isEqualTo(7L);
		assertThat(result.summary().totalValue()).isEqualByComparingTo("500");
		assertThat(result.summary().lowStockCount()).isEqualTo(2L);
		assertThat(result.summary().expiringSoonCount()).isEqualTo(1L);
		assertThat(result.total()).isEqualTo(7L);
		assertThat(result.items()).hasSize(1);
		InventoryListItemData item = result.items().get(0);
		assertThat(item.productName()).isEqualTo("P");
		assertThat(item.quantity()).isEqualTo(5);

		verify(repo, times(1)).loadSummaryWithCount(q);
		verify(repo, never()).loadSummary(any(InventoryListQuery.class));
		verify(repo, never()).countRows(any(InventoryListQuery.class));
		verify(repo, times(1)).loadPage(q);
	}

	@Test
	void list_marksLowStockAndExpiringRowsBasedOnReturnedData() {
		InventoryListQuery q = sampleQuery();
		LocalDate today = LocalDate.now(java.time.ZoneOffset.UTC);
		LocalDate expiring = today.plusDays(15);
		InventoryListRow lowRow = new InventoryListRow(
				2L, 20L, "Low", "SKU2", null, 1, "W", "A", null, null, 1, 5, 1, "u",
				BigDecimal.ONE, Instant.parse("2026-01-01T00:00:00Z"));
		InventoryListRow expiringRow = new InventoryListRow(
				3L, 30L, "Exp", "SKU3", null, 1, "W", "A", null, expiring, 4, 1, 1, "u",
				BigDecimal.ONE, Instant.parse("2026-01-01T00:00:00Z"));
		when(repo.loadSummaryWithCount(q)).thenReturn(new InventorySummaryWithCount(
				new InventorySummaryData(2L, BigDecimal.valueOf(20), 1L, 1L), 2L));
		when(repo.loadPage(q)).thenReturn(List.of(lowRow, expiringRow));

		InventoryListPageData result = service.list(q);

		assertThat(result.items()).hasSize(2);
		assertThat(result.items().get(0).isLowStock()).isTrue();
		assertThat(result.items().get(0).isExpiringSoon()).isFalse();
		assertThat(result.items().get(1).isLowStock()).isFalse();
		assertThat(result.items().get(1).isExpiringSoon()).isTrue();
	}

	@Test
	void list_emptyResult_hasZeroItemsAndZeroTotal() {
		InventoryListQuery q = sampleQuery();
		when(repo.loadSummaryWithCount(q)).thenReturn(new InventorySummaryWithCount(
				new InventorySummaryData(0L, BigDecimal.ZERO, 0L, 0L), 0L));
		when(repo.loadPage(q)).thenReturn(List.of());

		InventoryListPageData result = service.list(q);

		assertThat(result.items()).isEmpty();
		assertThat(result.total()).isZero();
		assertThat(result.summary().totalSkus()).isZero();
		verify(repo, times(1)).loadSummaryWithCount(q);
		verify(repo, never()).loadSummary(any(InventoryListQuery.class));
		verify(repo, never()).countRows(any(InventoryListQuery.class));
	}

	@Test
	void list_passesPageAndLimitToResponse() {
		InventoryListQuery q = new InventoryListQuery(null, InventoryStockLevel.ALL, null, null, null, 3, 50,
				InventoryListSortOrder.parseOrDefault(null));
		when(repo.loadSummaryWithCount(q)).thenReturn(new InventorySummaryWithCount(
				new InventorySummaryData(0L, BigDecimal.ZERO, 0L, 0L), 0L));
		when(repo.loadPage(q)).thenReturn(List.of());

		InventoryListPageData result = service.list(q);

		assertThat(result.page()).isEqualTo(3);
		assertThat(result.limit()).isEqualTo(50);
	}

	@Test
	void summary_stillUsesLoadSummary_alone() {
		InventoryListQuery q = sampleQuery();
		when(repo.loadSummary(q)).thenReturn(new InventorySummaryData(9L, BigDecimal.valueOf(100), 1L, 0L));

		var result = service.summary(q);

		assertThat(result.totalSkus()).isEqualTo(9L);
		verify(repo, times(1)).loadSummary(q);
		verify(repo, never()).loadSummaryWithCount(any(InventoryListQuery.class));
	}
}
