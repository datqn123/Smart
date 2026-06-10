package com.example.smart_erp.inventory.repository;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.sql.ResultSet;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.Mockito;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

import com.example.smart_erp.inventory.query.InventoryListQuery;
import com.example.smart_erp.inventory.query.InventoryListSortOrder;
import com.example.smart_erp.inventory.query.InventoryStockLevel;
import com.example.smart_erp.inventory.response.InventorySummaryData;

class InventoryListJdbcRepositoryTest {

	private final NamedParameterJdbcTemplate jdbc = Mockito.mock(NamedParameterJdbcTemplate.class);

	private final InventoryListJdbcRepository repo = new InventoryListJdbcRepository(jdbc);

	private static InventoryListQuery emptyQuery() {
		return new InventoryListQuery(null, InventoryStockLevel.ALL, null, null, null, 1, 20,
				InventoryListSortOrder.parseOrDefault(null));
	}

	private static InventoryListQuery queryWithFilters() {
		return new InventoryListQuery("foo", InventoryStockLevel.LOW_STOCK, 7, 2, null, 1, 20,
				InventoryListSortOrder.parseOrDefault(null));
	}

	private static ResultSet mockRs(Map<String, Object> values) throws java.sql.SQLException {
		ResultSet rs = Mockito.mock(ResultSet.class);
		for (var e : values.entrySet()) {
			Object v = e.getValue();
			if (v == null) {
				Mockito.when(rs.getObject(e.getKey())).thenReturn(null);
			}
			else if (v instanceof Long lv) {
				Mockito.when(rs.getLong(e.getKey())).thenReturn(lv);
			}
			else if (v instanceof BigDecimal bd) {
				Mockito.when(rs.getBigDecimal(e.getKey())).thenReturn(bd);
			}
			else if (v instanceof Integer iv) {
				Mockito.when(rs.getInt(e.getKey())).thenReturn(iv);
			}
			else if (v instanceof String sv) {
				Mockito.when(rs.getString(e.getKey())).thenReturn(sv);
			}
			else {
				Mockito.when(rs.getObject(e.getKey())).thenReturn(v);
			}
		}
		return rs;
	}

	@Test
	@SuppressWarnings("unchecked")
	void loadSummaryWithCount_returnsSummaryAndTotalFromSingleQuery() throws Exception {
		InventoryListQuery q = emptyQuery();
		Map<String, Object> values = Map.of(
				"total_rows", 42L,
				"total_skus", 42L,
				"total_value", new BigDecimal("12345.67"),
				"low_stock_count", 3L,
				"expiring_soon_count", 1L);
		ResultSet rs = mockRs(values);
		Mockito.when(jdbc.queryForObject(Mockito.anyString(),
				Mockito.any(MapSqlParameterSource.class),
				Mockito.<RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount>>any()))
				.thenAnswer(inv -> {
					RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount> m = inv.getArgument(2);
					return m.mapRow(rs, 1);
				});

		InventoryListJdbcRepository.InventorySummaryWithCount result = repo.loadSummaryWithCount(q);

		assertThat(result.total()).isEqualTo(42L);
		InventorySummaryData summary = result.summary();
		assertThat(summary.totalSkus()).isEqualTo(42L);
		assertThat(summary.totalValue()).isEqualByComparingTo("12345.67");
		assertThat(summary.lowStockCount()).isEqualTo(3L);
		assertThat(summary.expiringSoonCount()).isEqualTo(1L);

		ArgumentCaptor<String> sql = ArgumentCaptor.forClass(String.class);
		ArgumentCaptor<MapSqlParameterSource> params = ArgumentCaptor.forClass(MapSqlParameterSource.class);
		verify(jdbc, times(1)).queryForObject(sql.capture(), params.capture(),
				Mockito.<RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount>>any());
		String captured = sql.getValue();
		assertThat(captured).contains("total_rows");
		assertThat(captured).contains("total_skus");
		assertThat(captured).contains("total_value");
		assertThat(captured).contains("low_stock_count");
		assertThat(captured).contains("expiring_soon_count");
		assertThat(captured).contains("inventory i");
		assertThat(captured).contains("FROM");
		assertThat(captured.indexOf("COUNT(*)::bigint AS total_rows"))
				.isLessThan(captured.indexOf("FROM"));
		String outerSql = captured.substring(0, captured.indexOf("LEFT JOIN LATERAL"));
		assertThat(outerSql).doesNotContain("ORDER BY");
		assertThat(outerSql).doesNotContain("LIMIT");
		assertThat(outerSql).doesNotContain("OFFSET");
	}

