package com.example.smart_erp.catalog.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.oauth2.jwt.Jwt;

import com.example.smart_erp.catalog.dto.ProductsBulkDeleteRequest;
import com.example.smart_erp.catalog.media.CloudinaryMediaService;
import com.example.smart_erp.catalog.repository.CategoryJdbcRepository;
import com.example.smart_erp.catalog.repository.ProductJdbcRepository;
import com.example.smart_erp.catalog.response.ProductBulkDeleteData;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;

@ExtendWith(MockitoExtension.class)
class ProductServiceBulkDeleteTest {

	@Mock
	private ProductJdbcRepository productJdbcRepository;

	@Mock
	private CategoryJdbcRepository categoryJdbcRepository;

	@Mock
	private CloudinaryMediaService cloudinaryMediaService;

	@Mock
	private ProductImageService productImageService;

	private ProductService service;

	@BeforeEach
	void setUp() {
		ExecutorService executor = Executors.newSingleThreadExecutor();
		service = new ProductService(productJdbcRepository, categoryJdbcRepository, cloudinaryMediaService,
				productImageService, executor);
	}

	private static Jwt ownerJwt() {
		Instant now = Instant.now();
		return Jwt.withTokenValue("t").headers(h -> h.put("alg", "none")).issuedAt(now).expiresAt(now.plusSeconds(3600))
				.subject("1").claim("role", "Owner").build();
	}

	private static Jwt staffJwt() {
		Instant now = Instant.now();
		return Jwt.withTokenValue("t").headers(h -> h.put("alg", "none")).issuedAt(now).expiresAt(now.plusSeconds(3600))
				.subject("1").claim("role", "Staff").build();
	}

	@Test
	void bulkDelete_rejectsNonOwner() {
		assertThatThrownBy(() -> service.bulkDelete(new ProductsBulkDeleteRequest(List.of(1)), staffJwt()))
				.isInstanceOf(BusinessException.class).extracting(ex -> ((BusinessException) ex).getCode())
				.isEqualTo(ApiErrorCode.FORBIDDEN);
		verifyNoInteractions(productJdbcRepository);
	}

	@Test
	void bulkDelete_rejectsDuplicateIds() {
		assertThatThrownBy(() -> service.bulkDelete(new ProductsBulkDeleteRequest(List.of(1, 2, 1)), ownerJwt()))
				.isInstanceOf(BusinessException.class).satisfies(ex -> {
					BusinessException be = (BusinessException) ex;
					assertThat(be.getCode()).isEqualTo(ApiErrorCode.BAD_REQUEST);
					assertThat(be.getMessage()).contains("trùng lặp");
				});
		verify(productJdbcRepository, never()).findExistingProductIds(anyList());
	}

	@Test
	void bulkDelete_throwsBadRequestWithInvalidIdWhenSomeMissing() {
		List<Integer> ids = List.of(1, 2, 999);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(Set.of(1, 2));

		assertThatThrownBy(() -> service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt()))
				.isInstanceOfSatisfying(BusinessException.class, ex -> {
					assertThat(ex.getCode()).isEqualTo(ApiErrorCode.BAD_REQUEST);
					assertThat(ex.getMessage()).contains("không tồn tại");
					assertThat(ex.getDetails()).containsKey("invalidId");
					// Đảm bảo invalidId nằm trong tập missing
					String invalidId = (String) ex.getDetails().get("invalidId");
					assertThat(Set.of("999")).contains(invalidId);
				});

