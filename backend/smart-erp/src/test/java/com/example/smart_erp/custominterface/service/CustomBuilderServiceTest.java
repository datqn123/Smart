package com.example.smart_erp.custominterface.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.oauth2.jwt.Jwt;

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
	void saveBundle_validatesAndPersistsMetadata() {
		var request = validRequest(PAGE_ETAG);
		var page = pageRow();
		var currentEntity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");
		var savedEntity = entityRow(2, null, "NeedsConfig", "entity-kiem_hang_entity-draft-2");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(currentEntity));
		when(entityRepository.replaceBundle(eq(currentEntity), eq("Kiểm hàng"), eq("Desc"), eq(request.fields()),
				eq(request.views()), eq(request.permissions()), eq(7))).thenReturn(savedEntity);
		when(entityRepository.findFields(ENTITY_KEY)).thenReturn(fieldRows());
		when(entityRepository.findView(ENTITY_KEY)).thenReturn(Optional.of(viewRow(request.views())));
		when(entityRepository.findPermissions(ENTITY_KEY)).thenReturn(permissionRow());

		var saved = service.saveBundle(PAGE_KEY, request, jwt());

		assertThat(saved.validationSummary().valid()).isTrue();
		assertThat(saved.entityDefinition().etag()).isEqualTo("entity-kiem_hang_entity-draft-2");
		verify(entityRepository).replaceBundle(eq(currentEntity), eq("Kiểm hàng"), eq("Desc"), eq(request.fields()),
				eq(request.views()), eq(request.permissions()), eq(7));
	}

	@Test
	void publish_validatesAndPublishesSnapshots() {
		var page = pageRow();
		var entity = entityRow(1, null, "NeedsConfig", "entity-kiem_hang_entity-draft-1");

		when(menuRepository.findPage(PAGE_KEY)).thenReturn(Optional.of(page));
		when(entityRepository.findEntity(ENTITY_KEY)).thenReturn(Optional.of(entity));
		when(entityRepository.findFields(ENTITY_KEY)).thenReturn(fieldRows());
		when(entityRepository.findView(ENTITY_KEY)).thenReturn(Optional.of(viewRow(validRequest(PAGE_ETAG).views())));
		when(entityRepository.findPermissions(ENTITY_KEY)).thenReturn(permissionRow());

		var published = service.publish(PAGE_KEY, PAGE_ETAG, jwt());

		assertThat(published.validationSummary().valid()).isTrue();
		verify(entityRepository).publishSnapshot(PAGE_KEY, entity, 7);
		verify(menuRepository).publishPage(PAGE_KEY, 7);
	}

	private CustomBuilderBundleRequest validRequest(String etag) {
		return new CustomBuilderBundleRequest(menuPage(etag), ENTITY_KEY, "Kiểm hàng", "Desc", List.of(textField()),
				view(), permissionsRequest(), etag);
	}

	private CustomPageRequest menuPage(String etag) {
		return new CustomPageRequest("kiem_hang", PAGE_KEY, "Kiểm hàng", null, null, "/custom/" + PAGE_KEY,
				ENTITY_KEY, "record_list", List.of("Owner"), null, null, 0, etag);
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
		return new PageRow(1L, PAGE_KEY, "kiem_hang", "Kiểm hàng", null, null, "/custom/" + PAGE_KEY, ENTITY_KEY,
				"record_list", "NeedsConfig", 0, "[\"Owner\"]", null, null, 1, null, PAGE_ETAG, null, null);
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
}
