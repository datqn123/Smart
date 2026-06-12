package com.example.smart_erp.custominterface.service;

import java.util.List;

import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.custominterface.dto.CustomBuilderBundleRequest;
import com.example.smart_erp.custominterface.dto.CustomFieldRequest;
import com.example.smart_erp.custominterface.dto.CustomPermissionRequest;
import com.example.smart_erp.custominterface.dto.CustomViewRequest;
import com.example.smart_erp.custominterface.repository.CustomEntityJdbcRepository;
import com.example.smart_erp.custominterface.repository.CustomEntityJdbcRepository.EntityRow;
import com.example.smart_erp.custominterface.repository.CustomEntityJdbcRepository.FieldRow;
import com.example.smart_erp.custominterface.repository.CustomEntityJdbcRepository.PermissionRow;
import com.example.smart_erp.custominterface.repository.CustomEntityJdbcRepository.ViewRow;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository.PageRow;
import com.example.smart_erp.custominterface.response.CustomBuilderBundleData;
import com.example.smart_erp.custominterface.response.CustomEntityData;
import com.example.smart_erp.custominterface.response.CustomFieldData;
import com.example.smart_erp.custominterface.response.CustomMenuPageData;
import com.example.smart_erp.custominterface.response.CustomPermissionData;
import com.example.smart_erp.custominterface.response.CustomViewData;
import com.example.smart_erp.custominterface.response.ValidationSummaryData;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class CustomBuilderService {

	private static final TypeReference<List<String>> LIST_OF_STRING = new TypeReference<>() {
	};

	private static final String BAD_REQUEST = "Dữ liệu không hợp lệ. Vui lòng kiểm tra lại các trường được đánh dấu.";
	private static final String NOT_FOUND_PAGE = "Không tìm thấy giao diện tùy chỉnh.";
	private static final String NOT_FOUND_ENTITY = "Không tìm thấy entity tùy chỉnh.";
	private static final String STALE = "Cấu hình đã được cập nhật bởi người khác. Vui lòng tải lại trước khi lưu.";
	private static final String PUBLISH_INVALID =
			"Cấu hình chưa hợp lệ để publish. Vui lòng kiểm tra các cảnh báo.";

	private final CustomEntityJdbcRepository entityRepository;
	private final CustomInterfaceJdbcRepository menuRepository;
	private final CustomMetadataValidator validator;
	private final ObjectMapper objectMapper;

	public CustomBuilderService(CustomEntityJdbcRepository entityRepository, CustomInterfaceJdbcRepository menuRepository,
			CustomMetadataValidator validator, ObjectMapper objectMapper) {
		this.entityRepository = entityRepository;
		this.menuRepository = menuRepository;
		this.validator = validator;
		this.objectMapper = objectMapper;
	}

	@Transactional(readOnly = true)
	public CustomBuilderBundleData getBundle(String pageKey) {
		PageRow page = findPage(pageKey);
		EntityRow entity = findEntity(page.entityKey());
		return toBundle(page, entity, validate(page, entity));
	}

	@Transactional
	public CustomBuilderBundleData saveBundle(String pageKey, CustomBuilderBundleRequest request, Jwt jwt) {
		if (request == null || request.menuPage() == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST);
		}
		PageRow page = findPage(pageKey);
		EntityRow entity = findEntity(page.entityKey());
		assertEtag(page.etag(), suppliedEtag(request));

		ValidationSummaryData draftSummary = validator.validateDraft(request.menuPage().key(), request.entityKey(),
				request.fields(), request.views(), request.permissions());
		if (!draftSummary.valid()) {
			return toBundle(page, entity, draftSummary);
		}

		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		EntityRow updated = entityRepository.replaceBundle(entity, request.entityLabel(), request.entityDescription(),
				request.fields(), request.views(), request.permissions(), userId);
		return toBundle(page, updated, validate(page, updated));
	}

	@Transactional(readOnly = true)
	public ValidationSummaryData validatePage(String pageKey) {
		PageRow page = findPage(pageKey);
		EntityRow entity = findEntity(page.entityKey());
		return validate(page, entity);
	}

	@Transactional
	public CustomBuilderBundleData publish(String pageKey, String etag, Jwt jwt) {
		PageRow page = findPage(pageKey);
		EntityRow entity = findEntity(page.entityKey());
		assertEtag(page.etag(), etag);
		ValidationSummaryData summary = validate(page, entity);
		if (!summary.valid()) {
			throw new BusinessException(ApiErrorCode.UNPROCESSABLE_ENTITY, PUBLISH_INVALID);
		}
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		entityRepository.publishSnapshot(page.key(), entity, userId);
		menuRepository.publishPage(page.key(), userId);

		PageRow publishedPage = findPage(page.key());
		EntityRow publishedEntity = findEntity(entity.key());
		return toBundle(publishedPage, publishedEntity, ValidationSummaryData.ok());
	}

	private ValidationSummaryData validate(PageRow page, EntityRow entity) {
		return validator.validateDraft(page.key(), entity.key(), toFieldRequests(entityRepository.findFields(entity.key())),
				toViewRequest(entityRepository.findView(entity.key()).orElseGet(() -> emptyView(entity.key()))),
				toPermissionRequest(entityRepository.findPermissions(entity.key())));
	}

	private CustomBuilderBundleData toBundle(PageRow page, EntityRow entity, ValidationSummaryData summary) {
		List<FieldRow> fields = entityRepository.findFields(entity.key());
		ViewRow view = entityRepository.findView(entity.key()).orElseGet(() -> emptyView(entity.key()));
		PermissionRow permissions = entityRepository.findPermissions(entity.key());
		return new CustomBuilderBundleData(toPageData(page, summary),
				new CustomEntityData(entity.key(), entity.label(), entity.description(), entity.status(),
						entity.draftVersion(), entity.draftVersion(), entity.publishedVersion(), entity.etag()),
				fields.stream().map(this::toFieldData).toList(),
				new CustomViewData(view.listColumns(), view.filterFields(), view.defaultSort(), view.formSections(),
						"desktop"),
				new CustomPermissionData(permissions.view(), permissions.create(), permissions.update(),
						permissions.delete()),
				summary, page.etag());
	}

	private List<CustomFieldRequest> toFieldRequests(List<FieldRow> rows) {
		return rows.stream()
				.map(row -> new CustomFieldRequest(row.id(), row.label(), row.fieldKey(), row.type(), row.required(),
						row.filterable(), row.sortable(), row.searchable(), row.order(), row.helperText(), row.options(),
						row.reference(), row.validation(), row.defaultValue(), false, false, row.status()))
				.toList();
	}

	private CustomViewRequest toViewRequest(ViewRow row) {
		return new CustomViewRequest(row.listColumns(), row.filterFields(), row.defaultSort(), row.formSections(),
				"desktop");
	}

	private CustomPermissionRequest toPermissionRequest(PermissionRow row) {
		return new CustomPermissionRequest(row.view(), row.create(), row.update(), row.delete());
	}

	private CustomFieldData toFieldData(FieldRow row) {
		return new CustomFieldData(row.id(), row.label(), row.fieldKey(), row.type(), row.required(), row.filterable(),
				row.sortable(), row.searchable(), row.order(), row.helperText(), row.options(), row.reference(),
				row.validation(), row.defaultValue(), false, false, row.status());
	}

	private CustomMenuPageData toPageData(PageRow row, ValidationSummaryData summary) {
		return new CustomMenuPageData("page", String.valueOf(row.id()), row.key(), row.label(), row.icon(),
				row.parentKey(), row.routePath(), row.entityKey(), row.pageType(), row.status(), row.sortOrder(),
				row.description(), parseRoles(row.rolesJson()), row.entityPermission(), row.dataPermission(),
				row.draftVersion(), row.draftVersion(), row.publishedVersion(),
				hasDraft(row.draftVersion(), row.publishedVersion()), row.publishedAt(), null, row.updatedAt(), null,
				row.etag(), summary);
	}

	private PageRow findPage(String pageKey) {
		return menuRepository.findPage(pageKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, NOT_FOUND_PAGE));
	}

	private EntityRow findEntity(String entityKey) {
		if (!StringUtils.hasText(entityKey)) {
			throw new BusinessException(ApiErrorCode.NOT_FOUND, NOT_FOUND_ENTITY);
		}
		return entityRepository.findEntity(entityKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, NOT_FOUND_ENTITY));
	}

	private ViewRow emptyView(String entityKey) {
		return new ViewRow(entityKey, objectMapper.createArrayNode(), objectMapper.createArrayNode(), null,
				objectMapper.createArrayNode());
	}

	private List<String> parseRoles(String json) {
		if (!StringUtils.hasText(json)) {
			return List.of();
		}
		try {
			List<String> parsed = objectMapper.readValue(json, LIST_OF_STRING);
			return parsed == null ? List.of() : parsed;
		}
		catch (Exception ex) {
			return List.of();
		}
	}

	private static boolean hasDraft(int draftVersion, Integer publishedVersion) {
		return publishedVersion == null || draftVersion > publishedVersion;
	}

	private static String suppliedEtag(CustomBuilderBundleRequest request) {
		if (StringUtils.hasText(request.etag())) {
			return request.etag();
		}
		return request.menuPage().etag();
	}

	private static void assertEtag(String current, String supplied) {
		if (!StringUtils.hasText(supplied) || !supplied.equals(current)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, STALE);
		}
	}
}
