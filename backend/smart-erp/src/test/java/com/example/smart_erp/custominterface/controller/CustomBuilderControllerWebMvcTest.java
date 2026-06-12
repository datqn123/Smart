package com.example.smart_erp.custominterface.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;
import java.util.Objects;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.example.smart_erp.common.exception.GlobalExceptionHandler;
import com.example.smart_erp.common.exception.MaxUploadSizeExceededAdvice;
import com.example.smart_erp.config.MethodSecurityTestConfiguration;
import com.example.smart_erp.config.PermitAllWebSecurityConfiguration;
import com.example.smart_erp.config.SecurityBeansConfiguration;
import com.example.smart_erp.custominterface.dto.CustomBuilderBundleRequest;
import com.example.smart_erp.custominterface.response.CustomBuilderBundleData;
import com.example.smart_erp.custominterface.response.CustomEntityData;
import com.example.smart_erp.custominterface.response.CustomMenuPageData;
import com.example.smart_erp.custominterface.response.CustomPermissionData;
import com.example.smart_erp.custominterface.response.CustomViewData;
import com.example.smart_erp.custominterface.response.ValidationSummaryData;
import com.example.smart_erp.custominterface.service.CustomBuilderService;
import com.example.smart_erp.custominterface.service.CustomInterfaceService;
import com.fasterxml.jackson.databind.ObjectMapper;

@WebMvcTest(controllers = { CustomBuilderController.class, CustomInterfaceController.class })
@Import({ GlobalExceptionHandler.class, MaxUploadSizeExceededAdvice.class, SecurityBeansConfiguration.class,
		PermitAllWebSecurityConfiguration.class, MethodSecurityTestConfiguration.class })
class CustomBuilderControllerWebMvcTest {

	private static final String PAGE_KEY = "inventory_checks";

	@Autowired
	private MockMvc mockMvc;

	@Autowired
	private ObjectMapper objectMapper;

	@MockitoBean
	private CustomBuilderService builderService;

	@MockitoBean
	private CustomInterfaceService interfaceService;

	@Test
	void getBundle_returns403WithoutManageBuilderAuthority() throws Exception {
		mockMvc.perform(get("/api/v1/custom/builder/pages/{pageKey}/bundle", PAGE_KEY)
				.with(Objects.requireNonNull(jwt().authorities(new SimpleGrantedAuthority("can_view_dashboard")))
						.jwt(j -> j.subject("7"))))
				.andExpect(status().isForbidden());

		verifyNoInteractions(builderService);
	}

	@Test
	void getBundle_returnsEnvelopeForAuthorizedUser() throws Exception {
		when(builderService.getBundle(PAGE_KEY)).thenReturn(bundle("etag-1"));

		mockMvc.perform(get("/api/v1/custom/builder/pages/{pageKey}/bundle", PAGE_KEY)
				.with(manageBuilderJwt()))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.success").value(true))
				.andExpect(jsonPath("$.message").value("Thành công"))
				.andExpect(jsonPath("$.data.menuPage.key").value(PAGE_KEY))
				.andExpect(jsonPath("$.data.etag").value("etag-1"));

		verify(builderService).getBundle(PAGE_KEY);
	}

	@Test
	void patchBundle_delegatesSaveAndReturnsData() throws Exception {
		when(builderService.saveBundle(eq(PAGE_KEY), any(CustomBuilderBundleRequest.class), any(Jwt.class)))
				.thenReturn(bundle("etag-2"));

		mockMvc.perform(patch("/api/v1/custom/builder/pages/{pageKey}/bundle", PAGE_KEY)
				.contentType(APPLICATION_JSON)
				.content(bundleRequestJson("etag-1"))
				.with(manageBuilderJwt()))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.message").value("Đã lưu bản nháp cấu hình giao diện"))
				.andExpect(jsonPath("$.data.etag").value("etag-2"));

		verify(builderService).saveBundle(eq(PAGE_KEY), any(CustomBuilderBundleRequest.class), any(Jwt.class));
	}

	@Test
	void validatePage_delegatesValidation() throws Exception {
		when(builderService.validatePage(PAGE_KEY)).thenReturn(ValidationSummaryData.ok());

		mockMvc.perform(post("/api/v1/custom/builder/pages/{pageKey}/validate", PAGE_KEY)
				.with(manageBuilderJwt()))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.message").value("Thành công"))
				.andExpect(jsonPath("$.data.valid").value(true));

		verify(builderService).validatePage(PAGE_KEY);
	}

