package com.example.smart_erp.catalog.repository;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ProductJdbcRepositoryTest {

	@Mock
	private NamedParameterJdbcTemplate namedJdbc;

	/**
	 * Stub cho 3-arg query(String, Map, RowMapper) — overload mà production code sử dụng (Map.of("ids", ...) →
	 * {@code Map<String, ?>}).
	 */
	@SuppressWarnings("unchecked")
	private <T> void stubQuery(List<T> returnValue) {
		lenient().doReturn(returnValue).when(namedJdbc).query(anyString(), anyMap(), any(RowMapper.class));
	}

	@Test
	void findExistingProductIds_returnsEmptySetWhenInputEmpty() {
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);

		assertThat(repo.findExistingProductIds(List.of())).isEmpty();
		assertThat(repo.findExistingProductIds(null)).isEmpty();

		verifyNoInteractions(namedJdbc);
	}

	@Test
	void findExistingProductIds_returnsAllExistingIds() {
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<Integer> input = List.of(10, 20, 30);
		stubQuery(List.of(10, 20, 30));

		Set<Integer> result = repo.findExistingProductIds(input);

		assertThat(result).containsExactlyInAnyOrder(10, 20, 30);
	}

	@Test
	void findExistingProductIds_returnsSubsetWhenSomeIdsMissing() {
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<Integer> input = List.of(10, 20, 30);
		stubQuery(List.of(10, 30));

		Set<Integer> result = repo.findExistingProductIds(input);

		assertThat(result).containsExactlyInAnyOrder(10, 30);
		assertThat(result).hasSize(2);
	}

	@Test
	void findExistingProductIds_returnsEmptySetWhenNoneExist() {
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<Integer> input = List.of(10, 20);
		stubQuery(List.of());

		Set<Integer> result = repo.findExistingProductIds(input);

		assertThat(result).isEmpty();
	}

	@Test
	void findExistingProductIds_singleId() {
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		stubQuery(List.of(42));

		Set<Integer> result = repo.findExistingProductIds(List.of(42));

		assertThat(result).containsExactly(42);
	}

	@Test
	@SuppressWarnings("unchecked")
	void findExistingProductIds_passesListOfIdsAsParam() {
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<Integer> input = List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
		stubQuery(List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10));

		repo.findExistingProductIds(input);

		ArgumentCaptor<String> sqlCap = ArgumentCaptor.forClass(String.class);
		ArgumentCaptor<Map<String, Object>> paramCap = ArgumentCaptor.forClass(Map.class);
		verify(namedJdbc, times(1)).query(sqlCap.capture(), paramCap.capture(), any(RowMapper.class));
		assertThat(sqlCap.getValue()).contains("SELECT id FROM products WHERE id IN (:ids)");
		Map<String, Object> params = paramCap.getValue();
		assertThat((List<Integer>) params.get("ids")).containsExactlyElementsOf(input);
	}

	@Test
	void findBulkDeleteBlockReasons_returnsEmptyMapWhenInputEmpty() {
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);

		assertThat(repo.findBulkDeleteBlockReasons(List.of())).isEmpty();
		assertThat(repo.findBulkDeleteBlockReasons(null)).isEmpty();

		verifyNoInteractions(namedJdbc);
	}

	@Test
	@SuppressWarnings("unchecked")
	void findBulkDeleteBlockReasons_returnsEmptyMapWhenAllClean() {
		// Khi không có id nào bị block → repo trả empty map
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<Integer> input = List.of(1, 2, 3);
		stubQuery(List.of()); // mock trả list rỗng → map rỗng

		Map<Integer, String> result = repo.findBulkDeleteBlockReasons(input);

		assertThat(result).isEmpty();
	}

	@Test
	@SuppressWarnings("unchecked")
	void findBulkDeleteBlockReasons_passesIdsAsIntegerArrayForUnnest() {
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<Integer> input = List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
		stubQuery(List.of());

		repo.findBulkDeleteBlockReasons(input);

		ArgumentCaptor<String> sqlCap = ArgumentCaptor.forClass(String.class);
		ArgumentCaptor<Map<String, Object>> paramCap = ArgumentCaptor.forClass(Map.class);
		verify(namedJdbc, times(1)).query(sqlCap.capture(), paramCap.capture(), any(RowMapper.class));
		String sql = sqlCap.getValue();
		assertThat(sql).contains("unnest(:ids)");
		assertThat(sql).contains("stockreceiptdetails");
		assertThat(sql).contains("orderdetails");
		assertThat(sql).contains("inventory");
		Map<String, Object> params = paramCap.getValue();
		Object value = params.get("ids");
		// Phải là mảng Integer[] (không phải List) cho unnest(:ids) của PostgreSQL
		assertThat(value).isInstanceOf(Integer[].class);
		Integer[] arr = (Integer[]) value;
		assertThat(arr).containsExactly(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
	}

	@Test
	@SuppressWarnings("unchecked")
	void findBulkDeleteBlockReasons_sqlContainsPriorityOrder() {
		// SQL CASE WHEN phải ưu tiên: HAS_STOCK_RECEIPT > HAS_ORDER_LINES > HAS_STOCK (giữ nguyên thứ tự cũ)
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		stubQuery(List.of());

		repo.findBulkDeleteBlockReasons(List.of(1));

		ArgumentCaptor<String> sqlCap = ArgumentCaptor.forClass(String.class);
		verify(namedJdbc).query(sqlCap.capture(), anyMap(), any(RowMapper.class));
		String sql = sqlCap.getValue();
		int posStockReceipt = sql.indexOf("'HAS_STOCK_RECEIPT'");
		int posOrderLines = sql.indexOf("'HAS_ORDER_LINES'");
		int posStock = sql.indexOf("'HAS_STOCK'");
		assertThat(posStockReceipt).isPositive();
		assertThat(posOrderLines).isPositive();
		assertThat(posStock).isPositive();
		// Thứ tự ưu tiên trong CASE WHEN
		assertThat(posStockReceipt).isLessThan(posOrderLines);
		assertThat(posOrderLines).isLessThan(posStock);
	}

	@Test
	void findExistingProductIds_dedupesByHashSetSemantics() {
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		stubQuery(List.of(1, 1, 2));

		Set<Integer> result = repo.findExistingProductIds(List.of(1, 2));

		assertThat(result).hasSize(2);
		assertThat(new HashSet<>(result)).containsExactlyInAnyOrder(1, 2);
	}

	@Test
	@SuppressWarnings("unchecked")
	void findBulkDeleteBlockReasons_isCalledExactlyOncePerBulk() {
		// Đảm bảo batch: 1 query duy nhất cho N ids (không phải N query)
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		stubQuery(List.of());

		repo.findBulkDeleteBlockReasons(List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15));

		verify(namedJdbc, times(1)).query(anyString(), anyMap(), any(RowMapper.class));
	}

	@Test
	@SuppressWarnings("unchecked")
	void findExistingProductIds_isCalledExactlyOncePerBulk() {
		// Đảm bảo batch: 1 query duy nhất cho N ids (không phải N query)
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		stubQuery(List.of());

		repo.findExistingProductIds(List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15));

		verify(namedJdbc, times(1)).query(eq("SELECT id FROM products WHERE id IN (:ids)"), anyMap(),
				any(RowMapper.class));
	}

	@Test
	@SuppressWarnings("unchecked")
	void findBulkDeleteBlockReasons_emptyResultIsConvertedToEmptyMap() {
		// SQL có thể trả về rows với block_reason = NULL → repo chỉ thêm vào map khi reason != null
		// Khi list rỗng, kết quả phải là map rỗng
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		stubQuery(List.of());

		Map<Integer, String> result = repo.findBulkDeleteBlockReasons(List.of(1, 2));

		assertThat(result).isEmpty();
		assertThat(result).isNotNull();
	}

	@Test
	@SuppressWarnings("unchecked")
	void findExistingProductIds_doesNotQueryWhenInputIsEmpty() {
		// Edge case: empty input → không gọi DB
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);

		Set<Integer> result = repo.findExistingProductIds(List.of());

		assertThat(result).isEmpty();
		verifyNoInteractions(namedJdbc);
	}

	@Test
	@SuppressWarnings("unchecked")
	void findBulkDeleteBlockReasons_doesNotQueryWhenInputIsEmpty() {
		// Edge case: empty input → không gọi DB
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);

		Map<Integer, String> result = repo.findBulkDeleteBlockReasons(List.of());

		assertThat(result).isEmpty();
		verifyNoInteractions(namedJdbc);
	}

	@Test
	void stubExample_compilesAndRuns() {
		// sanity check: stubQuery + when combo (giữ import khi cần)
		when(namedJdbc.query(anyString(), anyMap(), any(RowMapper.class))).thenReturn(List.of(1));
		assertThat(namedJdbc.query("x", Map.of(), org.mockito.Mockito.mock(RowMapper.class))).containsExactly(1);
	}

	// ============== lockProductsForUpdateBatch tests ==============

	@Test
	void lockProductsForUpdateBatch_returnsEmptyListWhenInputEmpty() {
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);

		assertThat(repo.lockProductsForUpdateBatch(List.of())).isEmpty();
		assertThat(repo.lockProductsForUpdateBatch(null)).isEmpty();

		verifyNoInteractions(namedJdbc);
	}

	@Test
	@SuppressWarnings("unchecked")
	void lockProductsForUpdateBatch_executesSingleBatchQuery() {
		// I1: 1 query thay vì N lần per-row
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<ProductJdbcRepository.ProductLockSnapshot> snapshots = List.of(
				new ProductJdbcRepository.ProductLockSnapshot(1, "SKU1", null, "P1", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(2, "SKU2", null, "P2", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(3, "SKU3", null, "P3", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(4, "SKU4", null, "P4", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(5, "SKU5", null, "P5", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(6, "SKU6", null, "P6", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(7, "SKU7", null, "P7", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(8, "SKU8", null, "P8", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(9, "SKU9", null, "P9", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(10, "SKU10", null, "P10", null, null, null, "active", null));
		stubQuery(snapshots);

		repo.lockProductsForUpdateBatch(List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10));

		verify(namedJdbc, times(1)).query(anyString(), anyMap(), any(RowMapper.class));
	}

	@Test
	@SuppressWarnings("unchecked")
	void lockProductsForUpdateBatch_sqlUsesInClauseWithOrderByForUpdate() {
		// I1: SQL phải dùng IN(:ids) + ORDER BY id + FOR UPDATE để tránh deadlock
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<ProductJdbcRepository.ProductLockSnapshot> snapshots = List.of(
				new ProductJdbcRepository.ProductLockSnapshot(1, "SKU1", null, "P1", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(2, "SKU2", null, "P2", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(3, "SKU3", null, "P3", null, null, null, "active", null));
		stubQuery(snapshots);

		repo.lockProductsForUpdateBatch(List.of(1, 2, 3));

		ArgumentCaptor<String> sqlCap = ArgumentCaptor.forClass(String.class);
		verify(namedJdbc).query(sqlCap.capture(), anyMap(), any(RowMapper.class));
		String sql = sqlCap.getValue();
		assertThat(sql).contains("FROM products p WHERE p.id IN (:ids)");
		assertThat(sql).contains("ORDER BY p.id");
		assertThat(sql).contains("FOR UPDATE");
	}

	@Test
	@SuppressWarnings("unchecked")
	void lockProductsForUpdateBatch_passesIdsAsIntegerArray() {
		// I1: ids phải truyền dưới dạng Integer[] cho NamedParameterJdbcTemplate với IN(:ids)
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<Integer> input = List.of(10, 20, 30, 40, 50);
		List<ProductJdbcRepository.ProductLockSnapshot> snapshots = List.of(
				new ProductJdbcRepository.ProductLockSnapshot(10, "SKU10", null, "P10", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(20, "SKU20", null, "P20", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(30, "SKU30", null, "P30", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(40, "SKU40", null, "P40", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(50, "SKU50", null, "P50", null, null, null, "active", null));
		stubQuery(snapshots);

		repo.lockProductsForUpdateBatch(input);

		ArgumentCaptor<Map<String, Object>> paramCap = ArgumentCaptor.forClass(Map.class);
		verify(namedJdbc).query(anyString(), paramCap.capture(), any(RowMapper.class));
		Object value = paramCap.getValue().get("ids");
		assertThat(value).isInstanceOf(Integer[].class);
		assertThat((Integer[]) value).containsExactly(10, 20, 30, 40, 50);
	}

	@Test
	@SuppressWarnings("unchecked")
	void lockProductsForUpdateBatch_returnsAllSnapshotsWhenAllExist() {
		// Happy path: tất cả ids tồn tại → trả về list snapshot
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<ProductJdbcRepository.ProductLockSnapshot> snapshots = List.of(
				new ProductJdbcRepository.ProductLockSnapshot(1, "SKU1", null, "P1", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(2, "SKU2", null, "P2", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(3, "SKU3", null, "P3", null, null, null, "active", null));
		stubQuery(snapshots);

		List<ProductJdbcRepository.ProductLockSnapshot> result = repo.lockProductsForUpdateBatch(List.of(1, 2, 3));

		assertThat(result).hasSize(3);
	}

	@Test
	@SuppressWarnings("unchecked")
	void lockProductsForUpdateBatch_throwsBusinessExceptionConflictOnToctou() {
		// I3: Khi số row trả về < số id đầu vào (TOCTOU race) → throw BusinessException(CONFLICT)
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		// DB chỉ trả về 2 rows (id 1 và 3), id 2 đã bị xóa bởi transaction khác
		List<ProductJdbcRepository.ProductLockSnapshot> snapshots = List.of(
				new ProductJdbcRepository.ProductLockSnapshot(1, "SKU1", null, "P1", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(3, "SKU3", null, "P3", null, null, null, "active", null));
		stubQuery(snapshots);

		assertThatThrownBy(() -> repo.lockProductsForUpdateBatch(List.of(1, 2, 3)))
				.isInstanceOfSatisfying(BusinessException.class, ex -> {
					assertThat(ex.getCode()).isEqualTo(ApiErrorCode.CONFLICT);
					assertThat(ex.getMessage()).contains("Sản phẩm đã bị xóa bởi người dùng khác");
					assertThat(ex.getDetails()).containsEntry("id", "2");
				});
	}

	@Test
	@SuppressWarnings("unchecked")
	void lockProductsForUpdateBatch_throwsWhenAllIdsMissing() {
		// Edge case: tất cả ids đều biến mất → vẫn throw BusinessException(CONFLICT) với id đầu tiên
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		stubQuery(List.of());

		assertThatThrownBy(() -> repo.lockProductsForUpdateBatch(List.of(5, 6, 7)))
				.isInstanceOfSatisfying(BusinessException.class, ex -> {
					assertThat(ex.getCode()).isEqualTo(ApiErrorCode.CONFLICT);
					assertThat(ex.getDetails()).containsKey("id");
				});
	}

	@Test
	@SuppressWarnings("unchecked")
	void lockProductsForUpdateBatch_noThrowWhenAllIdsMatch() {
		// Không throw khi số row == số ids
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<ProductJdbcRepository.ProductLockSnapshot> snapshots = List.of(
				new ProductJdbcRepository.ProductLockSnapshot(1, "SKU1", null, "P1", null, null, null, "active", null),
				new ProductJdbcRepository.ProductLockSnapshot(2, "SKU2", null, "P2", null, null, null, "active", null));
		stubQuery(snapshots);

		// Should not throw
		List<ProductJdbcRepository.ProductLockSnapshot> result = repo.lockProductsForUpdateBatch(List.of(1, 2));
		assertThat(result).hasSize(2);
	}

	@Test
	@SuppressWarnings("unchecked")
	void lockProductsForUpdate_delegatesToBatch() {
		// Đảm bảo lockProductsForUpdate (plural) vẫn hoạt động và delegate xuống batch method
		ProductJdbcRepository repo = new ProductJdbcRepository(namedJdbc);
		List<ProductJdbcRepository.ProductLockSnapshot> snapshots = List.of(
				new ProductJdbcRepository.ProductLockSnapshot(1, "SKU1", null, "P1", null, null, null, "active", null));
		stubQuery(snapshots);

		// Should not throw — batch trả về 1 row cho 1 id
		repo.lockProductsForUpdate(List.of(1));
		verify(namedJdbc, times(1)).query(anyString(), anyMap(), any(RowMapper.class));
	}
}
