package com.example.smart_erp.users.service;

import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

import org.springframework.dao.DataIntegrityViolationException;
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
import com.example.smart_erp.users.dto.UserPatchRequest;
import com.example.smart_erp.users.repository.UsersListJdbcRepository;
import com.example.smart_erp.users.response.UserDetailData;
import com.example.smart_erp.users.response.UserSummaryData;
import com.example.smart_erp.users.response.UsersListPageData;

@Service
public class UsersManagementService {

	private static final String OWNER_ROLE_NAME = "Owner";

	private final UsersListJdbcRepository usersListJdbcRepository;
	private final UserRepository userRepository;
	private final RoleRepository roleRepository;
	private final RolePermissionReader rolePermissionReader;
	private final PasswordEncoder passwordEncoder;

	public UsersManagementService(UsersListJdbcRepository usersListJdbcRepository, UserRepository userRepository,
			RoleRepository roleRepository, RolePermissionReader rolePermissionReader, PasswordEncoder passwordEncoder) {
		this.usersListJdbcRepository = usersListJdbcRepository;
		this.userRepository = userRepository;
		this.roleRepository = roleRepository;
		this.rolePermissionReader = rolePermissionReader;
		this.passwordEncoder = passwordEncoder;
	}

	public UsersListPageData list(int actorUserId, String search, String status, Integer roleId, int page, int limit) {
		User actor = requireActorCanManageStaff(actorUserId);
		Objects.requireNonNull(actor, "actor");
		long total = usersListJdbcRepository.countRows(search, status, roleId);
		var rows = usersListJdbcRepository.loadPage(search, status, roleId, page, limit);
		var items = rows.stream().map(UsersManagementService::toSummary).toList();
		return new UsersListPageData(items, page, limit, total);
	}