	@Test
	void publishPage_passesEtagAndReturnsBundle() throws Exception {
		when(builderService.publish(eq(PAGE_KEY), eq("etag-1"), any(Jwt.class))).thenReturn(bundle("etag-2"));

		mockMvc.perform(post("/api/v1/custom/builder/pages/{pageKey}/publish", PAGE_KEY)
				.contentType(APPLICATION_JSON)
				.content("{\"etag\":\"etag-1\"}")
				.with(manageBuilderJwt()))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.message").value("Đã publish cấu hình giao diện"))
				.andExpect(jsonPath("$.data.etag").value("etag-2"));

		verify(builderService).publish(eq(PAGE_KEY), eq("etag-1"), any(Jwt.class));
	}

	@Test
	void runtimePage_returnsBuilderBundleFromInterfaceController() throws Exception {
		when(builderService.runtimeBundle(eq(PAGE_KEY), any(Authentication.class), any(Jwt.class)))
				.thenReturn(bundle("runtime-etag"));

		mockMvc.perform(get("/api/v1/custom/pages/{pageKey}/runtime", PAGE_KEY)
				.with(Objects.requireNonNull(jwt().authorities(new SimpleGrantedAuthority("can_use_custom_entities")))
						.jwt(j -> j.subject("7").claim("role", "Admin"))))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.message").value("Thành công"))
				.andExpect(jsonPath("$.data.menuPage.key").value(PAGE_KEY))
				.andExpect(jsonPath("$.data.etag").value("runtime-etag"));

		verify(builderService).runtimeBundle(eq(PAGE_KEY), any(Authentication.class), any(Jwt.class));
	}

	private CustomBuilderBundleData bundle(String etag) {
		return new CustomBuilderBundleData(
				new CustomMenuPageData("page", "1", PAGE_KEY, "Kiểm hàng", "clipboard-check", "operations",
						"/custom/inventory-checks", "inventory_check", "record_list", "Published", 0, null,
						List.of("Admin"), "can_use_custom_entities", "can_view_inventory", 1, 1, 1, false, null,
						null, null, null, etag, ValidationSummaryData.ok()),
				new CustomEntityData("inventory_check", "Kiểm hàng", "Desc", "Published", 1, 1, 1, "entity-etag"),
				List.of(),
				new CustomViewData(objectMapper.createArrayNode(), objectMapper.createArrayNode(), "name asc",
						objectMapper.createArrayNode(), "desktop"),
				new CustomPermissionData(List.of("Admin"), List.of("Admin"), List.of("Admin"), List.of("Admin")),
				ValidationSummaryData.ok(), etag);
	}

	private String bundleRequestJson(String etag) {
		return """
				{
				  "menuPage": {
				    "parentKey": "operations",
				    "key": "inventory_checks",
				    "label": "Kiểm hàng",
				    "icon": "clipboard-check",
				    "description": null,
				    "routePath": "/custom/inventory-checks",
				    "entityKey": "inventory_check",
				    "pageType": "record_list",
				    "visibilityRoles": ["Admin"],
				    "entityPermission": "can_use_custom_entities",
				    "dataPermission": "can_view_inventory",
				    "sortOrder": 0,
				    "etag": "%s"
				  },
				  "entityKey": "inventory_check",
				  "entityLabel": "Kiểm hàng",
				  "entityDescription": "Desc",
				  "fields": [],
				  "views": {
				    "listColumns": [],
				    "filterFields": [],
				    "defaultSort": "name asc",
				    "formSections": [],
				    "previewMode": "desktop"
				  },
				  "permissions": {
				    "view": ["Admin"],
				    "create": ["Admin"],
				    "update": ["Admin"],
				    "delete": ["Admin"]
				  },
				  "etag": "%s"
				}
				""".formatted(etag, etag);
	}

	private static org.springframework.test.web.servlet.request.RequestPostProcessor manageBuilderJwt() {
		return Objects.requireNonNull(jwt()
				.authorities(new SimpleGrantedAuthority("can_manage_custom_builder"))
				.jwt(j -> j.subject("7").claim("role", "Admin")));
	}
}