	@Test
	@SuppressWarnings("unchecked")
	void loadSummaryWithCount_handlesEmptyResultWithZeros() throws Exception {
		InventoryListQuery q = emptyQuery();
		Map<String, Object> values = Map.of(
				"total_rows", 0L,
				"total_skus", 0L,
				"total_value", BigDecimal.ZERO,
				"low_stock_count", 0L,
				"expiring_soon_count", 0L);
		ResultSet rs = mockRs(values);
		Mockito.when(jdbc.queryForObject(Mockito.anyString(),
				Mockito.any(MapSqlParameterSource.class),
				Mockito.<RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount>>any()))
				.thenAnswer(inv -> {
					RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount> m = inv.getArgument(2);
					return m.mapRow(rs, 1);
				});

		InventoryListJdbcRepository.InventorySummaryWithCount result = repo.loadSummaryWithCount(q);

		assertThat(result.total()).isZero();
		assertThat(result.summary().totalSkus()).isZero();
		assertThat(result.summary().totalValue()).isEqualByComparingTo("0");
		assertThat(result.summary().lowStockCount()).isZero();
		assertThat(result.summary().expiringSoonCount()).isZero();
	}

	@Test
	@SuppressWarnings("unchecked")
	void loadSummaryWithCount_appliesFilterConditionsFromQuery() throws Exception {
		InventoryListQuery q = queryWithFilters();
		ResultSet rs = mockRs(Map.of(
				"total_rows", 5L,
				"total_skus", 5L,
				"total_value", BigDecimal.valueOf(100),
				"low_stock_count", 5L,
				"expiring_soon_count", 0L));
		Mockito.when(jdbc.queryForObject(Mockito.anyString(),
				Mockito.any(MapSqlParameterSource.class),
				Mockito.<RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount>>any()))
				.thenAnswer(inv -> {
					RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount> m = inv.getArgument(2);
					return m.mapRow(rs, 1);
				});

		repo.loadSummaryWithCount(q);

		ArgumentCaptor<String> sql = ArgumentCaptor.forClass(String.class);
		ArgumentCaptor<MapSqlParameterSource> params = ArgumentCaptor.forClass(MapSqlParameterSource.class);
		verify(jdbc).queryForObject(sql.capture(), params.capture(),
				Mockito.<RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount>>any());
		String capturedSql = sql.getValue();
		assertThat(capturedSql).contains("i.quantity > 0 AND i.quantity <= i.min_quantity");
		assertThat(capturedSql).contains("i.location_id = :_location_id");
		assertThat(capturedSql).contains("p.category_id = :_category_id");
		assertThat(capturedSql).contains("(p.name ilike :_search OR p.sku_code ilike :_search)");
		Map<String, Object> p = params.getValue().getValues();
		assertThat(p).containsEntry("_location_id", 7);
		assertThat(p).containsEntry("_category_id", 2);
		assertThat(p.get("_search")).isEqualTo("%foo%");
	}