	public UserDetailData getById(int actorUserId, int userId) {
		User actor = userRepository.findWithRoleById(actorUserId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.UNAUTHORIZED, "Phiên đăng nhập không hợp lệ"));
		if (!"Active".equals(actor.getStatus())) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Tài khoản của bạn không thể thực hiện thao tác này");
		}
		boolean isSelf = actorUserId == userId;
		if (!isSelf && !rolePermissionReader.canManageStaff(actor.getRole())) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Bạn không có quyền xem nhân viên");
		}

		User u = isSelf ? actor : userRepository.findWithRoleById(userId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nhân viên"));
		return toDetail(u);
	}

	@Transactional
	public UserDetailData patch(int actorUserId, int userId, UserPatchRequest body) {
		if (body == null || body.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of("body", "Cần ít nhất một trường"));
		}

		User actor = requireActorCanManageStaff(actorUserId);
		User target = userRepository.findWithRoleById(userId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nhân viên"));

		boolean roleIdChange = body.roleId() != null && !Objects.equals(body.roleId(), target.getRoleId());
		if (roleIdChange) {
			String actorRoleName = actor.getRole() != null ? actor.getRole().getName() : "";
			if (!OWNER_ROLE_NAME.equalsIgnoreCase(actorRoleName)) {
				throw new BusinessException(ApiErrorCode.FORBIDDEN, "Chỉ Owner được phép thay đổi vai trò");
			}
			Role newRole = roleRepository.findById(Objects.requireNonNull(body.roleId(), "roleId"))
					.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, "Vai trò không hợp lệ",
							Map.of("roleId", "Không tồn tại")));
			if (OWNER_ROLE_NAME.equalsIgnoreCase(newRole.getName())) {
				throw new BusinessException(ApiErrorCode.FORBIDDEN, "Không được phép gán vai trò Owner");
			}
			target.setRoleId(body.roleId());
		}

		if (body.fullName() != null) {
			target.setFullName(body.fullName());
		}
		if (body.email() != null) {
			target.setEmail(body.email());
		}
		if (body.phone() != null) {
			target.setPhone(body.phone());
		}
		if (body.staffCode() != null) {
			target.setStaffCode(body.staffCode());
		}
		if (body.status() != null) {
			target.setStatus("Inactive".equals(body.status()) ? "Locked" : "Active");
		}
		if (StringUtils.hasText(body.password())) {
			target.setPasswordHash(passwordEncoder.encode(body.password()));
		}

		try {
			User saved = Objects.requireNonNull(userRepository.save(Objects.requireNonNull(target, "target")),
					"saved user");
			User withRole = userRepository.findWithRoleById(Objects.requireNonNull(saved.getId(), "id"))
					.orElse(saved);
			return toDetail(withRole);
		}
		catch (DataIntegrityViolationException e) {
			// OQ-4: trùng thông tin → 409 và huỷ lưu. Ở đây ưu tiên trả details theo các field phổ biến.
			Map<String, String> details = new LinkedHashMap<>();
			if (body.email() != null && userRepository.existsByEmailIgnoreCase(body.email())) {
				details.put("email", "Email đã được sử dụng");
			}
			if (body.staffCode() != null) {
				// staff_code unique partial; không có exists helper nên chỉ gợi ý chung
				details.putIfAbsent("staffCode", "Mã nhân viên đã được sử dụng");
			}
			throw new BusinessException(ApiErrorCode.CONFLICT, "Dữ liệu đã tồn tại trong hệ thống",
					details.isEmpty() ? null : details);
		}
	}

	@Transactional
	public void softDelete(int actorUserId, int userId) {
		requireActorCanManageStaff(actorUserId);
		if (actorUserId == userId) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể vô hiệu hóa tài khoản của chính bạn");
		}

		User target = userRepository.findWithRoleById(userId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nhân viên"));

		String targetRoleName = target.getRole() != null ? target.getRole().getName() : "";
		if (OWNER_ROLE_NAME.equalsIgnoreCase(targetRoleName)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể vô hiệu hóa tài khoản Owner");
		}

		userRepository.lockActiveUserById(userId);
	}

	private User requireActorCanManageStaff(int actorUserId) {
		User actor = userRepository.findWithRoleById(actorUserId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.UNAUTHORIZED, "Phiên đăng nhập không hợp lệ"));
		if (!"Active".equals(actor.getStatus())) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Tài khoản của bạn không thể thực hiện thao tác này");
		}
		if (!rolePermissionReader.canManageStaff(actor.getRole())) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Bạn không có quyền quản lý nhân viên");
		}
		return actor;
	}

	private static UserSummaryData toSummary(UsersListJdbcRepository.UserListRow r) {
		String employeeCode = StringUtils.hasText(r.staffCode()) ? r.staffCode() : r.username();
		String apiStatus = "Active".equals(r.dbStatus()) ? "Active" : "Inactive";
		return new UserSummaryData(
				r.id(),
				employeeCode,
				r.fullName(),
				r.email(),
				r.phone(),
				r.roleId(),
				r.roleName(),
				apiStatus,
				r.joinedDate() != null ? r.joinedDate().toString() : null,
				null);
	}

	private static UserDetailData toDetail(User u) {
		String roleName = u.getRole() != null ? u.getRole().getName() : "";
		String employeeCode = StringUtils.hasText(u.getStaffCode()) ? u.getStaffCode() : u.getUsername();
		String apiStatus = "Active".equals(u.getStatus()) ? "Active" : "Inactive";
		String joined = u.getCreatedAt() != null ? u.getCreatedAt().atZone(ZoneOffset.UTC).toLocalDate().toString() : null;
		String lastLogin = u.getLastLogin() != null ? u.getLastLogin().toString() : null;
		return new UserDetailData(
				Objects.requireNonNullElse(u.getId(), 0),
				employeeCode,
				u.getFullName(),
				u.getEmail(),
				u.getPhone(),
				Objects.requireNonNullElse(u.getRoleId(), 0),
				roleName,
				apiStatus,
				joined,
				null,
				u.getUsername(),
				lastLogin);
	}
}

