package com.example.smart_erp.ai.inventorydraft;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.UUID;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.smart_erp.ai.inventorydraft.dto.InventoryDraftCommitResult;
import com.example.smart_erp.ai.inventorydraft.dto.InventoryDraftCreateRequest;
import com.example.smart_erp.ai.inventorydraft.dto.InventoryDraftPatchRequest;
import com.example.smart_erp.ai.inventorydraft.dto.InventoryDraftResponse;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.receipts.response.StockReceiptViewData;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

@Service
public class AiInventoryDraftService {

	public static final int MAX_LINES = 20;
	public static final int TTL_HOURS = 72;

	private final AiInventoryDraftJdbcRepository repository;
	private final AiInventoryDraftCommitter committer;
	private final ObjectMapper objectMapper;

	public AiInventoryDraftService(
			AiInventoryDraftJdbcRepository repository,
			AiInventoryDraftCommitter committer,
			ObjectMapper objectMapper) {
		this.repository = repository;
		this.committer = committer;
		this.objectMapper = objectMapper;
	}

	@Transactional
	public InventoryDraftResponse create(Authentication auth, InventoryDraftCreateRequest req) {
		InventoryEntityType entityType = parseEntity(req.entityType());
		requirePermission(auth);
		validateLinesArray(req.lines());
		ObjectNode payload = objectMapper.createObjectNode();
		payload.set("header", req.header());
		payload.set("lineColumns", req.lineColumns());
		payload.set("lines", req.lines());
		if (req.meta() != null && !req.meta().isNull()) {
			payload.set("meta", req.meta());
		}
		Identity id = identity(auth);
		Instant expires = Instant.now().plus(TTL_HOURS, ChronoUnit.HOURS);
		UUID draftId = repository.insert(
				id.userId(),
				id.tenantId(),
				req.conversationId(),
				entityType.wireValue(),
				payload,
				expires);
		return loadRequired(draftId, id.userId());
	}

	@Transactional(readOnly = true)
	public InventoryDraftResponse get(Authentication auth, UUID draftId) {
		Identity id = identity(auth);
		AiInventoryDraftJdbcRepository.DraftRow row = findOwned(draftId, id.userId());
		requirePermission(auth);
		ensureNotExpired(row);
		return toResponse(row);
	}

	@Transactional
	public InventoryDraftResponse patch(Authentication auth, UUID draftId, InventoryDraftPatchRequest req) {
		Identity id = identity(auth);
		AiInventoryDraftJdbcRepository.DraftRow row = findOwned(draftId, id.userId());
		requirePermission(auth);
		ensureEditable(row);
		validateLinesArray(req.lines());
		ObjectNode payload = row.payload().deepCopy();
		payload.set("lines", req.lines());
		if (req.header() != null && !req.header().isNull()) {
			payload.set("header", req.header());
		}
		if (req.lineColumns() != null && !req.lineColumns().isNull()) {
			payload.set("lineColumns", req.lineColumns());
		}
		if (!repository.updatePayload(draftId, id.userId(), payload)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể cập nhật nháp (hết hạn hoặc đã commit)");
		}
		return loadRequired(draftId, id.userId());
	}

	@Transactional
	public InventoryDraftCommitResult commit(Authentication auth, UUID draftId) {
		Identity id = identity(auth);
		AiInventoryDraftJdbcRepository.DraftRow row = findOwned(draftId, id.userId());
		InventoryEntityType entityType = parseEntity(row.entityType());
		requirePermission(auth);
		ensureEditable(row);
		Jwt jwt = requireJwt(auth);
		ObjectNode payload = row.payload().deepCopy();
		ObjectNode header = payload.has("header") && payload.get("header").isObject()
				? (ObjectNode) payload.get("header")
				: objectMapper.createObjectNode();
		JsonNode linesNode = payload.get("lines");
		if (linesNode == null || !linesNode.isArray()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Nháp không có danh sách dòng");
		}
		ArrayNode lines = (ArrayNode) linesNode;
		StockReceiptViewData created;
		try {
			created = switch (entityType) {
				case STOCK_RECEIPT -> committer.commitStockReceipt(header, lines, jwt);
			};
		}
		catch (BusinessException e) {
			return new InventoryDraftCommitResult(false, e.getMessage(), null, null, objectMapper.valueToTree(toResponse(row)));
		}
		ObjectNode commitResult = objectMapper.createObjectNode();
		commitResult.put("committedAt", Instant.now().toString());
		commitResult.put("createdReceiptId", created.id());
		commitResult.put("receiptCode", created.receiptCode());
		repository.updateAfterCommit(draftId, id.userId(), payload, commitResult, "committed");
		InventoryDraftResponse draft = loadRequired(draftId, id.userId());
		return new InventoryDraftCommitResult(
				true,
				"Đã tạo phiếu nhập " + created.receiptCode(),
				(int) created.id(),
				created.receiptCode(),
				objectMapper.valueToTree(draft));
	}

