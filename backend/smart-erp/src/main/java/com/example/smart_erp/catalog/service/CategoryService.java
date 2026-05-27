package com.example.smart_erp.catalog.service;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.fasterxml.jackson.databind.JsonNode;

import com.example.smart_erp.catalog.dto.CategoryCreateRequest;
import com.example.smart_erp.catalog.repository.CategoryJdbcRepository;
import com.example.smart_erp.catalog.repository.CategoryJdbcRepository.CategoryFlatRow;
import com.example.smart_erp.catalog.repository.CategoryParentEdgeRow;
import com.example.smart_erp.catalog.response.CategoryDeleteData;
import com.example.smart_erp.catalog.response.CategoryDetailData;
import com.example.smart_erp.catalog.response.CategoryListPageData;
import com.example.smart_erp.catalog.response.CategoryNodeResponse;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;

import org.springframework.security.oauth2.jwt.Jwt;

@Service
public class CategoryService {

	private static final Pattern CODE_PATTERN = Pattern.compile("^\\S.*\\S$|^\\S$");

	private final CategoryJdbcRepository categoryJdbcRepository;

	public CategoryService(CategoryJdbcRepository categoryJdbcRepository) {
		this.categoryJdbcRepository = categoryJdbcRepository;
	}

	@Transactional(readOnly = true)
	public CategoryListPageData list(String formatRaw, String searchRaw, String statusRaw) {
		String format = formatRaw == null || formatRaw.isBlank() ? "tree" : formatRaw.trim().toLowerCase(Locale.ROOT);
		if (!"tree".equals(format) && !"flat".equals(format)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số truy vấn không hợp lệ",
					Map.of("format", "Chỉ chấp nhận tree hoặc flat"));
		}
		String statusFilter = normalizeListStatus(statusRaw);
		List<CategoryFlatRow> rows = categoryJdbcRepository.loadAllActive(statusFilter);
		List<CategoryFlatRow> filtered = applySearchFilter(rows, searchRaw);
		Set<Long> allowed = new HashSet<>();
		for (CategoryFlatRow r : filtered) {
			allowed.add(r.id());
		}
		if ("flat".equals(format)) {
			filtered.sort((a, b) -> {
				int c = Integer.compare(a.sortOrder(), b.sortOrder());
				if (c != 0) {
					return c;
				}
				return a.name().compareToIgnoreCase(b.name());
			});
			List<CategoryNodeResponse> items = new ArrayList<>();
			for (CategoryFlatRow r : filtered) {
				items.add(categoryJdbcRepository.toNodeResponseFlat(r));
			}
			return new CategoryListPageData(items);
		}
		Map<Long, CategoryFlatRow> byId = new HashMap<>();
		for (CategoryFlatRow r : filtered) {
			byId.put(r.id(), r);
		}
		Map<Long, List<Long>> childrenIndex = categoryJdbcRepository.buildChildrenIndex(filtered);
		List<CategoryNodeResponse> roots = new ArrayList<>();
		Set<Long> emittedRoot = new HashSet<>();
		for (CategoryFlatRow r : filtered) {
			boolean localRoot = r.parentId() == null || !allowed.contains(r.parentId());
			if (localRoot && emittedRoot.add(r.id())) {
				roots.add(buildSubTree(r.id(), byId, childrenIndex, allowed));
			}
		}
		roots.sort((a, b) -> {
			int c = Integer.compare(a.sortOrder(), b.sortOrder());
			if (c != 0) {
				return c;
			}
			return a.name().compareToIgnoreCase(b.name());
		});
		return new CategoryListPageData(roots);
	}

	private CategoryNodeResponse buildSubTree(long id, Map<Long, CategoryFlatRow> byId,
			Map<Long, List<Long>> childrenIndex, Set<Long> allowed) {
		CategoryFlatRow c = byId.get(id);
		if (c == null) {
			throw new IllegalStateException("Thiếu node danh mục id=" + id + " trong tập đã lọc");
		}
		List<CategoryNodeResponse> childNodes = new ArrayList<>();
		for (Long ch : childrenIndex.getOrDefault(id, List.of())) {
			if (allowed.contains(ch)) {
				childNodes.add(buildSubTree(ch, byId, childrenIndex, allowed));
			}
		}
		childNodes.sort((a, b) -> {
			int cmp = Integer.compare(a.sortOrder(), b.sortOrder());
			if (cmp != 0) {
				return cmp;
			}
			return a.name().compareToIgnoreCase(b.name());
		});
		return categoryJdbcRepository.toNodeResponse(c, childNodes);
	}

	@Transactional(readOnly = true)
	public CategoryDetailData getById(long id) {
		return categoryJdbcRepository.loadDetail(id)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy danh mục"));
	}

	@Transactional(readOnly = true)
	public java.util.Optional<Long> findIdByCategoryCode(String categoryCode) {
		if (!StringUtils.hasText(categoryCode)) {
			return java.util.Optional.empty();
		}
		return categoryJdbcRepository.findActiveIdByExactCode(categoryCode.trim());
	}

	@Transactional
	public CategoryNodeResponse create(CategoryCreateRequest req) {
		String code = requireNonBlank(req.categoryCode(), "categoryCode", 50);
		String name = requireNonBlank(req.name(), "name", 255);
		String status = normalizeStatusOrDefault(req.status());
		int sortOrder = req.sortOrder() == null ? 0 : req.sortOrder();
		if (categoryJdbcRepository.existsActiveWithCode(code)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Mã danh mục đã tồn tại");
		}
		Long parentId = req.parentId();
		if (parentId != null && !categoryJdbcRepository.existsActiveId(parentId)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Danh mục cha không tồn tại",
					Map.of("parentId", "parentId không khớp bản ghi categories đang hiệu lực"));
		}
		String description = normalizeDescriptionForStore(req.description());
		long newId = categoryJdbcRepository.insert(code, name, description, parentId, sortOrder, status);
		return categoryJdbcRepository.findActiveById(newId)
				.map(c -> categoryJdbcRepository.toNodeResponse(c, List.of()))
				.orElseThrow(() -> new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Không đọc lại danh mục sau tạo"));
	}

	@Transactional
	public CategoryNodeResponse patch(long id, JsonNode body) {
		if (body == null || !body.isObject() || body.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Body PATCH không được rỗng");
		}
		CategoryFlatRow locked = categoryJdbcRepository.lockActiveByIdForUpdate(id)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy danh mục"));
		String newCode = locked.categoryCode();
		String newName = locked.name();
		String newDesc = locked.description();
		Long newParent = locked.parentId();
		int newSort = locked.sortOrder();
		String newStatus = locked.status();
		boolean any = false;

		if (body.has("categoryCode")) {
			JsonNode n = body.get("categoryCode");
			if (!n.isNull()) {
				any = true;
				newCode = requireNonBlank(n.asText(), "categoryCode", 50);
				if (categoryJdbcRepository.existsOtherActiveWithCode(id, newCode)) {
					throw new BusinessException(ApiErrorCode.CONFLICT, "Mã danh mục đã tồn tại");
				}
			}
		}
		if (body.has("name")) {
			JsonNode n = body.get("name");
			if (!n.isNull()) {
				any = true;
				newName = requireNonBlank(n.asText(), "name", 255);
			}
		}
		if (body.has("description")) {
			JsonNode n = body.get("description");
			if (!n.isNull()) {
				any = true;
				newDesc = normalizeDescriptionForStore(n.asText());
			}
		}
		if (body.has("parentId")) {
			JsonNode n = body.get("parentId");
			if (!n.isNull()) {
				any = true;
				if (!n.isIntegralNumber()) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "parentId không hợp lệ",
							Map.of("parentId", "Phải là số nguyên dương"));
				}
				long pid = n.asLong();
				if (pid <= 0L) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "parentId không hợp lệ",
							Map.of("parentId", "Phải là số nguyên dương"));
				}
				if (pid == id) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "parentId không hợp lệ",
							Map.of("parentId", "Không được trỏ chính danh mục đang sửa"));
				}
				if (!categoryJdbcRepository.existsActiveId(pid)) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Danh mục cha không tồn tại",
							Map.of("parentId", "parentId không khớp bản ghi categories đang hiệu lực"));
				}
				List<CategoryParentEdgeRow> edges = categoryJdbcRepository.loadAllActiveParentEdges();
				if (wouldPutParentInDescendantSubtree(id, pid, edges)) {
					throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể đặt danh mục cha vì tạo vòng lặp phân cấp");
				}
				newParent = pid;
			}
		}
		if (body.has("sortOrder")) {
			JsonNode n = body.get("sortOrder");
			if (!n.isNull()) {
				any = true;
				if (!n.isIntegralNumber()) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "sortOrder không hợp lệ");
				}
				newSort = n.asInt();
			}
		}
		if (body.has("status")) {
			JsonNode n = body.get("status");
			if (!n.isNull()) {
				any = true;
				newStatus = normalizeStatusRequired(n.asText());
			}
		}
		if (!any) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Cần ít nhất một trường hợp lệ để cập nhật");
		}
		categoryJdbcRepository.update(id, newCode, newName, newDesc, newParent, newSort, newStatus);
		return categoryJdbcRepository.findActiveById(id)
				.map(c -> categoryJdbcRepository.toNodeResponse(c, List.of()))
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy danh mục"));
	}

	@Transactional
	public CategoryDeleteData delete(long id, Jwt jwt) {
		StockReceiptAccessPolicy.assertOwnerOnly(jwt, "Chỉ tài khoản Owner mới được xóa mềm danh mục");
		categoryJdbcRepository.lockActiveByIdForUpdate(id)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy danh mục"));
		if (categoryJdbcRepository.countActiveChildren(id) > 0L) {
			throw new BusinessException(ApiErrorCode.CONFLICT,
					"Không thể đánh dấu xóa: còn danh mục con đang hiệu lực hoặc còn sản phẩm gán vào danh mục này");
		}
		if (categoryJdbcRepository.countProductsOnCategory(id) > 0L) {
			throw new BusinessException(ApiErrorCode.CONFLICT,
					"Không thể đánh dấu xóa: còn danh mục con đang hiệu lực hoặc còn sản phẩm gán vào danh mục này");
		}
		categoryJdbcRepository.softDelete(id);
		return new CategoryDeleteData(id, true);
	}

	private static boolean wouldPutParentInDescendantSubtree(long categoryId, long newParentId,
			List<CategoryParentEdgeRow> edges) {
		Map<Long, List<Long>> byParent = new HashMap<>();
		for (CategoryParentEdgeRow e : edges) {
			if (e.parentId() != null) {
				byParent.computeIfAbsent(e.parentId(), k -> new ArrayList<>()).add(e.id());
			}
		}
		Deque<Long> dq = new ArrayDeque<>(byParent.getOrDefault(categoryId, List.of()));
		Set<Long> seen = new HashSet<>();
		while (!dq.isEmpty()) {
			Long u = dq.poll();
			if (u == null || !seen.add(u)) {
				continue;
			}
			if (u == newParentId) {
				return true;
			}
			dq.addAll(byParent.getOrDefault(u, List.of()));
		}
		return false;
	}

	private static List<CategoryFlatRow> applySearchFilter(List<CategoryFlatRow> rows, String searchRaw) {
		if (searchRaw == null) {
			return new ArrayList<>(rows);
		}
		String term = searchRaw.trim();
		if (term.isEmpty()) {
			return new ArrayList<>(rows);
		}
		Set<Long> match = new HashSet<>();
		for (CategoryFlatRow r : rows) {
			if (containsIgnoreCase(r.name(), term) || containsIgnoreCase(r.categoryCode(), term)) {
				match.add(r.id());
			}
		}
		Map<Long, Long> parentById = new HashMap<>();
		for (CategoryFlatRow r : rows) {
			parentById.put(r.id(), r.parentId());
		}
		Set<Long> allowed = new HashSet<>(match);
		for (Long m : match) {
			Long p = parentById.get(m);
			int guard = 0;
			while (p != null && guard++ < 512) {
				allowed.add(p);
				p = parentById.get(p);
			}
		}
		List<CategoryFlatRow> out = new ArrayList<>();
		for (CategoryFlatRow r : rows) {
			if (allowed.contains(r.id())) {
				out.add(r);
			}
		}
		return out;
	}

	private static boolean containsIgnoreCase(String hay, String needle) {
		if (hay == null) {
			return false;
		}
		return hay.toLowerCase(Locale.ROOT).contains(needle.toLowerCase(Locale.ROOT));
	}

	private static String normalizeListStatus(String statusRaw) {
		if (statusRaw == null || statusRaw.isBlank() || "all".equalsIgnoreCase(statusRaw.trim())) {
			return "all";
		}
		String s = statusRaw.trim();
		if ("Active".equalsIgnoreCase(s)) {
			return "Active";
		}
		if ("Inactive".equalsIgnoreCase(s)) {
			return "Inactive";
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số status không hợp lệ",
				Map.of("status", "Giá trị hợp lệ: all, Active, Inactive"));
	}

	private static String normalizeStatusOrDefault(String status) {
		if (!StringUtils.hasText(status)) {
			return "Active";
		}
		return normalizeStatusRequired(status);
	}

	private static String normalizeStatusRequired(String status) {
		String t = status.trim();
		if ("Active".equalsIgnoreCase(t)) {
			return "Active";
		}
		if ("Inactive".equalsIgnoreCase(t)) {
			return "Inactive";
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "status không hợp lệ",
				Map.of("status", "Giá trị hợp lệ: Active, Inactive"));
	}

	private static String requireNonBlank(String raw, String field, int maxLen) {
		if (raw == null || raw.isBlank()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of(field, "Không được để trống"));
		}
		String t = raw.trim();
		if (t.length() > maxLen) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of(field, "Vượt quá " + maxLen + " ký tự"));
		}
		if ("categoryCode".equals(field) && !CODE_PATTERN.matcher(t).matches()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "categoryCode không hợp lệ",
					Map.of("categoryCode", "Không được chỉ gồm khoảng trắng"));
		}
		return t;
	}

	private static String normalizeDescriptionForStore(String raw) {
		if (raw == null) {
			return null;
		}
		String t = raw.trim();
		return t.isEmpty() ? null : t;
	}
}