		// KHÔNG gọi batch block-reason vì lỗi trước đó
		verify(productJdbcRepository, never()).findBulkDeleteBlockReasons(anyList());
	}

	@Test
	void bulkDelete_throwsBadRequestWhenAllMissing() {
		List<Integer> ids = List.of(100, 200);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(Set.of());

		assertThatThrownBy(() -> service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt()))
				.isInstanceOfSatisfying(BusinessException.class, ex -> {
					assertThat(ex.getCode()).isEqualTo(ApiErrorCode.BAD_REQUEST);
					assertThat(ex.getMessage()).contains("không tồn tại");
					assertThat(ex.getDetails()).containsKey("invalidId");
				});
	}

	@Test
	void bulkDelete_singleIdHappyPath() {
		List<Integer> ids = List.of(42);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(Set.of(42));
		when(productJdbcRepository.findBulkDeleteBlockReasons(ids)).thenReturn(Map.of());
		when(productJdbcRepository.deleteProducts(ids)).thenReturn(1);

		ProductBulkDeleteData data = service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt());

		assertThat(data.deletedCount()).isEqualTo(1);
		assertThat(data.deletedIds()).containsExactly(42);
		// batch methods chỉ được gọi 1 lần
		verify(productJdbcRepository, times(1)).findExistingProductIds(ids);
		verify(productJdbcRepository, times(1)).findBulkDeleteBlockReasons(ids);
		verify(productJdbcRepository, times(1)).lockProductsForUpdate(ids);
		verify(productJdbcRepository, times(1)).deleteProducts(ids);
	}

	@Test
	void bulkDelete_multipleIdsHappyPath() {
		List<Integer> ids = List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(new HashSet<>(ids));
		when(productJdbcRepository.findBulkDeleteBlockReasons(ids)).thenReturn(Map.of());
		when(productJdbcRepository.deleteProducts(ids)).thenReturn(10);

		ProductBulkDeleteData data = service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt());

		assertThat(data.deletedCount()).isEqualTo(10);
		assertThat(data.deletedIds()).hasSize(10);
		// batch được gọi ĐÚNG 1 LẦN, không phải 10 lần (đây là điểm mấu chốt của fix N+1)
		verify(productJdbcRepository, times(1)).findExistingProductIds(ids);
		verify(productJdbcRepository, times(1)).findBulkDeleteBlockReasons(ids);
	}

	@Test
	void bulkDelete_throwsConflictWhenBlockedHasStockReceipt() {
		List<Integer> ids = List.of(1, 2, 3);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(new HashSet<>(ids));
		when(productJdbcRepository.findBulkDeleteBlockReasons(ids))
				.thenReturn(Map.of(2, "HAS_STOCK_RECEIPT"));

		assertThatThrownBy(() -> service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt()))
				.isInstanceOfSatisfying(BusinessException.class, ex -> {
					assertThat(ex.getCode()).isEqualTo(ApiErrorCode.CONFLICT);
					assertThat(ex.getMessage()).contains("phiếu nhập kho");
					assertThat(ex.getDetails()).containsEntry("failedId", "2");
					assertThat(ex.getDetails()).containsEntry("reason", "HAS_STOCK_RECEIPT");
				});

		// Không thực hiện lock/delete khi có block
		verify(productJdbcRepository, never()).lockProductsForUpdate(anyList());
		verify(productJdbcRepository, never()).deleteProducts(anyList());
	}

	@Test
	void bulkDelete_throwsConflictWhenBlockedHasOrderLines() {
		List<Integer> ids = List.of(1, 2, 3);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(new HashSet<>(ids));
		when(productJdbcRepository.findBulkDeleteBlockReasons(ids)).thenReturn(Map.of(3, "HAS_ORDER_LINES"));

		assertThatThrownBy(() -> service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt()))
				.isInstanceOfSatisfying(BusinessException.class, ex -> {
					assertThat(ex.getCode()).isEqualTo(ApiErrorCode.CONFLICT);
					assertThat(ex.getMessage()).contains("đơn hàng");
					assertThat(ex.getDetails()).containsEntry("failedId", "3");
					assertThat(ex.getDetails()).containsEntry("reason", "HAS_ORDER_LINES");
				});
	}

	@Test
	void bulkDelete_throwsConflictWhenBlockedHasStock() {
		List<Integer> ids = List.of(1, 2, 3);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(new HashSet<>(ids));
		when(productJdbcRepository.findBulkDeleteBlockReasons(ids)).thenReturn(Map.of(1, "HAS_STOCK"));

		assertThatThrownBy(() -> service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt()))
				.isInstanceOfSatisfying(BusinessException.class, ex -> {
					assertThat(ex.getCode()).isEqualTo(ApiErrorCode.CONFLICT);
					assertThat(ex.getMessage()).contains("tồn kho");
					assertThat(ex.getDetails()).containsEntry("failedId", "1");
					assertThat(ex.getDetails()).containsEntry("reason", "HAS_STOCK");
				});
	}

	@Test
	void bulkDelete_throwsInternalServerErrorWhenDeletedCountMismatch() {
		List<Integer> ids = List.of(1, 2, 3);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(new HashSet<>(ids));
		when(productJdbcRepository.findBulkDeleteBlockReasons(ids)).thenReturn(Map.of());
		when(productJdbcRepository.deleteProducts(ids)).thenReturn(2); // chỉ xóa được 2, không khớp 3

		assertThatThrownBy(() -> service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt()))
				.isInstanceOfSatisfying(BusinessException.class, ex -> {
					assertThat(ex.getCode()).isEqualTo(ApiErrorCode.INTERNAL_SERVER_ERROR);
					assertThat(ex.getMessage()).contains("không khớp số dòng");
				});
	}

	@Test
	void bulkDelete_doesNotCallLegacyPerItemExistenceCheck() {
		// Đảm bảo KHÔNG còn gọi per-item existsProductId (N query cũ) — chỉ batch
		List<Integer> ids = List.of(1, 2, 3);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(new HashSet<>(ids));
		when(productJdbcRepository.findBulkDeleteBlockReasons(ids)).thenReturn(Map.of());
		when(productJdbcRepository.deleteProducts(ids)).thenReturn(3);

		service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt());

		verify(productJdbcRepository, never()).existsProductId(org.mockito.ArgumentMatchers.anyInt());
		verify(productJdbcRepository, never()).existsStockReceiptDetail(org.mockito.ArgumentMatchers.anyInt());
		verify(productJdbcRepository, never()).existsOrderDetail(org.mockito.ArgumentMatchers.anyInt());
		verify(productJdbcRepository, never()).sumInventoryQuantity(org.mockito.ArgumentMatchers.anyInt());
	}

	@Test
	void bulkDelete_returnsAllDeletedIdsInResponse() {
		List<Integer> ids = List.of(10, 20, 30);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(new HashSet<>(ids));
		when(productJdbcRepository.findBulkDeleteBlockReasons(ids)).thenReturn(Map.of());
		when(productJdbcRepository.deleteProducts(ids)).thenReturn(3);

		ProductBulkDeleteData data = service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt());

		assertThat(new HashSet<>(data.deletedIds())).isEqualTo(new HashSet<>(ids));
		assertThat(data.deletedCount()).isEqualTo(3);
	}

	@Test
	void bulkDelete_withZeroIds_callsBatchButNoOpDelete() {
		// Edge case: list ids rỗng — không thể xảy ra do validation @NotEmpty ở DTO, nhưng bulk methods phải handle an toàn
		// Do @NotEmpty nên invalid — nhưng ta vẫn test bằng cách tạo request rỗng để verify batch methods handle empty
		ProductsBulkDeleteRequest req = new ProductsBulkDeleteRequest(new ArrayList<>());

		// @NotEmpty sẽ không được validate trong unit test (chỉ khi qua controller),
		// nên ta test hành vi của service với empty list.
		// Service phải gọi batch và nhận empty kết quả.
		when(productJdbcRepository.findExistingProductIds(req.ids())).thenReturn(Set.of());
		when(productJdbcRepository.findBulkDeleteBlockReasons(req.ids())).thenReturn(Map.of());
		when(productJdbcRepository.deleteProducts(req.ids())).thenReturn(0);

		ProductBulkDeleteData data = service.bulkDelete(req, ownerJwt());

		assertThat(data.deletedCount()).isEqualTo(0);
		assertThat(data.deletedIds()).isEmpty();
		verify(productJdbcRepository, times(1)).findExistingProductIds(req.ids());
		verify(productJdbcRepository, times(1)).findBulkDeleteBlockReasons(req.ids());
	}

	@Test
	void bulkDelete_mixedBlockedAndUnblocked_throwsOnFirstBlocked() {
		// Mixed: id 2 bị block, id 1, 3 ok — phải throw khi phát hiện block đầu tiên
		List<Integer> ids = List.of(1, 2, 3);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(new HashSet<>(ids));
		when(productJdbcRepository.findBulkDeleteBlockReasons(ids))
				.thenReturn(Map.of(2, "HAS_STOCK_RECEIPT", 3, "HAS_STOCK"));

		assertThatThrownBy(() -> service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt()))
				.isInstanceOfSatisfying(BusinessException.class, ex -> {
					assertThat(ex.getCode()).isEqualTo(ApiErrorCode.CONFLICT);
					// failedId phải là 1 trong các id bị block
					String failedId = (String) ex.getDetails().get("failedId");
					assertThat(Set.of("2", "3")).contains(failedId);
				});
	}

	@Test
	void bulkDelete_propagatesToctouConflictFromBatchLock() {
		// I3: khi race xảy ra (id bị xóa giữa check và lock), BusinessException(CONFLICT)
		// từ lockProductsForUpdateBatch phải được propagate lên service
		List<Integer> ids = List.of(1, 2, 3);
		when(productJdbcRepository.findExistingProductIds(ids)).thenReturn(new HashSet<>(ids));
		when(productJdbcRepository.findBulkDeleteBlockReasons(ids)).thenReturn(Map.of());
		org.mockito.Mockito.doThrow(new BusinessException(ApiErrorCode.CONFLICT,
				"Sản phẩm đã bị xóa bởi người dùng khác", Map.of("id", "2")))
				.when(productJdbcRepository).lockProductsForUpdate(ids);

		assertThatThrownBy(() -> service.bulkDelete(new ProductsBulkDeleteRequest(ids), ownerJwt()))
				.isInstanceOfSatisfying(BusinessException.class, ex -> {
					assertThat(ex.getCode()).isEqualTo(ApiErrorCode.CONFLICT);
					assertThat(ex.getMessage()).contains("Sản phẩm đã bị xóa bởi người dùng khác");
					assertThat(ex.getDetails()).containsEntry("id", "2");
				});

		// deleteProducts không được gọi vì lock thất bại
		verify(productJdbcRepository, never()).deleteProducts(anyList());
	}
}
