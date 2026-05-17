package com.example.smart_erp.ai.catalogdraft;

import java.util.UUID;

import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.smart_erp.ai.catalogdraft.dto.CatalogDraftCommitResult;
import com.example.smart_erp.ai.catalogdraft.dto.CatalogDraftCreateRequest;
import com.example.smart_erp.ai.catalogdraft.dto.CatalogDraftPatchRequest;
import com.example.smart_erp.ai.catalogdraft.dto.CatalogDraftResponse;
import com.example.smart_erp.common.api.ApiSuccessResponse;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/ai/catalog-drafts")
@Validated
public class AiCatalogDraftController {

	private final AiCatalogDraftService service;

	public AiCatalogDraftController(AiCatalogDraftService service) {
		this.service = service;
	}

	@PostMapping
	@PreAuthorize("hasAuthority('can_use_ai')")
	public ResponseEntity<ApiSuccessResponse<CatalogDraftResponse>> create(
			Authentication authentication,
			@Valid @RequestBody CatalogDraftCreateRequest body) {
		CatalogDraftResponse data = service.create(authentication, body);
		return ResponseEntity.status(201).body(ApiSuccessResponse.of(data, "Đã tạo nháp"));
	}

	@GetMapping("/{id}")
	@PreAuthorize("hasAuthority('can_use_ai')")
	public ResponseEntity<ApiSuccessResponse<CatalogDraftResponse>> get(
			Authentication authentication,
			@PathVariable UUID id) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.get(authentication, id), "Thành công"));
	}

	@PatchMapping("/{id}")
	@PreAuthorize("hasAuthority('can_use_ai')")
	public ResponseEntity<ApiSuccessResponse<CatalogDraftResponse>> patch(
			Authentication authentication,
			@PathVariable UUID id,
			@Valid @RequestBody CatalogDraftPatchRequest body) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.patch(authentication, id, body), "Đã lưu nháp"));
	}

	@PostMapping("/{id}/commit")
	@PreAuthorize("hasAuthority('can_use_ai')")
	public ResponseEntity<ApiSuccessResponse<CatalogDraftCommitResult>> commit(
			Authentication authentication,
			@PathVariable UUID id) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.commit(authentication, id), "Đã xử lý commit"));
	}

	@DeleteMapping("/{id}")
	@PreAuthorize("hasAuthority('can_use_ai')")
	public ResponseEntity<ApiSuccessResponse<Void>> delete(Authentication authentication, @PathVariable UUID id) {
		service.delete(authentication, id);
		return ResponseEntity.ok(ApiSuccessResponse.of(null, "Đã hủy nháp"));
	}
}
