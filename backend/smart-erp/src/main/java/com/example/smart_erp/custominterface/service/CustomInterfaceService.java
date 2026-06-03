package com.example.smart_erp.custominterface.service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.custominterface.dto.CustomFolderRequest;
import com.example.smart_erp.custominterface.dto.CustomPageRequest;
import com.example.smart_erp.custominterface.dto.CustomPublishRequest;
import com.example.smart_erp.custominterface.dto.CustomReorderRequest;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository.FolderRow;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository.PageRow;
import com.example.smart_erp.custominterface.response.CustomMenuFolderData;
import com.example.smart_erp.custominterface.response.CustomMenuPageData;
import com.example.smart_erp.custominterface.response.CustomMenuTreeData;
import com.example.smart_erp.custominterface.response.ValidationSummaryData;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class CustomInterfaceService {

	private static final Pattern KEY_PATTERN = Pattern.compile("^[a-z0-9_]+$");
	private static final Set<String> PAGE_TYPES = Set.of("record_list", "form", "table_detail");
	private static final Set<String> ROLES = Set.of("Owner", "Admin", "Staff", "Warehouse");
	private static final TypeReference<List<String>> LIST_OF_STRING = new TypeReference<>() {
	};

	private static final String BAD_REQUEST = "Dữ liệu không hợp lệ. Vui lòng kiểm tra lại các trường được đánh dấu.";
	private static final String CONFLICT = "Mã hoặc route đã được sử dụng. Vui lòng chọn giá trị khác.";
	private static final String STALE = "Cấu hình đã được cập nhật bởi người khác. Vui lòng tải lại trước khi lưu.";
	private static final String NOT_FOUND_PAGE = "Không tìm thấy giao diện tùy chỉnh hoặc giao diện chưa được publish.";

	private final CustomInterfaceJdbcRepository repository;
	private final ObjectMapper objectMapper;

	public CustomInterfaceService(CustomInterfaceJdbcRepository repository, ObjectMapper objectMapper) {
		this.repository = repository;
		this.objectMapper = objectMapper;
	}

	@Transactional(readOnly = true)
	public CustomMenuTreeData menuTree() {
		return tree(repository.findActiveFolders(), repository.findActivePages());
	}

	@Transactional
	public CustomMenuTreeData createFolder(CustomFolderRequest req, Jwt jwt) {
		if (req == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST);
		}
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		String key = requireKey(req.key(), "key");
		String label = requireText(req.label(), "label", "Tên danh mục không được để trống.");
		if (repository.folderKeyExists(key, null) || repository.pageKeyExists(key, null)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, CONFLICT, Map.of("key", "Mã danh mục đã tồn tại."));
		}
		repository.insertFolder(key, label, clean(req.icon()), clean(req.description()), rolesJson(req.visibilityRoles()),
				req.sortOrder() == null ? repository.findActiveFolders().size() : req.sortOrder(), userId);
		repository.event("folder", key, "create", userId);
		return menuTree();
	}

	@Transactional
	public CustomMenuTreeData updateFolder(String folderKey, CustomFolderRequest req, Jwt jwt) {
		if (req == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST);
		}
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		FolderRow current = repository.findFolder(folderKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy danh mục menu."));
		assertEtag(current.etag(), req == null ? null : req.etag());
		String key = requireKey(req.key(), "key");
		String label = requireText(req.label(), "label", "Tên danh mục không được để trống.");
		if (repository.folderKeyExists(key, current.id()) || repository.pageKeyExists(key, null)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, CONFLICT, Map.of("key", "Mã danh mục đã tồn tại."));
		}
		repository.updateFolder(current, key, label, clean(req.icon()), clean(req.description()),
				rolesJson(req.visibilityRoles()), req.sortOrder() == null ? current.sortOrder() : req.sortOrder(), userId);
		repository.event("folder", key, "update", userId);
		return menuTree();
	}

	@Transactional
	public CustomMenuTreeData createPage(CustomPageRequest req, Jwt jwt) {
		if (req == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST);
		}
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		String parentKey = requireKey(req.parentKey(), "parentKey");
		FolderRow parent = repository.findFolder(parentKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST,
						Map.of("parentKey", "Danh mục menu cha không tồn tại.")));
		String key = requireKey(req.key(), "key");
		String routePath = requireRoute(req.routePath());
		validatePageUniqueness(key, routePath, null);
		String pageType = requirePageType(req.pageType());
		repository.insertPage(parent.key(), key, requireText(req.label(), "label", "Tên giao diện không được để trống."),
				clean(req.icon()), clean(req.description()), routePath, requireText(req.entityKey(), "entityKey",
						"Entity liên kết không được để trống."),
				pageType, rolesJson(req.visibilityRoles()), clean(req.entityPermission()), clean(req.dataPermission()),
				req.sortOrder() == null ? repository.findActivePages().stream()
						.filter(p -> parent.key().equals(p.parentKey())).toList().size() : req.sortOrder(),
				userId);
		repository.event("page", key, "create", userId);
		return menuTree();
	}

	@Transactional
	public CustomMenuTreeData updatePage(String pageKey, CustomPageRequest req, Jwt jwt) {
		if (req == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST);
		}
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		PageRow current = repository.findPage(pageKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy giao diện tùy chỉnh."));
		assertEtag(current.etag(), req == null ? null : req.etag());
		String parentKey = requireKey(req.parentKey(), "parentKey");
		FolderRow parent = repository.findFolder(parentKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST,
						Map.of("parentKey", "Danh mục menu cha không tồn tại.")));
		String key = requireKey(req.key(), "key");
		String routePath = requireRoute(req.routePath());
		validatePageUniqueness(key, routePath, current.id());
		repository.updatePage(current, parent.key(), key,
				requireText(req.label(), "label", "Tên giao diện không được để trống."),
				clean(req.icon()), clean(req.description()), routePath,
				requireText(req.entityKey(), "entityKey", "Entity liên kết không được để trống."),
				requirePageType(req.pageType()), rolesJson(req.visibilityRoles()), clean(req.entityPermission()),
				clean(req.dataPermission()), req.sortOrder() == null ? current.sortOrder() : req.sortOrder(), userId);
		repository.event("page", key, "update", userId);
		return menuTree();
	}

	@Transactional
	public CustomMenuTreeData reorder(CustomReorderRequest req, Jwt jwt) {
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		if (req == null || req.folders() == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST, Map.of("folders", "Bắt buộc"));
		}
		assertTreeEtag(req.etag());
		Set<String> folderKeys = repository.findActiveFolders().stream().map(FolderRow::key).collect(Collectors.toSet());
		Set<String> pageKeys = repository.findActivePages().stream().map(PageRow::key).collect(Collectors.toSet());
		for (CustomReorderRequest.FolderOrder folder : req.folders()) {
			String key = requireKey(folder.key(), "folders.key");
			if (!folderKeys.contains(key)) {
				throw new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy danh mục menu.");
			}
			repository.updateFolderOrder(key, folder.sortOrder() == null ? 0 : folder.sortOrder(), userId);
			if (folder.pages() != null) {
				for (CustomReorderRequest.PageOrder page : folder.pages()) {
					String pageKey = requireKey(page.key(), "pages.key");
					if (!pageKeys.contains(pageKey)) {
						throw new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy giao diện tùy chỉnh.");
					}
					repository.updatePageOrder(pageKey, page.sortOrder() == null ? 0 : page.sortOrder(), userId);
				}
			}
		}
		repository.event("menu", "tree", "reorder", userId);
		return menuTree();
	}

	@Transactional(readOnly = true)
	public ValidationSummaryData validatePublish() {
		List<ValidationSummaryData.Item> errors = new ArrayList<>();
		for (PageRow page : repository.findActivePages()) {
			if (!StringUtils.hasText(page.entityKey())) {
				errors.add(new ValidationSummaryData.Item("data", "Entity liên kết không được để trống.", page.key()));
			}
			if (!StringUtils.hasText(page.routePath()) || !page.routePath().startsWith("/custom/")) {
				errors.add(new ValidationSummaryData.Item("runtime", "Route phải bắt đầu bằng /custom/.", page.key()));
			}
		}
		return new ValidationSummaryData(errors.isEmpty(), errors, List.of());
	}

	@Transactional
	public CustomMenuTreeData publish(CustomPublishRequest req, Jwt jwt) {
		assertTreeEtag(req == null ? null : req.etag());
		ValidationSummaryData summary = validatePublish();
		if (!summary.valid()) {
			throw new BusinessException(ApiErrorCode.UNPROCESSABLE_ENTITY,
					"Cấu hình chưa hợp lệ để publish. Vui lòng kiểm tra các cảnh báo.",
					Map.of("validation", "failed"));
		}
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		repository.publishAll(userId);
		repository.event("menu", "tree", "publish", userId);
		return menuTree();
	}

	@Transactional
	public CustomMenuTreeData archiveFolder(String folderKey, Jwt jwt) {
		FolderRow folder = repository.findFolder(folderKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy danh mục menu."));
		if (repository.countPublishedPagesInFolder(folder.key()) > 0) {
			throw new BusinessException(ApiErrorCode.CONFLICT,
					"Không thể ẩn danh mục vì vẫn còn giao diện đã publish bên trong.");
		}
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		repository.archiveFolder(folder.key(), userId);
		repository.event("folder", folder.key(), "archive", userId);
		return menuTree();
	}

	@Transactional
	public CustomMenuTreeData archivePage(String pageKey, Jwt jwt) {
		PageRow page = repository.findPage(pageKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy giao diện tùy chỉnh."));
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		repository.archivePage(page.key(), userId);
		repository.event("page", page.key(), "archive", userId);
		return menuTree();
	}

	@Transactional(readOnly = true)
	public CustomMenuTreeData runtimeMenu(Authentication authentication, Jwt jwt) {
		if (!hasAuthority(authentication, "can_use_custom_entities")
				&& !hasAuthority(authentication, "can_manage_custom_builder")) {
			return new CustomMenuTreeData("runtime-empty", List.of());
		}
		CustomMenuTreeData all = tree(repository.findActiveFolders(), repository.findActivePages());
		String role = jwt.getClaimAsString("role");
		List<CustomMenuFolderData> folders = all.folders().stream()
				.filter(folder -> "Published".equals(folder.status()) && roleAllowed(folder.roles(), role))
				.map(folder -> {
					List<CustomMenuPageData> pages = folder.children().stream()
							.filter(page -> pageVisible(page, role, authentication))
							.toList();
					return new CustomMenuFolderData(folder.nodeType(), folder.id(), folder.key(), folder.label(),
							folder.icon(), folder.description(), folder.status(), folder.sortOrder(), folder.roles(),
							folder.version(), folder.draftVersion(), folder.publishedVersion(), folder.hasDraft(),
							folder.publishedAt(), folder.publishedByName(), folder.updatedAt(), folder.updatedByName(),
							folder.etag(), folder.validationSummary(), pages);
				})
				.filter(folder -> !folder.children().isEmpty())
				.toList();
		return new CustomMenuTreeData("runtime-" + folders.size(), folders);
	}

	@Transactional(readOnly = true)
	public CustomMenuTreeData runtimePage(String pageKey, Authentication authentication, Jwt jwt) {
		PageRow page = repository.findPublishedPage(pageKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, NOT_FOUND_PAGE));
		FolderRow folder = repository.findFolder(page.parentKey())
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, NOT_FOUND_PAGE));
		CustomMenuPageData pageData = toPageData(page);
		String role = jwt.getClaimAsString("role");
		if (!"Published".equals(folder.status()) || !roleAllowed(parseRoles(folder.rolesJson()), role)
				|| !pageVisible(pageData, role, authentication)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Bạn không có quyền thực hiện thao tác này.");
		}
		CustomMenuFolderData folderData = toFolderData(folder, List.of(pageData));
		return new CustomMenuTreeData("runtime-page-" + page.key(), List.of(folderData));
	}

	private CustomMenuTreeData tree(List<FolderRow> folders, List<PageRow> pages) {
		Map<String, List<CustomMenuPageData>> pagesByParent = new LinkedHashMap<>();
		for (PageRow page : pages) {
			pagesByParent.computeIfAbsent(page.parentKey(), ignored -> new ArrayList<>()).add(toPageData(page));
		}
		List<CustomMenuFolderData> out = folders.stream()
				.map(folder -> toFolderData(folder, pagesByParent.getOrDefault(folder.key(), List.of())))
				.toList();
		String signature = folders.stream()
				.map(folder -> String.join(":", folder.key(), folder.status(), String.valueOf(folder.sortOrder()), folder.etag()))
				.collect(Collectors.joining("|"))
				+ "#"
				+ pages.stream()
						.map(page -> String.join(":", page.key(), page.parentKey(), page.status(),
								String.valueOf(page.sortOrder()), page.routePath(), page.etag()))
						.collect(Collectors.joining("|"));
		return new CustomMenuTreeData("tree-draft-" + Integer.toHexString(signature.hashCode()), out);
	}

	private CustomMenuFolderData toFolderData(FolderRow row, List<CustomMenuPageData> children) {
		return new CustomMenuFolderData("folder", String.valueOf(row.id()), row.key(), row.label(), row.icon(),
				row.description(), row.status(), row.sortOrder(), parseRoles(row.rolesJson()), row.draftVersion(),
				row.draftVersion(), row.publishedVersion(), hasDraft(row.draftVersion(), row.publishedVersion()),
				row.publishedAt(), null, row.updatedAt(), null, row.etag(), ValidationSummaryData.ok(), children);
	}

	private CustomMenuPageData toPageData(PageRow row) {
		return new CustomMenuPageData("page", String.valueOf(row.id()), row.key(), row.label(), row.icon(),
				row.parentKey(), row.routePath(), row.entityKey(), row.pageType(), row.status(), row.sortOrder(),
				row.description(), parseRoles(row.rolesJson()), row.entityPermission(), row.dataPermission(),
				row.draftVersion(), row.draftVersion(), row.publishedVersion(),
				hasDraft(row.draftVersion(), row.publishedVersion()), row.publishedAt(), null, row.updatedAt(), null,
				row.etag(), ValidationSummaryData.ok());
	}

	private boolean pageVisible(CustomMenuPageData page, String role, Authentication authentication) {
		return "Published".equals(page.status()) && roleAllowed(page.roles(), role)
				&& permissionAllowed(page.entityPermission(), authentication)
				&& permissionAllowed(page.dataPermission(), authentication);
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
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, BAD_REQUEST, Map.of("routePath", "Route không được để trống."));
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

	private void validatePageUniqueness(String key, String routePath, Long exceptId) {
		if (repository.pageKeyExists(key, exceptId) || repository.folderKeyExists(key, null)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, CONFLICT, Map.of("key", "Mã giao diện đã tồn tại."));
		}
		if (repository.routeExists(routePath, exceptId)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, CONFLICT, Map.of("routePath", "Route đã được sử dụng."));
		}
	}

	private static void assertEtag(String current, String supplied) {
		if (!StringUtils.hasText(supplied) || !current.equals(supplied)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, STALE);
		}
	}

	private void assertTreeEtag(String supplied) {
		String current = menuTree().treeEtag();
		if (!StringUtils.hasText(supplied) || !current.equals(supplied)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, STALE);
		}
	}

	private static String clean(String raw) {
		if (raw == null) {
			return null;
		}
		String value = raw.trim();
		return value.isEmpty() ? null : value;
	}
}
