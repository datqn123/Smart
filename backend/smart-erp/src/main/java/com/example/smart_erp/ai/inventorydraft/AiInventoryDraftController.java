package com.example.smart_erp.ai.inventorydraft;

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

import com.example.smart_erp.ai.inventorydraft.dto.InventoryDraftCommitResult;
import com.example.smart_erp.ai.inventorydraft.dto.InventoryDraftCreateRequest;
import com.example.smart_erp.ai.inventorydraft.dto.InventoryDraftPatchRequest;
import com.example.smart_erp.ai.inventorydraft.dto.InventoryDraftResponse;
import com.example.smart_erp.common.api.ApiSuccessResponse;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/ai/inventory-drafts")
@Validated
public class AiInventoryDraftController {

	private final AiInventoryDraftService service;

	public AiInventoryDraftController(AiInventoryDraftService service) {
		this.service = service;
	}

	@PostMapping
	@PreAuthorize("hasAuthority('can_use_ai') and hasAuthority('can_manage_inventory')")
	public ResponseEntity<ApiSuccessResponse<InventoryDraftResponse>> create(
			Authentication authentication,
			@Valid @RequestBody InventoryDraftCreateRequest body) {
		InventoryDraftResponse data = service.create(authentication, body);
		return ResponseEntity.status(201).body(ApiSuccessResponse.of(data, "Đã tạo nháp phiếu kho"));
	}

	@GetMapping("/{id}")
	@PreAuthorize("hasAuthority('can_use_ai') and hasAuthority('can_manage_inventory')")
	public ResponseEntity<ApiSuccessResponse<InventoryDraftResponse>> get(
			Authentication authentication,
			@PathVariable UUID id) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.get(authentication, id), "Thành công"));
	}

	@PatchMapping("/{id}")
	@PreAuthorize("hasAuthority('can_use_ai') and hasAuthority('can_manage_inventory')")
	public ResponseEntity<ApiSuccessResponse<InventoryDraftResponse>> patch(
			Authentication authentication,
			@PathVariable UUID id,
			@Valid @RequestBody InventoryDraftPatchRequest body) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.patch(authentication, id, body), "Đã lưu nháp"));
	}

	@PostMapping("/{id}/commit")
	@PreAuthorize("hasAuthority('can_use_ai') and hasAuthority('can_manage_inventory')")
	public ResponseEntity<ApiSuccessResponse<InventoryDraftCommitResult>> commit(
			Authentication authentication,
			@PathVariable UUID id) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.commit(authentication, id), "Đã xử lý commit"));
	}

	@DeleteMapping("/{id}")
	@PreAuthorize("hasAuthority('can_use_ai') and hasAuthority('can_manage_inventory')")
	public ResponseEntity<ApiSuccessResponse<Void>> delete(Authentication authentication, @PathVariable UUID id) {
		service.delete(authentication, id);
		return ResponseEntity.ok(ApiSuccessResponse.of(null, "Đã hủy nháp"));
	}
}
