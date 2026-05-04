package com.example.smart_erp.settings.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;
import java.util.Map;
import java.util.Objects;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.common.exception.GlobalExceptionHandler;
import com.example.smart_erp.common.exception.MaxUploadSizeExceededAdvice;
import com.example.smart_erp.config.MethodSecurityTestConfiguration;
import com.example.smart_erp.config.PermitAllWebSecurityConfiguration;
import com.example.smart_erp.config.SecurityBeansConfiguration;
import com.example.smart_erp.settings.systemlogs.SystemLogsService;
import com.example.smart_erp.settings.systemlogs.response.SystemLogItemData;
import com.example.smart_erp.settings.systemlogs.response.SystemLogsListData;

@WebMvcTest(controllers = SystemLogsController.class)
@Import({ GlobalExceptionHandler.class, MaxUploadSizeExceededAdvice.class, SecurityBeansConfiguration.class,
		PermitAllWebSecurityConfiguration.class, MethodSecurityTestConfiguration.class })
class SystemLogsControllerWebMvcTest {

	@Autowired
	private MockMvc mockMvc;

	@MockitoBean
	private SystemLogsService service;

	@Test
	void get_returns200WithEnvelope() throws Exception {
		var item = new SystemLogItemData(101, "2026-04-23T10:30:15.000Z", "Nguyễn Văn A", "LOGIN", "AUTH",
				"Người dùng đăng nhập thành công", "Info", "192.168.1.1");
		when(service.list(eq("abc"), eq(null), eq(null), eq(null), eq(null), eq(1), eq(20), any(org.springframework.security.oauth2.jwt.Jwt.class)))
				.thenReturn(new SystemLogsListData(List.of(item), 1, 20, 1));

		mockMvc.perform(get("/api/v1/system-logs").param("search", "abc").param("page", "1").param("limit", "20")
				.with(Objects.requireNonNull(jwt().jwt(j -> j.subject("1").claim("role", "Admin")
						.claim("mp", Map.of("can_view_system_logs", true))))))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.success").value(true))
				.andExpect(jsonPath("$.data.items.length()").value(1))
				.andExpect(jsonPath("$.data.items[0].id").value(101))
				.andExpect(jsonPath("$.data.total").value(1));
	}

	@Test
	void delete_whenPolicyForbidden_returns403() throws Exception {
		doThrow(new BusinessException(ApiErrorCode.FORBIDDEN, "Không được phép xóa nhật ký hệ thống theo chính sách hệ thống."))
				.when(service).deleteById(eq(10L), any(org.springframework.security.oauth2.jwt.Jwt.class));

		mockMvc.perform(delete("/api/v1/system-logs/10")
				.with(Objects.requireNonNull(jwt().jwt(j -> j.subject("1").claim("role", "Admin")
						.claim("mp", Map.of("can_view_system_logs", true))))))
				.andExpect(status().isForbidden())
				.andExpect(jsonPath("$.success").value(false))
				.andExpect(jsonPath("$.error").value("FORBIDDEN"))
				.andExpect(jsonPath("$.message").value("Không được phép xóa nhật ký hệ thống theo chính sách hệ thống."));

		verify(service).deleteById(eq(10L), any(org.springframework.security.oauth2.jwt.Jwt.class));
	}

	@Test
	void bulkDelete_whenPolicyForbidden_returns403() throws Exception {
		doThrow(new BusinessException(ApiErrorCode.FORBIDDEN, "Không được phép xóa nhật ký hệ thống theo chính sách hệ thống."))
				.when(service).bulkDelete(anyList(), any(org.springframework.security.oauth2.jwt.Jwt.class));

		mockMvc.perform(post("/api/v1/system-logs/bulk-delete").contentType(MediaType.APPLICATION_JSON_VALUE)
				.content("{\"ids\":[1,2,3]}")
				.with(Objects.requireNonNull(jwt().jwt(j -> j.subject("1").claim("role", "Admin")
						.claim("mp", Map.of("can_view_system_logs", true))))))
				.andExpect(status().isForbidden())
				.andExpect(jsonPath("$.success").value(false))
				.andExpect(jsonPath("$.error").value("FORBIDDEN"));
	}
}