	@Test
	@SuppressWarnings("unchecked")
	void loadSummaryWithCount_matchesSeparateLoadSummaryAndCountRows() throws Exception {
		InventoryListQuery q = emptyQuery();
		Map<String, Object> summaryValues = Map.of(
				"total_skus", 7L,
				"total_value", new BigDecimal("500.50"),
				"low_stock_count", 2L,
				"expiring_soon_count", 1L);
		ResultSet summaryRs = mockRs(summaryValues);
		ResultSet countRs = mockRs(Map.of());
		Mockito.when(countRs.getLong(1)).thenReturn(7L);

		Mockito.when(jdbc.queryForObject(Mockito.anyString(),
				Mockito.any(MapSqlParameterSource.class),
				Mockito.<RowMapper<InventorySummaryData>>any()))
				.thenAnswer(inv -> {
					RowMapper<InventorySummaryData> m = inv.getArgument(2);
					return m.mapRow(summaryRs, 1);
				});
		Mockito.when(jdbc.queryForObject(Mockito.anyString(),
				Mockito.any(MapSqlParameterSource.class),
				eq(Long.class)))
				.thenReturn(7L);

		InventorySummaryData separateSummary = repo.loadSummary(q);
		long separateCount = repo.countRows(q);

		ResultSet combinedRs = mockRs(Map.of(
				"total_rows", 7L,
				"total_skus", 7L,
				"total_value", new BigDecimal("500.50"),
				"low_stock_count", 2L,
				"expiring_soon_count", 1L));
		Mockito.when(jdbc.queryForObject(Mockito.anyString(),
				Mockito.any(MapSqlParameterSource.class),
				Mockito.<RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount>>any()))
				.thenAnswer(inv -> {
					RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount> m = inv.getArgument(2);
					return m.mapRow(combinedRs, 1);
				});

		InventoryListJdbcRepository.InventorySummaryWithCount combined = repo.loadSummaryWithCount(q);

		assertThat(combined.total()).isEqualTo(separateCount);
		assertThat(combined.summary().totalSkus()).isEqualTo(separateSummary.totalSkus());
		assertThat(combined.summary().totalValue()).isEqualByComparingTo(separateSummary.totalValue());
		assertThat(combined.summary().lowStockCount()).isEqualTo(separateSummary.lowStockCount());
		assertThat(combined.summary().expiringSoonCount()).isEqualTo(separateSummary.expiringSoonCount());
	}

	@Test
	void loadSummaryWithCount_doesNotExecuteMoreThanOneQuery() {
		InventoryListQuery q = emptyQuery();
		Mockito.when(jdbc.queryForObject(Mockito.anyString(),
				Mockito.any(MapSqlParameterSource.class),
				Mockito.<RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount>>any()))
				.thenReturn(new InventoryListJdbcRepository.InventorySummaryWithCount(
						new InventorySummaryData(0L, BigDecimal.ZERO, 0L, 0L), 0L));

		repo.loadSummaryWithCount(q);

		verify(jdbc, times(1)).queryForObject(Mockito.anyString(),
				Mockito.any(MapSqlParameterSource.class),
				Mockito.<RowMapper<InventoryListJdbcRepository.InventorySummaryWithCount>>any());
		verify(jdbc, Mockito.never()).query(Mockito.anyString(),
				Mockito.any(MapSqlParameterSource.class), Mockito.any(RowMapper.class));
	}

	@Test
	void existing_loadSummary_and_countRows_stillWork() {
		Mockito.when(jdbc.queryForObject(Mockito.anyString(),
				Mockito.any(MapSqlParameterSource.class),
				Mockito.<RowMapper<InventorySummaryData>>any()))
				.thenReturn(new InventorySummaryData(1L, BigDecimal.ONE, 0L, 0L));
		Mockito.when(jdbc.queryForObject(Mockito.anyString(),
				Mockito.any(MapSqlParameterSource.class),
				eq(Long.class)))
				.thenReturn(1L);

		InventorySummaryData s = repo.loadSummary(emptyQuery());
		long c = repo.countRows(emptyQuery());

		assertThat(s.totalSkus()).isEqualTo(1L);
		assertThat(c).isEqualTo(1L);
	}
}
