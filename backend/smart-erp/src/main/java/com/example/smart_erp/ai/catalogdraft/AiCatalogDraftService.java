package com.example.smart_erp.ai.catalogdraft;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.UUID;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.smart_erp.ai.catalogdraft.dto.CatalogDraftCommitResult;
import com.example.smart_erp.ai.catalogdraft.dto.CatalogDraftCreateRequest;
import com.example.smart_erp.ai.catalogdraft.dto.CatalogDraftPatchRequest;
import com.example.smart_erp.ai.catalogdraft.dto.CatalogDraftResponse;
import com.example.smart_erp.ai.catalogdraft.dto.CatalogDraftRowCommitOutcome;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

@Service
public class AiCatalogDraftService {

	public static final int MAX_ROWS = 50;
	public static final int TTL_HOURS = 72;

	private final AiCatalogDraftJdbcRepository repository;
	private final AiCatalogDraftCommitter committer;
	private final ObjectMapper objectMapper;

	public AiCatalogDraftService(
			AiCatalogDraftJdbcRepository repository,
			AiCatalogDraftCommitter committer,
			ObjectMapper objectMapper) {
		this.repository = repository;
		this.committer = committer;
		this.objectMapper = objectMapper;
	}

	@Transactional
	public CatalogDraftResponse create(Authentication auth, CatalogDraftCreateRequest req) {
		CatalogEntityType entityType = parseEntity(req.entityType());
		requireEntityPermission(auth, entityType);
		validateRowsArray(req.rows());
		ObjectNode payload = objectMapper.createObjectNode();
		payload.set("columns", req.columns());
		payload.set("rows", req.rows());
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
	public CatalogDraftResponse get(Authentication auth, UUID draftId) {
		Identity id = identity(auth);
		AiCatalogDraftJdbcRepository.DraftRow row = findOwned(draftId, id.userId());
		requireEntityPermission(auth, parseEntity(row.entityType()));
		ensureNotExpired(row);
		return toResponse(row);
	}

	@Transactional
	public CatalogDraftResponse patch(Authentication auth, UUID draftId, CatalogDraftPatchRequest req) {
		Identity id = identity(auth);
		AiCatalogDraftJdbcRepository.DraftRow row = findOwned(draftId, id.userId());
		CatalogEntityType entityType = parseEntity(row.entityType());
		requireEntityPermission(auth, entityType);
		ensureEditable(row);
		validateRowsArray(req.rows());
		ObjectNode payload = row.payload().deepCopy();
		payload.set("rows", req.rows());
		if (req.columns() != null && !req.columns().isNull()) {
			payload.set("columns", req.columns());
		}
		if (!repository.updatePayload(draftId, id.userId(), payload)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể cập nhật nháp (hết hạn hoặc đã commit)");
		}
		return loadRequired(draftId, id.userId());
	}

	@Transactional
	public CatalogDraftCommitResult commit(Authentication auth, UUID draftId) {
		Identity id = identity(auth);
		AiCatalogDraftJdbcRepository.DraftRow row = findOwned(draftId, id.userId());
		CatalogEntityType entityType = parseEntity(row.entityType());
		requireEntityPermission(auth, entityType);
		ensureEditable(row);
		ObjectNode payload = row.payload().deepCopy();
		JsonNode rowsNode = payload.get("rows");
		if (rowsNode == null || !rowsNode.isArray()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Nháp không có danh sách dòng");
		}
		ArrayNode rows = (ArrayNode) rowsNode;
		var outcomes = committer.commitRows(entityType, rows);
		int committed = 0;
		int failed = 0;
		int skipped = 0;
		for (CatalogDraftRowCommitOutcome o : outcomes) {
			if (o.success()) {
				if ("Đã ghi trước đó".equals(o.message())) {
					skipped++;
				}
				else {
					committed++;
				}
			}
			else {
				failed++;
			}
		}
		payload.set("rows", rows);
		ObjectNode commitResult = objectMapper.createObjectNode();
		commitResult.put("committedAt", Instant.now().toString());
		commitResult.set("outcomes", objectMapper.valueToTree(outcomes));
		String status = failed == 0 && committed + skipped > 0 ? "committed" : "draft";
		repository.updateAfterCommit(draftId, id.userId(), payload, commitResult, status);
		CatalogDraftResponse draft = loadRequired(draftId, id.userId());
		return new CatalogDraftCommitResult(committed, failed, skipped, outcomes, objectMapper.valueToTree(draft));
	}

	@Transactional
	public void delete(Authentication auth, UUID draftId) {
		Identity id = identity(auth);
		AiCatalogDraftJdbcRepository.DraftRow row = findOwned(draftId, id.userId());
		requireEntityPermission(auth, parseEntity(row.entityType()));
		ObjectNode payload = row.payload().deepCopy();
		repository.updateAfterCommit(draftId, id.userId(), payload, null, "expired");
	}

	private CatalogDraftResponse loadRequired(UUID id, String userId) {
		return repository.findByIdForUser(id, userId)
				.map(this::toResponse)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nháp"));
	}

	private AiCatalogDraftJdbcRepository.DraftRow findOwned(UUID id, String userId) {
		return repository.findByIdForUser(id, userId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nháp"));
	}

	private static void ensureEditable(AiCatalogDraftJdbcRepository.DraftRow row) {
		if (!"draft".equals(row.status())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Nháp không còn ở trạng thái chỉnh sửa");
		}
		if (row.expiresAt().isBefore(Instant.now())) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Nháp đã hết hạn");
		}
	}

	private static void ensureNotExpired(AiCatalogDraftJdbcRepository.DraftRow row) {
		if ("expired".equals(row.status()) || row.expiresAt().isBefore(Instant.now())) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Nháp đã hết hạn");
		}
	}

	private void validateRowsArray(JsonNode rows) {
		if (rows == null || !rows.isArray()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "rows phải là mảng");
		}
		if (rows.size() > MAX_ROWS) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tối đa " + MAX_ROWS + " dòng mỗi nháp");
		}
	}

	private CatalogDraftResponse toResponse(AiCatalogDraftJdbcRepository.DraftRow row) {
		JsonNode payload = row.payload();
		return new CatalogDraftResponse(
				row.id().toString(),
				row.entityType(),
				row.status(),
				payload.get("columns"),
				payload.get("rows"),
				payload.get("meta"),
				row.commitResult(),
				row.conversationId(),
				row.createdAt(),
				row.updatedAt(),
				row.expiresAt());
	}

	private static CatalogEntityType parseEntity(String raw) {
		return CatalogEntityType.parse(raw)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, "entityType không hợp lệ"));
	}

	private static void requireEntityPermission(Authentication auth, CatalogEntityType type) {
		if (!hasAuthority(auth, "can_use_ai")) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Không có quyền dùng AI");
		}
		if (type.requiresManageProducts() && !hasAuthority(auth, "can_manage_products")) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Không có quyền quản lý danh mục/sản phẩm");
		}
		if (type.requiresManageCustomers() && !hasAuthority(auth, "can_manage_customers")) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Không có quyền quản lý khách hàng");
		}
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
		if (auth == null || !(auth.getPrincipal() instanceof org.springframework.security.oauth2.jwt.Jwt jwt)) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, "Yêu cầu JWT");
		}
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
