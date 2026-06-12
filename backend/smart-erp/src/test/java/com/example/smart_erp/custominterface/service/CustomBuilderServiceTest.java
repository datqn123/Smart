package com.example.smart_erp.custominterface.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.catchThrowable;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.security.oauth2.jwt.Jwt;

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
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository.FolderRow;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository.PageRow;
import com.fasterxml.jackson.databind.ObjectMapper;

@ExtendWith(MockitoExtension.class)
class CustomBuilderServiceTest {

	private static final String PAGE_KEY = "kiem_hang_page";
	private static final String ENTITY_KEY = "kiem_hang_entity";
	private static final String PAGE_ETAG = "page-kiem_hang_page-draft-1";

	@Mock
	private CustomEntityJdbcRepository entityRepository;

	@Mock
	private CustomInterfaceJdbcRepository menuRepository;

	private ObjectMapper mapper;
	private CustomBuilderService service;

	@BeforeEach
	void setUp() {
		mapper = new ObjectMapper();
		service = new CustomBuilderService(entityRepository, menuRepository, new CustomMetadataValidator(mapper), mapper);
	}

	@Test
	void saveBundle_updatesPageDraftMetadataAndReturnsUpdatedEtag() {
		var request = requestWithMenuPage(builderMenuPage(PAGE_ETAG), "  Kiểm hàng  ");
		var page = pageRow();
		var updatedPage = builderPageRow();
		var currentEntity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");
		var savedEntity = entityRow(2, null, "NeedsConfig", "entity-kiem_hang_entity-draft-2");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(menuRepository.findFolder("kiem_hang_moi")).thenReturn(Optional.of(folderRow("kiem_hang_moi")));
		when(menuRepository.routeExists("/custom/kiem-hang-moi", page.id())).thenReturn(false);
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(currentEntity), Optional.of(savedEntity));
		when(menuRepository.updateBuilderPageDraft(page, "kiem_hang_moi", "Kiểm hàng mới", "package-check",
				"Màn hình kiểm hàng mới", "/custom/kiem-hang-moi", "table_detail", "[\"Admin\",\"Staff\"]",
				"can_manage_custom_builder", "can_view_inventory", 12, 7)).thenReturn(updatedPage);
		when(entityRepository.replaceBundle(eq(currentEntity), eq("Kiểm hàng"), eq("Desc"), eq(request.fields()),
				eq(request.views()), eq(request.permissions()), eq(7))).thenReturn(savedEntity);
		when(entityRepository.findFields(ENTITY_KEY)).thenReturn(fieldRows());
		when(entityRepository.findView(ENTITY_KEY)).thenReturn(Optional.of(viewRow(request.views())));
		when(entityRepository.findPermissions(ENTITY_KEY)).thenReturn(permissionRow());

		var saved = service.saveBundle(PAGE_KEY, request, jwt());

