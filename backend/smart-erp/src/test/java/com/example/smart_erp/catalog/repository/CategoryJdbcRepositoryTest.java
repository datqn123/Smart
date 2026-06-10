package com.example.smart_erp.catalog.repository;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class CategoryJdbcRepositoryTest {

	@Mock
	private NamedParameterJdbcTemplate namedJdbc;

	private void stubQueryForBoolean(boolean returnValue) {
		lenient().when(namedJdbc.queryForObject(anyString(), anyMap(), eq(Boolean.class))).thenReturn(returnValue);
	}

	@Test
	void wouldCreateCycle_returnsTrueWhenNewParentIsDirectChild() {
		// A -> B (B là con trực tiếp của A). Set A.parentId = B → tạo cycle
		CategoryJdbcRepository repo = new CategoryJdbcRepository(namedJdbc);
		stubQueryForBoolean(true);

		boolean result = repo.wouldCreateCycle(1L, 2L);

		assertThat(result).isTrue();
		verify(namedJdbc, times(1)).queryForObject(anyString(), anyMap(), eq(Boolean.class));
	}

	@Test
	void wouldCreateCycle_returnsTrueWhenNewParentIsDeepDescendant() {
		// A -> B -> C. Set A.parentId = C → tạo cycle (gián tiếp)
		CategoryJdbcRepository repo = new CategoryJdbcRepository(namedJdbc);
		stubQueryForBoolean(true);

		boolean result = repo.wouldCreateCycle(1L, 3L);

		assertThat(result).isTrue();
	}

	@Test
	void wouldCreateCycle_returnsFalseWhenNewParentNotInSubtree() {
		// A -> B, X là node khác không liên quan. Set A.parentId = X → OK
		CategoryJdbcRepository repo = new CategoryJdbcRepository(namedJdbc);
		stubQueryForBoolean(false);

		boolean result = repo.wouldCreateCycle(1L, 99L);

		assertThat(result).isFalse();
	}

	@Test
	void wouldCreateCycle_returnsFalseWhenCategoryIsLeaf() {
		// A là leaf, không có descendant. Set A.parentId = B → OK
		CategoryJdbcRepository repo = new CategoryJdbcRepository(namedJdbc);
		stubQueryForBoolean(false);

		boolean result = repo.wouldCreateCycle(1L, 2L);

		assertThat(result).isFalse();
	}

	@Test
	void wouldCreateCycle_returnsFalseWhenDbReturnsNull() {
		// Edge case: queryForObject trả null (defensive) → coi như không tạo cycle
		CategoryJdbcRepository repo = new CategoryJdbcRepository(namedJdbc);
		when(namedJdbc.queryForObject(anyString(), anyMap(), eq(Boolean.class))).thenReturn(null);

		boolean result = repo.wouldCreateCycle(1L, 2L);

		assertThat(result).isFalse();
	}

	@Test
	void wouldCreateCycle_usesRecursiveCteWithDepthLimit() {
		// Verify SQL dùng WITH RECURSIVE, có depth limit (defense in depth chống infinite loop)
		CategoryJdbcRepository repo = new CategoryJdbcRepository(namedJdbc);
		stubQueryForBoolean(false);

		repo.wouldCreateCycle(1L, 2L);

		ArgumentCaptor<String> sqlCap = ArgumentCaptor.forClass(String.class);
		verify(namedJdbc).queryForObject(sqlCap.capture(), anyMap(), eq(Boolean.class));
		String sql = sqlCap.getValue();
		assertThat(sql).contains("WITH RECURSIVE");
		assertThat(sql.toUpperCase()).contains("UNION ALL");
		assertThat(sql).containsIgnoringCase("depth");
		assertThat(sql).contains("deleted_at IS NULL");
		assertThat(sql).containsIgnoringCase("EXISTS");
	}

	@Test
	void wouldCreateCycle_passesBothIdsAsParameters() {
		// Verify cả categoryId và newParentId được truyền đúng vào params
		CategoryJdbcRepository repo = new CategoryJdbcRepository(namedJdbc);
		stubQueryForBoolean(false);

		repo.wouldCreateCycle(42L, 99L);

		ArgumentCaptor<Map<String, Object>> paramCap = ArgumentCaptor.forClass(Map.class);
		verify(namedJdbc).queryForObject(anyString(), paramCap.capture(), eq(Boolean.class));
		Map<String, Object> params = paramCap.getValue();
		assertThat(params).containsEntry("categoryId", 42L);
		assertThat(params).containsEntry("newParentId", 99L);
	}
}