	@Transactional
	public void delete(Authentication auth, UUID draftId) {
		Identity id = identity(auth);
		findOwned(draftId, id.userId());
		requirePermission(auth);
		ObjectNode payload = findOwned(draftId, id.userId()).payload().deepCopy();
		repository.updateAfterCommit(draftId, id.userId(), payload, null, "expired");
	}

	private InventoryDraftResponse loadRequired(UUID id, String userId) {
		return repository.findByIdForUser(id, userId)
				.map(this::toResponse)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nháp"));
	}

	private AiInventoryDraftJdbcRepository.DraftRow findOwned(UUID id, String userId) {
		return repository.findByIdForUser(id, userId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nháp"));
	}

	private static void ensureEditable(AiInventoryDraftJdbcRepository.DraftRow row) {
		if (!"draft".equals(row.status())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Nháp không còn ở trạng thái chỉnh sửa");
		}
		if (row.expiresAt().isBefore(Instant.now())) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Nháp đã hết hạn");
		}
	}

	private static void ensureNotExpired(AiInventoryDraftJdbcRepository.DraftRow row) {
		if ("expired".equals(row.status()) || row.expiresAt().isBefore(Instant.now())) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Nháp đã hết hạn");
		}
	}

	private void validateLinesArray(JsonNode lines) {
		if (lines == null || !lines.isArray()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "lines phải là mảng");
		}
		if (lines.size() > MAX_LINES) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tối đa " + MAX_LINES + " dòng mỗi phiếu");
		}
	}

	private InventoryDraftResponse toResponse(AiInventoryDraftJdbcRepository.DraftRow row) {
		JsonNode payload = row.payload();
		return new InventoryDraftResponse(
				row.id().toString(),
				row.entityType(),
				row.status(),
				payload.get("header"),
				payload.get("lineColumns"),
				payload.get("lines"),
				payload.get("meta"),
				row.commitResult(),
				row.conversationId(),
				row.createdAt(),
				row.updatedAt(),
				row.expiresAt());
	}

	private static InventoryEntityType parseEntity(String raw) {
		return InventoryEntityType.parse(raw)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, "entityType không hợp lệ"));
	}

	private static void requirePermission(Authentication auth) {
		if (!hasAuthority(auth, "can_use_ai")) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Không có quyền dùng AI");
		}
		if (!hasAuthority(auth, "can_manage_inventory")) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Không có quyền quản lý kho");
		}
	}

	private static Jwt requireJwt(Authentication auth) {
		if (auth == null || !(auth.getPrincipal() instanceof Jwt jwt)) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, "Yêu cầu JWT");
		}
		return jwt;
	}

	private static boolean hasAuthority(Authentication auth, String name) {
		if (auth == null) {
			return false;
		}
		for (GrantedAuthority ga : auth.getAuthorities()) {
			if (name.equals(ga.getAuthority())) {
				return true;
			}
		}
		return false;
	}

	private static Identity identity(Authentication auth) {
		Jwt jwt = requireJwt(auth);
		String userId = jwt.getClaimAsString("user_id");
		if (userId == null || userId.isBlank()) {
			userId = jwt.getSubject();
		}
		String tenantId = jwt.getClaimAsString("tenant_id");
		if (tenantId == null || tenantId.isBlank()) {
			tenantId = "1";
		}
		return new Identity(userId, tenantId);
	}

	private record Identity(String userId, String tenantId) {
	}
}