		assertThat(saved.validationSummary().valid()).isTrue();
		assertThat(saved.etag()).isEqualTo(updatedPage.etag());
		assertThat(saved.menuPage().etag()).isEqualTo(updatedPage.etag());
		assertThat(saved.menuPage().parentKey()).isEqualTo("kiem_hang_moi");
		assertThat(saved.menuPage().label()).isEqualTo("Kiểm hàng mới");
		assertThat(saved.menuPage().icon()).isEqualTo("package-check");
		assertThat(saved.menuPage().description()).isEqualTo("Màn hình kiểm hàng mới");
		assertThat(saved.menuPage().routePath()).isEqualTo("/custom/kiem-hang-moi");
		assertThat(saved.menuPage().pageType()).isEqualTo("table_detail");
		assertThat(saved.menuPage().roles()).containsExactly("Admin", "Staff");
		assertThat(saved.menuPage().entityPermission()).isEqualTo("can_manage_custom_builder");
		assertThat(saved.menuPage().dataPermission()).isEqualTo("can_view_inventory");
		assertThat(saved.menuPage().sortOrder()).isEqualTo(12);
		assertThat(saved.entityDefinition().etag()).isEqualTo("entity-kiem_hang_entity-draft-2");
		verify(menuRepository).updateBuilderPageDraft(page, "kiem_hang_moi", "Kiểm hàng mới", "package-check",
				"Màn hình kiểm hàng mới", "/custom/kiem-hang-moi", "table_detail", "[\"Admin\",\"Staff\"]",
				"can_manage_custom_builder", "can_view_inventory", 12, 7);
		verify(entityRepository).replaceBundle(eq(currentEntity), eq("Kiểm hàng"), eq("Desc"), eq(request.fields()),
				eq(request.views()), eq(request.permissions()), eq(7));
	}

	@Test
	void saveBundle_pageMetadataConflictThrowsConflictAndSkipsEntityReplace() {
		var request = validRequest(PAGE_ETAG);
		var page = pageRow();
		var entity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(menuRepository.findFolder("kiem_hang")).thenReturn(Optional.of(folderRow("kiem_hang")));
		when(menuRepository.routeExists("/custom/kiem_hang_page", page.id())).thenReturn(false);
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(entity));
		when(menuRepository.updateBuilderPageDraft(page, "kiem_hang", "Kiểm hàng", null, null,
				"/custom/kiem_hang_page", "record_list", "[\"Owner\"]", null, null, 0, 7))
				.thenThrow(new OptimisticLockingFailureException("stale"));

		Throwable thrown = catchThrowable(() -> service.saveBundle(PAGE_KEY, request, jwt()));

		assertThat(thrown).isInstanceOf(BusinessException.class);
		assertThat(((BusinessException) thrown).getCode()).isEqualTo(ApiErrorCode.CONFLICT);
		verify(entityRepository, never()).replaceBundle(any(), any(), any(), any(), any(), any(), any());
	}

	@Test
	void saveBundle_mismatchedRequestPageKeyThrowsBadRequestAndSkipsPersist() {
		assertBadRequestDoesNotPersist(requestWithMenuPage(menuPageWithKey("other_page")));
	}

	@Test
	void saveBundle_mismatchedRequestEntityKeyThrowsBadRequestAndSkipsPersist() {
		assertBadRequestDoesNotPersist(requestWithEntityKey("other_entity"));
	}

	@Test
	void saveBundle_mismatchedRequestMenuPageEntityKeyThrowsBadRequestAndSkipsPersist() {
		assertBadRequestDoesNotPersist(requestWithMenuPage(menuPageWithEntityKey("other_entity")));
	}

	@Test
	void saveBundle_nullEntityLabelThrowsBadRequestAndSkipsPersist() {
		assertBadRequestDoesNotPersist(requestWithEntityLabel(null));
	}

	@Test
	void saveBundle_blankEntityLabelThrowsBadRequestAndSkipsPersist() {
		assertBadRequestDoesNotPersist(requestWithEntityLabel("   "));
	}

	@Test
	void saveBundle_blankPageLabelThrowsBadRequestAndSkipsPersist() {
		assertBadRequestDoesNotPersistAfterKnownParent(requestWithMenuPage(menuPageWithLabel("   ")));
	}

	@Test
	void saveBundle_routeOutsideCustomPrefixThrowsBadRequestAndSkipsPersist() {
		assertBadRequestDoesNotPersistAfterKnownParent(requestWithMenuPage(menuPageWithRoute("/inventory/checks")));
	}

	@Test
	void saveBundle_duplicateRouteThrowsConflictAndSkipsPersist() {
		var request = validRequest(PAGE_ETAG);
		var page = pageRow();
		var entity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(entity));
		when(menuRepository.findFolder("kiem_hang")).thenReturn(Optional.of(folderRow("kiem_hang")));
		when(menuRepository.routeExists("/custom/kiem_hang_page", page.id())).thenReturn(true);

		Throwable thrown = catchThrowable(() -> service.saveBundle(PAGE_KEY, request, jwt()));

		assertThat(thrown).isInstanceOf(BusinessException.class);
		assertThat(((BusinessException) thrown).getCode()).isEqualTo(ApiErrorCode.CONFLICT);
		verify(menuRepository, never()).updateBuilderPageDraft(any(), any(), any(), any(), any(), any(), any(), any(),
				any(), any(), anyInt(), eq(7));
		verify(entityRepository, never()).replaceBundle(any(), any(), any(), any(), any(), any(), any());
	}

	@Test
	void saveBundle_invalidPageTypeThrowsBadRequestAndSkipsPersist() {
		assertBadRequestDoesNotPersistAfterKnownRoute(requestWithMenuPage(menuPageWithPageType("chart")));
	}

	@Test
	void saveBundle_missingParentFolderThrowsBadRequestAndSkipsPersist() {
		var request = validRequest(PAGE_ETAG);
		var page = pageRow();
		var entity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(entity));
		when(menuRepository.findFolder("kiem_hang")).thenReturn(Optional.empty());

		Throwable thrown = catchThrowable(() -> service.saveBundle(PAGE_KEY, request, jwt()));

		assertThat(thrown).isInstanceOf(BusinessException.class);
		assertThat(((BusinessException) thrown).getCode()).isEqualTo(ApiErrorCode.BAD_REQUEST);
		verify(menuRepository, never()).updateBuilderPageDraft(any(), any(), any(), any(), any(), any(), any(), any(),
				any(), any(), anyInt(), eq(7));
		verify(entityRepository, never()).replaceBundle(any(), any(), any(), any(), any(), any(), any());
	}

	@Test
	void saveBundle_invalidVisibilityRoleThrowsBadRequestAndSkipsPersist() {
		assertBadRequestDoesNotPersistAfterKnownRoute(
				requestWithMenuPage(menuPageWithVisibilityRoles(List.of("Admin", "Guest"))));
	}

	@Test
	void saveBundle_emptyVisibilityRolesDefaultToOwnerAdminWhenSaving() {
		var request = requestWithMenuPage(menuPageWithVisibilityRoles(List.of()));
		var page = pageRow();
		var updatedPage = new PageRow(1L, PAGE_KEY, "kiem_hang", "Kiểm hàng", null, null, "/custom/" + PAGE_KEY,
				ENTITY_KEY, "record_list", "NeedsConfig", 0, "[\"Owner\",\"Admin\"]", null, null, 2, null,
				"page-kiem_hang_page-draft-2", null, null);
		var currentEntity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");
		var savedEntity = entityRow(2, null, "NeedsConfig", "entity-kiem_hang_entity-draft-2");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(menuRepository.findFolder("kiem_hang")).thenReturn(Optional.of(folderRow("kiem_hang")));
		when(menuRepository.routeExists("/custom/kiem_hang_page", page.id())).thenReturn(false);
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(currentEntity), Optional.of(savedEntity));
		when(menuRepository.updateBuilderPageDraft(page, "kiem_hang", "Kiểm hàng", null, null,
				"/custom/kiem_hang_page", "record_list", "[\"Owner\",\"Admin\"]", null, null, 0, 7))
				.thenReturn(updatedPage);
		when(entityRepository.replaceBundle(eq(currentEntity), eq("Kiểm hàng"), eq("Desc"), eq(request.fields()),
				eq(request.views()), eq(request.permissions()), eq(7))).thenReturn(savedEntity);
		when(entityRepository.findFields(ENTITY_KEY)).thenReturn(fieldRows());
		when(entityRepository.findView(ENTITY_KEY)).thenReturn(Optional.of(viewRow(request.views())));
		when(entityRepository.findPermissions(ENTITY_KEY)).thenReturn(permissionRow());

		var saved = service.saveBundle(PAGE_KEY, request, jwt());

		assertThat(saved.menuPage().roles()).containsExactly("Owner", "Admin");
		verify(menuRepository).updateBuilderPageDraft(page, "kiem_hang", "Kiểm hàng", null, null,
				"/custom/kiem_hang_page", "record_list", "[\"Owner\",\"Admin\"]", null, null, 0, 7);
	}

	@Test
	void saveBundle_nullVisibilityRolesDefaultToOwnerAdminWhenSaving() {
		var request = requestWithMenuPage(menuPageWithVisibilityRoles(null));
		var page = pageRow();
		var updatedPage = new PageRow(1L, PAGE_KEY, "kiem_hang", "Kiểm hàng", null, null, "/custom/" + PAGE_KEY,
				ENTITY_KEY, "record_list", "NeedsConfig", 0, "[\"Owner\",\"Admin\"]", null, null, 2, null,
				"page-kiem_hang_page-draft-2", null, null);
		var currentEntity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");
		var savedEntity = entityRow(2, null, "NeedsConfig", "entity-kiem_hang_entity-draft-2");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(menuRepository.findFolder("kiem_hang")).thenReturn(Optional.of(folderRow("kiem_hang")));
		when(menuRepository.routeExists("/custom/kiem_hang_page", page.id())).thenReturn(false);
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(currentEntity), Optional.of(savedEntity));
		when(menuRepository.updateBuilderPageDraft(page, "kiem_hang", "Kiểm hàng", null, null,
				"/custom/kiem_hang_page", "record_list", "[\"Owner\",\"Admin\"]", null, null, 0, 7))
				.thenReturn(updatedPage);
		when(entityRepository.replaceBundle(eq(currentEntity), eq("Kiểm hàng"), eq("Desc"), eq(request.fields()),
				eq(request.views()), eq(request.permissions()), eq(7))).thenReturn(savedEntity);
		when(entityRepository.findFields(ENTITY_KEY)).thenReturn(fieldRows());
		when(entityRepository.findView(ENTITY_KEY)).thenReturn(Optional.of(viewRow(request.views())));
		when(entityRepository.findPermissions(ENTITY_KEY)).thenReturn(permissionRow());

		var saved = service.saveBundle(PAGE_KEY, request, jwt());

		assertThat(saved.menuPage().roles()).containsExactly("Owner", "Admin");
		verify(menuRepository).updateBuilderPageDraft(page, "kiem_hang", "Kiểm hàng", null, null,
				"/custom/kiem_hang_page", "record_list", "[\"Owner\",\"Admin\"]", null, null, 0, 7);
	}

	@Test
	void saveBundle_invalidDraftReturnsSummaryAndSkipsPersist() {
		var request = requestWithFields(List.of());
		var page = pageRow();
		var entity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(entity));
		when(menuRepository.findFolder("kiem_hang")).thenReturn(Optional.of(folderRow("kiem_hang")));
		when(menuRepository.routeExists("/custom/kiem_hang_page", page.id())).thenReturn(false);
		when(entityRepository.findFields(ENTITY_KEY)).thenReturn(fieldRows());
		when(entityRepository.findView(ENTITY_KEY)).thenReturn(Optional.of(viewRow(validRequest(PAGE_ETAG).views())));
		when(entityRepository.findPermissions(ENTITY_KEY)).thenReturn(permissionRow());

		var saved = service.saveBundle(PAGE_KEY, request, jwt());

		assertThat(saved.validationSummary().valid()).isFalse();
		assertThat(saved.validationSummary().errors()).isNotEmpty();
		verify(menuRepository, never()).updateBuilderPageDraft(any(), any(), any(), any(), any(), any(), any(), any(),
				any(), any(), anyInt(), eq(7));
		verify(entityRepository, never()).replaceBundle(any(), any(), any(), any(), any(), any(), any());
	}

	@Test
	void publish_validatesAndPublishesSnapshots() {
		var page = pageRow();
		var publishedPage = pageRow(1, 1, "Published", PAGE_ETAG);
		var entity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");
		var publishedEntity = entityRow(1, 1, "Published", "entity-kiem_hang_entity-draft-1");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page), Optional.of(publishedPage));
		when(menuRepository.findFolder("kiem_hang")).thenReturn(Optional.of(folderRow("kiem_hang")));
		when(menuRepository.routeExists("/custom/kiem_hang_page", page.id())).thenReturn(false);
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(entity), Optional.of(publishedEntity));
		when(entityRepository.findFields(ENTITY_KEY)).thenReturn(fieldRows());
		when(entityRepository.findView(ENTITY_KEY)).thenReturn(Optional.of(viewRow(validRequest(PAGE_ETAG).views())));
		when(entityRepository.findPermissions(ENTITY_KEY)).thenReturn(permissionRow());

		var published = service.publish(PAGE_KEY, PAGE_ETAG, jwt());

		assertThat(published.validationSummary().valid()).isTrue();
		verify(entityRepository).publishSnapshot(PAGE_KEY, entity, 7);
		verify(menuRepository).publishPage(page, 7);
	}

	@Test
	void publish_repositoryConflictThrowsBusinessConflict() {
		var page = pageRow();
		var entity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(menuRepository.findFolder("kiem_hang")).thenReturn(Optional.of(folderRow("kiem_hang")));
		when(menuRepository.routeExists("/custom/kiem_hang_page", page.id())).thenReturn(false);
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(entity));
		when(entityRepository.findFields(ENTITY_KEY)).thenReturn(fieldRows());
		when(entityRepository.findView(ENTITY_KEY)).thenReturn(Optional.of(viewRow(validRequest(PAGE_ETAG).views())));
		when(entityRepository.findPermissions(ENTITY_KEY)).thenReturn(permissionRow());
		doThrow(new OptimisticLockingFailureException("stale")).when(menuRepository).publishPage(page, 7);

		Throwable thrown = catchThrowable(() -> service.publish(PAGE_KEY, PAGE_ETAG, jwt()));

		assertThat(thrown).isInstanceOf(BusinessException.class);
		assertThat(((BusinessException) thrown).getCode()).isEqualTo(ApiErrorCode.CONFLICT);
	}

	@Test
	void publish_invalidCurrentPageRouteThrowsBadRequestAndSkipsSnapshots() {
		var page = pageRowWithRoute("/inventory/checks");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(menuRepository.findFolder("kiem_hang")).thenReturn(Optional.of(folderRow("kiem_hang")));

		Throwable thrown = catchThrowable(() -> service.publish(PAGE_KEY, PAGE_ETAG, jwt()));

		assertThat(thrown).isInstanceOf(BusinessException.class);
		assertThat(((BusinessException) thrown).getCode()).isEqualTo(ApiErrorCode.BAD_REQUEST);
		verify(entityRepository, never()).publishSnapshot(any(), any(), anyInt());
		verify(menuRepository, never()).publishPage(any(), anyInt());
	}

	private CustomBuilderBundleRequest validRequest(String etag) {
		return new CustomBuilderBundleRequest(menuPage(etag), ENTITY_KEY, "Kiểm hàng", "Desc", List.of(textField()),
				view(), permissionsRequest(), etag);
	}

	private CustomBuilderBundleRequest requestWithMenuPage(CustomPageRequest menuPage) {
		return requestWithMenuPage(menuPage, "Kiểm hàng");
	}

	private CustomBuilderBundleRequest requestWithMenuPage(CustomPageRequest menuPage, String entityLabel) {
		return new CustomBuilderBundleRequest(menuPage, ENTITY_KEY, entityLabel, "Desc", List.of(textField()), view(),
				permissionsRequest(), PAGE_ETAG);
	}

	private CustomBuilderBundleRequest requestWithEntityKey(String entityKey) {
		return new CustomBuilderBundleRequest(menuPage(PAGE_ETAG), entityKey, "Kiểm hàng", "Desc", List.of(textField()),
				view(), permissionsRequest(), PAGE_ETAG);
	}

	private CustomBuilderBundleRequest requestWithEntityLabel(String label) {
		return new CustomBuilderBundleRequest(menuPage(PAGE_ETAG), ENTITY_KEY, label, "Desc", List.of(textField()),
				view(), permissionsRequest(), PAGE_ETAG);
	}

	private CustomBuilderBundleRequest requestWithFields(List<CustomFieldRequest> fields) {
		return new CustomBuilderBundleRequest(menuPage(PAGE_ETAG), ENTITY_KEY, "Kiểm hàng", "Desc", fields, view(),
				permissionsRequest(), PAGE_ETAG);
	}

	private CustomPageRequest menuPage(String etag) {
		return new CustomPageRequest("kiem_hang", PAGE_KEY, "Kiểm hàng", null, null, "/custom/" + PAGE_KEY,
				ENTITY_KEY, "record_list", List.of("Owner"), null, null, 0, etag);
	}

	private CustomPageRequest menuPageWithKey(String key) {
		return new CustomPageRequest("kiem_hang", key, "Kiểm hàng", null, null, "/custom/" + key, ENTITY_KEY,
				"record_list", List.of("Owner"), null, null, 0, PAGE_ETAG);
	}

	private CustomPageRequest menuPageWithEntityKey(String entityKey) {
		return new CustomPageRequest("kiem_hang", PAGE_KEY, "Kiểm hàng", null, null, "/custom/" + PAGE_KEY,
				entityKey, "record_list", List.of("Owner"), null, null, 0, PAGE_ETAG);
	}

	private CustomPageRequest menuPageWithLabel(String label) {
		return new CustomPageRequest("kiem_hang", PAGE_KEY, label, null, null, "/custom/" + PAGE_KEY, ENTITY_KEY,
				"record_list", List.of("Owner"), null, null, 0, PAGE_ETAG);
	}

	private CustomPageRequest menuPageWithRoute(String routePath) {
		return new CustomPageRequest("kiem_hang", PAGE_KEY, "Kiểm hàng", null, null, routePath, ENTITY_KEY,
				"record_list", List.of("Owner"), null, null, 0, PAGE_ETAG);
	}

	private CustomPageRequest menuPageWithPageType(String pageType) {
		return new CustomPageRequest("kiem_hang", PAGE_KEY, "Kiểm hàng", null, null, "/custom/" + PAGE_KEY,
				ENTITY_KEY, pageType, List.of("Owner"), null, null, 0, PAGE_ETAG);
	}

	private CustomPageRequest menuPageWithVisibilityRoles(List<String> roles) {
		return new CustomPageRequest("kiem_hang", PAGE_KEY, "Kiểm hàng", null, null, "/custom/" + PAGE_KEY,
				ENTITY_KEY, "record_list", roles, null, null, 0, PAGE_ETAG);
	}

	private CustomPageRequest builderMenuPage(String etag) {
		return new CustomPageRequest("  kiem_hang_moi  ", PAGE_KEY, "  Kiểm hàng mới  ", "  package-check  ",
				"  Màn hình kiểm hàng mới  ", "  /custom/kiem-hang-moi  ", ENTITY_KEY, "  table_detail  ",
				List.of("Admin", " Staff "), "  can_manage_custom_builder  ", "  can_view_inventory  ", 12, etag);
	}

	private CustomFieldRequest textField() {
		return new CustomFieldRequest(null, "Tên", "name", "text", true, true, true, true, 0, null,
				mapper.createArrayNode(), mapper.createObjectNode(), mapper.createObjectNode(), null, false, false,
				"Active");
	}

	private CustomViewRequest view() {
		var columns = mapper.createArrayNode();
		columns.addObject().put("fieldKey", "name").put("label", "Tên");
		var sections = mapper.createArrayNode();
		sections.addObject().put("id", "main").put("title", "Thông tin")
				.set("fieldKeys", mapper.createArrayNode().add("name"));
		return new CustomViewRequest(columns, mapper.createArrayNode().add("name"), "name asc", sections, "desktop");
	}

	private PageRow pageRow() {
		return pageRow(1, null, "NeedsConfig", PAGE_ETAG);
	}

	private PageRow pageRow(int draftVersion, Integer publishedVersion, String status, String etag) {
		return new PageRow(1L, PAGE_KEY, "kiem_hang", "Kiểm hàng", null, null, "/custom/" + PAGE_KEY, ENTITY_KEY,
				"record_list", status, 0, "[\"Owner\"]", null, null, draftVersion, publishedVersion, etag, null,
				null);
	}

	private PageRow pageRowWithRoute(String routePath) {
		return new PageRow(1L, PAGE_KEY, "kiem_hang", "Kiểm hàng", null, null, routePath, ENTITY_KEY, "record_list",
				"NeedsConfig", 0, "[\"Owner\"]", null, null, 1, null, PAGE_ETAG, null, null);
	}

	private PageRow builderPageRow() {
		return new PageRow(1L, PAGE_KEY, "kiem_hang_moi", "Kiểm hàng mới", "package-check",
				"Màn hình kiểm hàng mới", "/custom/kiem-hang-moi", ENTITY_KEY, "table_detail", "NeedsConfig", 12,
				"[\"Admin\",\"Staff\"]", "can_manage_custom_builder", "can_view_inventory", 2, null,
				"page-kiem_hang_page-draft-2", null, null);
	}

	private FolderRow folderRow(String key) {
		return new FolderRow(2L, key, "Kiểm hàng", null, null, "Draft", 0, "[\"Owner\"]", 1, null,
				"folder-" + key + "-draft-1", null, null);
	}

	private EntityRow entityRow(int draftVersion, Integer publishedVersion, String status, String etag) {
		return new EntityRow(10L, ENTITY_KEY, "Kiểm hàng", "Desc", status, draftVersion, publishedVersion, etag);
	}

	private List<FieldRow> fieldRows() {
		return List.of(new FieldRow("field-1", ENTITY_KEY, "name", "Tên", "text", true, true, true, true, 0,
				null, mapper.createArrayNode(), mapper.createObjectNode(), mapper.createObjectNode(), null, "Active"));
	}

	private ViewRow viewRow(CustomViewRequest view) {
		return new ViewRow(ENTITY_KEY, view.listColumns(), view.filterFields(), view.defaultSort(), view.formSections());
	}

	private PermissionRow permissionRow() {
		return new PermissionRow(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner"));
	}

	private CustomPermissionRequest permissionsRequest() {
		return new CustomPermissionRequest(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner"));
	}

	private Jwt jwt() {
		return Jwt.withTokenValue("token").header("alg", "none").subject("7").claim("role", "Owner").build();
	}

	private void assertBadRequestDoesNotPersist(CustomBuilderBundleRequest request) {
		assertBadRequestDoesNotPersist(request, false, false);
	}

	private void assertBadRequestDoesNotPersistAfterKnownParent(CustomBuilderBundleRequest request) {
		assertBadRequestDoesNotPersist(request, true, false);
	}

	private void assertBadRequestDoesNotPersistAfterKnownRoute(CustomBuilderBundleRequest request) {
		assertBadRequestDoesNotPersist(request, true, true);
	}

	private void assertBadRequestDoesNotPersist(CustomBuilderBundleRequest request, boolean knownParent,
			boolean uniqueRoute) {
		var page = pageRow();
		var entity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(entity));
		if (knownParent) {
			when(menuRepository.findFolder("kiem_hang")).thenReturn(Optional.of(folderRow("kiem_hang")));
		}
		if (uniqueRoute) {
			when(menuRepository.routeExists("/custom/kiem_hang_page", page.id())).thenReturn(false);
		}

		Throwable thrown = catchThrowable(() -> service.saveBundle(PAGE_KEY, request, jwt()));

		assertThat(thrown).isInstanceOf(BusinessException.class);
		assertThat(((BusinessException) thrown).getCode()).isEqualTo(ApiErrorCode.BAD_REQUEST);
		verify(menuRepository, never()).updateBuilderPageDraft(any(), any(), any(), any(), any(), any(), any(), any(),
				any(), any(), anyInt(), eq(7));
		verify(entityRepository, never()).replaceBundle(any(), any(), any(), any(), any(), any(), any());
	}
}
