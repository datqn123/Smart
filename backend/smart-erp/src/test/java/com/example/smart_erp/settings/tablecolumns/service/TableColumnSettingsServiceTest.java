package com.example.smart_erp.settings.tablecolumns.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.Instant;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.oauth2.jwt.Jwt;

import com.example.smart_erp.auth.repository.SystemLogJdbcRepository;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.settings.tablecolumns.dto.SaveTableColumnSettingsRequest;
import com.example.smart_erp.settings.tablecolumns.repository.UserTableColumnSettingsJdbcRepository;
import com.fasterxml.jackson.databind.ObjectMapper;

@ExtendWith(MockitoExtension.class)
class TableColumnSettingsServiceTest {

	@Mock
	private UserTableColumnSettingsJdbcRepository repo;

	@Mock
	private SystemLogJdbcRepository systemLogJdbcRepository;

	private TableColumnSettingsService service;

	@BeforeEach
	void setUp() {
		service = new TableColumnSettingsService(repo, new ObjectMapper(), systemLogJdbcRepository);
	}

	@Test
	void getInventoryScope_returnsDefaultsWhenNoPersistedRows() {
		when(repo.findByUserId(7)).thenReturn(List.of());
		var out = service.getInventoryScope(jwt(7));
		assertThat(out.items()).hasSize(3);
		assertThat(out.items().get(0).tableKey()).isEqualTo("inventory_stock");
		assertThat(out.items().get(0).columns()).extracting("key")
				.containsExactly("skuCode", "productName", "location", "quantity", "expiryDate", "status");
	}

	@Test
	void getInventoryScope_normalizesStoredUnknownAndMissingColumns() {
		when(repo.findByUserId(7)).thenReturn(List.of(
				new UserTableColumnSettingsJdbcRepository.Row(
						"inventory_dispatch",
						"[\"dispatchDate\"]",
						"[\"dispatchCode\",\"orderCode\",\"unknown\"]",
						Instant.now(),
						"Owner")));
		var out = service.getInventoryScope(jwt(7));
		var dispatch = out.items().stream().filter(i -> "inventory_dispatch".equals(i.tableKey())).findFirst().orElseThrow();
		assertThat(dispatch.columns()).extracting("key")
				.containsExactly("dispatchCode", "orderCode", "customerName", "dispatchDate", "userName", "itemCount", "status");
		assertThat(dispatch.columns().stream().filter(c -> "dispatchDate".equals(c.key())).findFirst().orElseThrow().visible())
				.isFalse();
	}

	@Test
	void saveInventoryScope_rejectsRequiredHiddenColumn() {
		SaveTableColumnSettingsRequest req = new SaveTableColumnSettingsRequest(List.of(
				new SaveTableColumnSettingsRequest.Item(
						"inventory_dispatch",
						List.of("dispatchCode"),
						List.of("dispatchCode", "orderCode"))));
		assertThatThrownBy(() -> service.saveInventoryScope(jwt(7), req))
				.isInstanceOfSatisfying(BusinessException.class, ex -> {
					assertThat(ex.getCode()).isEqualTo(ApiErrorCode.BAD_REQUEST);
					assertThat(ex.getDetails()).containsEntry("items[0].hiddenColumns",
							"Cột bắt buộc dispatchCode không thể bị ẩn.");
				});
		verify(repo, never()).upsert(anyInt(), eq("inventory_dispatch"), org.mockito.ArgumentMatchers.anyString(),
				org.mockito.ArgumentMatchers.anyString(), anyInt());
	}

	@Test
	void saveInventoryScope_upsertsAndNormalizesMissingOrderTail() {
		SaveTableColumnSettingsRequest req = new SaveTableColumnSettingsRequest(List.of(
				new SaveTableColumnSettingsRequest.Item(
						"inventory_dispatch",
						List.of("dispatchDate"),
						List.of("dispatchCode", "orderCode"))));

		when(repo.findByUserId(7)).thenReturn(List.of(
				new UserTableColumnSettingsJdbcRepository.Row(
						"inventory_dispatch",
						"[\"dispatchDate\"]",
						"[\"dispatchCode\",\"orderCode\",\"customerName\",\"dispatchDate\",\"userName\",\"itemCount\",\"status\"]",
						Instant.now(),
						"Owner")));

		var out = service.saveInventoryScope(jwt(7), req);

		verify(repo).upsert(eq(7), eq("inventory_dispatch"), eq("[\"dispatchDate\"]"),
				eq("[\"dispatchCode\",\"orderCode\",\"customerName\",\"dispatchDate\",\"userName\",\"itemCount\",\"status\"]"), eq(7));
		verify(systemLogJdbcRepository).insertInventoryPatch(eq(7), org.mockito.ArgumentMatchers.anyString());
		assertThat(out.items()).hasSize(3);
	}

	private static Jwt jwt(int userId) {
		return new Jwt("token", Instant.now(), Instant.now().plusSeconds(3600), Map.of("alg", "HS256"),
				Map.of("sub", String.valueOf(userId), "role", "Owner"));
	}
}

