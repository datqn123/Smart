package com.example.smart_erp.custominterface.service;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.custominterface.dto.CustomBuilderBundleRequest;
import com.example.smart_erp.custominterface.dto.CustomFieldRequest;
import com.example.smart_erp.custominterface.dto.CustomPageRequest;
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

	private static final Pattern KEY_PATTERN = Pattern.compile("^[a-z0-9_]+$");
	private static final Set<String> PAGE_TYPES = Set.of("record_list", "form", "table_detail");
	private static final Set<String> ROLES = Set.of("Owner", "Admin", "Staff", "Warehouse");
	private static final TypeReference<List<String>> LIST_OF_STRING = new TypeReference<>() {
	};

	private static final String BAD_REQUEST = "Dữ liệu không hợp lệ. Vui lòng kiểm tra lại các trường được đánh dấu.";
	private static final String CONFLICT = "Mã hoặc route đã được sử dụng. Vui lòng chọn giá trị khác.";
	private static final String NOT_FOUND_PAGE = "Không tìm thấy giao diện tùy chỉnh.";
	private static final String NOT_FOUND_PUBLISHED_PAGE =
			"Không tìm thấy giao diện tùy chỉnh hoặc giao diện chưa được publish.";
	private static final String NOT_FOUND_ENTITY = "Không tìm thấy entity tùy chỉnh.";
	private static final String FORBIDDEN = "Bạn không có quyền thực hiện thao tác này.";
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

	@Transactional(readOnly = true)
	public CustomBuilderBundleData runtimeBundle(String pageKey, Authentication authentication, Jwt jwt) {
		PageRow page = menuRepository.findPublishedPage(pageKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, NOT_FOUND_PUBLISHED_PAGE));
		String role = jwt.getClaimAsString("role");
		if (!roleAllowed(parseRoles(page.rolesJson()), role) || !permissionAllowed(page.entityPermission(), authentication)
				|| !permissionAllowed(page.dataPermission(), authentication)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, FORBIDDEN);
		}
		EntityRow entity = findEntity(page.entityKey());
		return toBundle(page, entity, ValidationSummaryData.ok());
	}

	@Transactional
	public CustomBuilderBundleData saveBundle(String pageKey, CustomBuilderBundleRequest request, Jwt jwt) {
		if (request == null || request.menuPage() == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST);
		}
		PageRow page = findPage(pageKey);
		EntityRow entity = findEntity(page.entityKey());
		assertEtag(page.etag(), suppliedEtag(request));
		assertRequestIdentity(request, page);
		String entityLabel = normalizedEntityLabel(request.entityLabel());
		PageDraftMetadata menuPage = validatePageMetadata(request.menuPage(), page);

		ValidationSummaryData draftSummary = validator.validateDraft(request.menuPage().key(), request.entityKey(),
				request.fields(), request.views(), request.permissions());
		if (!draftSummary.valid()) {
			return toBundle(page, entity, draftSummary);
		}

		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		try {
			PageRow updatedPage = menuRepository.updateBuilderPageDraft(page, menuPage.parentKey(), menuPage.label(),
					menuPage.icon(), menuPage.description(), menuPage.routePath(), menuPage.pageType(),
					menuPage.rolesJson(), menuPage.entityPermission(), menuPage.dataPermission(), menuPage.sortOrder(),
					userId);
			entityRepository.replaceBundle(entity, entityLabel, request.entityDescription(), request.fields(),
					request.views(), request.permissions(), userId);
			EntityRow updatedEntity = findEntity(entity.key());
			return toBundle(updatedPage, updatedEntity, validate(updatedPage, updatedEntity));
		}
		catch (OptimisticLockingFailureException ex) {
			throw staleConflict();
		}
	}

	private PageDraftMetadata validatePageMetadata(CustomPageRequest req, PageRow page) {
		String parentKey = requireKey(req.parentKey(), "parentKey");
		menuRepository.findFolder(parentKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST,
						Map.of("parentKey", "Danh mục menu cha không tồn tại.")));
		String label = requireText(req.label(), "label", "Tên giao diện không được để trống.");
		String routePath = requireRoute(req.routePath());
		if (menuRepository.routeExists(routePath, page.id())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, CONFLICT, Map.of("routePath", "Route đã được sử dụng."));
		}
		return new PageDraftMetadata(parentKey, label, clean(req.icon()), clean(req.description()), routePath,
				requirePageType(req.pageType()), rolesJson(req.visibilityRoles()), clean(req.entityPermission()),
				clean(req.dataPermission()), req.sortOrder() == null ? page.sortOrder() : req.sortOrder());
	}

	private void validateCurrentPageMetadata(PageRow page) {
		validatePageMetadata(new CustomPageRequest(page.parentKey(), page.key(), page.label(), page.icon(),
				page.description(), page.routePath(), page.entityKey(), page.pageType(),
				parseRolesForValidation(page.rolesJson()), page.entityPermission(), page.dataPermission(),
				page.sortOrder(), page.etag()), page);
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
		assertEtag(page.etag(), etag);
		validateCurrentPageMetadata(page);
		EntityRow entity = findEntity(page.entityKey());
		ValidationSummaryData summary = validate(page, entity);
		if (!summary.valid()) {
			throw new BusinessException(ApiErrorCode.UNPROCESSABLE_ENTITY, PUBLISH_INVALID);
		}
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		try {
			entityRepository.publishSnapshot(page.key(), entity, userId);
			menuRepository.publishPage(page, userId);
		}
		catch (OptimisticLockingFailureException ex) {
			throw staleConflict();
		}

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

	private List<String> parseRolesForValidation(String json) {
		if (!StringUtils.hasText(json)) {
			return List.of();
		}
		try {
			List<String> parsed = objectMapper.readValue(json, LIST_OF_STRING);
			return parsed == null ? List.of() : parsed;
		}
		catch (Exception ex) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST,
					Map.of("visibilityRoles", "Role không hợp lệ."));
		}
	}

	private String rolesJson(List<String> roles) {
		List<String> normalized = normalizeRoles(roles);
		try {
			return objectMapper.writeValueAsString(normalized);
		}
		catch (Exception ex) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST);
		}
	}

	private static List<String> normalizeRoles(List<String> roles) {
		if (roles == null || roles.isEmpty()) {
			return List.of("Owner", "Admin");
		}
		Set<String> out = new LinkedHashSet<>();
		for (String role : roles) {
			String value = clean(role);
			if (!StringUtils.hasText(value) || !ROLES.contains(value)) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST,
						Map.of("visibilityRoles", "Role không hợp lệ."));
			}
			out.add(value);
		}
		return List.copyOf(out);
	}

	private static String requireKey(String raw, String field) {
		String key = clean(raw);
		if (!StringUtils.hasText(key)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST, Map.of(field, "Bắt buộc"));
		}
		if (!KEY_PATTERN.matcher(key).matches()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST,
					Map.of(field, "Mã chỉ gồm chữ thường, số và dấu gạch dưới."));
		}
		return key;
	}

	private static String requireText(String raw, String field, String message) {
		String value = clean(raw);
		if (!StringUtils.hasText(value)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST, Map.of(field, message));
		}
		return value;
	}

	private static String requireRoute(String raw) {
		String route = clean(raw);
		if (!StringUtils.hasText(route)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST,
					Map.of("routePath", "Route không được để trống."));
		}
		if (!route.startsWith("/custom/")) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST,
					Map.of("routePath", "Route phải bắt đầu bằng /custom/."));
		}
		return route;
	}

	private static String requirePageType(String raw) {
		String value = clean(raw);
		if (!PAGE_TYPES.contains(value)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST,
					Map.of("pageType", "Loại giao diện không hợp lệ."));
		}
		return value;
	}

	private static boolean hasDraft(int draftVersion, Integer publishedVersion) {
		return publishedVersion == null || draftVersion > publishedVersion;
	}

	private static boolean roleAllowed(List<String> roles, String role) {
		if (roles == null || roles.isEmpty() || !StringUtils.hasText(role)) {
			return true;
		}
		return roles.stream().anyMatch(r -> r.equalsIgnoreCase(role.trim()));
	}

	private static boolean permissionAllowed(String permission, Authentication authentication) {
		return !StringUtils.hasText(permission) || hasAuthority(authentication, permission);
	}

	private static boolean hasAuthority(Authentication authentication, String permission) {
		if (authentication == null || !StringUtils.hasText(permission)) {
			return false;
		}
		return authentication.getAuthorities().stream().anyMatch(ga -> permission.equals(ga.getAuthority()));
	}

	private static String suppliedEtag(CustomBuilderBundleRequest request) {
		if (StringUtils.hasText(request.etag())) {
			return request.etag();
		}
		return request.menuPage().etag();
	}

	private static void assertRequestIdentity(CustomBuilderBundleRequest request, PageRow page) {
		if (!page.key().equals(request.menuPage().key()) || !page.entityKey().equals(request.entityKey())
				|| !page.entityKey().equals(request.menuPage().entityKey())) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST);
		}
	}

	private static String normalizedEntityLabel(String label) {
		if (!StringUtils.hasText(label)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST);
		}
		return label.trim();
	}

	private static String trim(String raw) {
		return raw == null ? null : raw.trim();
	}

	private static String clean(String raw) {
		String value = trim(raw);
		return StringUtils.hasText(value) ? value : null;
	}

	private static void assertEtag(String current, String supplied) {
		if (!StringUtils.hasText(supplied) || !supplied.equals(current)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, STALE);
		}
	}

	private static BusinessException staleConflict() {
		return new BusinessException(ApiErrorCode.CONFLICT, STALE);
	}

	private record PageDraftMetadata(String parentKey, String label, String icon, String description, String routePath,
			String pageType, String rolesJson, String entityPermission, String dataPermission, int sortOrder) {
	}
}
