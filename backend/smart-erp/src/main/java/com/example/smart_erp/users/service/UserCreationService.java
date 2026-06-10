package com.example.smart_erp.users.service;

import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.example.smart_erp.auth.entity.Role;
import com.example.smart_erp.auth.entity.User;
import com.example.smart_erp.auth.repository.RoleRepository;
import com.example.smart_erp.auth.repository.UserRepository;
import com.example.smart_erp.auth.support.RolePermissionReader;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.users.dto.UserCreateRequest;
import com.example.smart_erp.users.response.UserResponseData;

@Service
public class UserCreationService {

	private static final String OWNER_ROLE_NAME = "Owner";

	private final UserRepository userRepository;

	private final RoleRepository roleRepository;

	private final PasswordEncoder passwordEncoder;

	private final RolePermissionReader rolePermissionReader;

	public UserCreationService(UserRepository userRepository, RoleRepository roleRepository,
			PasswordEncoder passwordEncoder, RolePermissionReader rolePermissionReader) {
		this.userRepository = userRepository;
		this.roleRepository = roleRepository;
		this.passwordEncoder = passwordEncoder;
		this.rolePermissionReader = rolePermissionReader;
	}

	@Transactional
	public UserResponseData createUser(int actorUserId, UserCreateRequest request) {
		User actor = userRepository.findWithRoleById(actorUserId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.UNAUTHORIZED, "Phiên đăng nhập không hợp lệ"));
		if (!"Active".equals(actor.getStatus())) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Tài khoản của bạn không thể thực hiện thao tác này");
		}
		if (!rolePermissionReader.canManageStaff(actor.getRole())) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Bạn không có quyền quản lý nhân viên");
		}

		Integer roleId = Objects.requireNonNull(request.roleId(), "roleId");
		Role targetRole = roleRepository.findById(roleId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, "Vai trò không hợp lệ",
						Map.of("roleId", "Không tồn tại")));

		if (OWNER_ROLE_NAME.equalsIgnoreCase(targetRole.getName())) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Không được phép gán vai trò Owner cho tài khoản mới");
		}

		String emailNorm = request.email().strip();
		String usernameNorm = request.username().strip();

		assertNotDuplicate(usernameNorm, emailNorm);

		String apiStatus = request.status() != null ? request.status() : "Active";
		String dbStatus = "Inactive".equals(apiStatus) ? "Locked" : "Active";

		User u = new User();
		u.setUsername(usernameNorm);
		u.setPasswordHash(passwordEncoder.encode(request.password()));
		u.setFullName(request.fullName().strip());
		u.setEmail(emailNorm);
		if (StringUtils.hasText(request.phone())) {
			u.setPhone(request.phone().strip());
		}
		if (StringUtils.hasText(request.staffCode())) {
			u.setStaffCode(request.staffCode().strip());
		}
		u.setRoleId(roleId);
		u.setStatus(dbStatus);
		User saved = userRepository.save(u);
		String roleName = targetRole.getName();
		return toResponse(saved, roleName);
	}

	private void assertNotDuplicate(String username, String email) {
		Map<String, String> details = new LinkedHashMap<>();
		if (userRepository.existsByUsername(username)) {
			details.put("username", "Tên đăng nhập đã được sử dụng");
		}
		if (userRepository.existsByEmailIgnoreCase(email)) {
			details.put("email", "Email đã được sử dụng");
		}
		if (!details.isEmpty()) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Dữ liệu đã tồn tại trong hệ thống", details);
		}
	}

	private static UserResponseData toResponse(User user, String roleDisplayName) {
		String employeeCode = StringUtils.hasText(user.getStaffCode()) ? user.getStaffCode() : user.getUsername();
		String apiStatus = "Active".equals(user.getStatus()) ? "Active" : "Inactive";
		String joined = user.getCreatedAt() != null
				? user.getCreatedAt().atZone(ZoneOffset.UTC).toLocalDate().toString()
				: null;
		return new UserResponseData(user.getId(), employeeCode, user.getFullName(), user.getEmail(),
				user.getPhone(), user.getRoleId(), roleDisplayName, apiStatus, joined, null);
	}
}
