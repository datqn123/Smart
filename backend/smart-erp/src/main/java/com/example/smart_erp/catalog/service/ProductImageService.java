package com.example.smart_erp.catalog.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import com.example.smart_erp.catalog.dto.ProductImageCreateRequest;
import com.example.smart_erp.catalog.media.CloudinaryMediaService;
import com.example.smart_erp.catalog.repository.ProductImageJdbcRepository;
import com.example.smart_erp.catalog.response.ProductImageData;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;

@Service
public class ProductImageService {

	private final ProductImageJdbcRepository productImageJdbcRepository;
	private final CloudinaryMediaService cloudinaryMediaService;

	public ProductImageService(ProductImageJdbcRepository productImageJdbcRepository,
			CloudinaryMediaService cloudinaryMediaService) {
		this.productImageJdbcRepository = productImageJdbcRepository;
		this.cloudinaryMediaService = cloudinaryMediaService;
	}

	@Transactional
	public ProductImageData addImageFromJson(int productId, ProductImageCreateRequest body) {
		requireProduct(productId);
		String url = body.url().trim();
		if (url.length() > 500) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "URL quá dài",
					Map.of("url", "Tối đa 500 ký tự"));
		}
		return persistAfterOptionalPrimaryReset(productId, url, body.sortOrderValue(), body.primaryFlag(), null, null);
	}

	@Transactional
	public ProductImageData addImageFromMultipart(int productId, MultipartFile file, int sortOrder, boolean isPrimary) {
		requireProduct(productId);
		String url = cloudinaryMediaService.uploadProductImage(file, productId);
		if (url.length() > 500) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "URL trả về vượt quá giới hạn lưu trữ",
					Map.of("file", "Liên hệ quản trị (image_url 500 ký tự)"));
		}
		Long size = file.getSize() > 0 ? file.getSize() : null;
		String mime = normalizeMime(file.getContentType());
		return persistAfterOptionalPrimaryReset(productId, url, sortOrder, isPrimary, size, mime);
	}

	private void requireProduct(int productId) {
		if (!productImageJdbcRepository.productExists(productId)) {
			throw new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy sản phẩm");
		}
	}

	/**
	 * Lưu gallery sau khi upload (Cloudinary) xong; thứ tự mảng = sortOrder 0..n-1, đúng một
	 * {@code primaryIndex} (0-based).
	 */
	@Transactional
	public List<ProductImageData> persistGalleryAfterUploads(int productId, List<String> urls, List<Long> fileSizes,
			List<String> mimeTypes, int primaryIndex) {
		requireProduct(productId);
		if (urls.isEmpty()) {
			return List.of();
		}
		if (urls.size() != fileSizes.size() || urls.size() != mimeTypes.size()) {
			throw new IllegalStateException("Gallery lists size mismatch");
		}
		if (primaryIndex < 0 || primaryIndex >= urls.size()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "primaryImageIndex không hợp lệ",
					Map.of("primaryImageIndex", "Nằm trong [0, số file - 1]"));
		}
		String primaryUrl = urls.get(primaryIndex);
		productImageJdbcRepository.clearPrimaryForProduct(productId);
		productImageJdbcRepository.updateProductMainImageUrl(productId, primaryUrl);
		List<ProductImageData> out = new ArrayList<>();
		for (int i = 0; i < urls.size(); i++) {
			String url = urls.get(i);
			if (url.length() > 500) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "URL quá dài",
						Map.of("file", "Tối đa 500 ký tự"));
			}
			boolean isPrimary = (i == primaryIndex);
			int id = productImageJdbcRepository.insertImage(productId, url, isPrimary, i, fileSizes.get(i),
					mimeTypes.get(i));
			out.add(new ProductImageData(id, productId, url, i, isPrimary));
		}
		return out;
	}

	private ProductImageData persistAfterOptionalPrimaryReset(int productId, String url, int sortOrder, boolean isPrimary,
			Long fileSizeBytes, String mimeType) {
		if (isPrimary) {
			productImageJdbcRepository.clearPrimaryForProduct(productId);
			productImageJdbcRepository.updateProductMainImageUrl(productId, url);
		}
		int id = productImageJdbcRepository.insertImage(productId, url, isPrimary, sortOrder, fileSizeBytes, mimeType);
		return new ProductImageData(id, productId, url, sortOrder, isPrimary);
	}

	private static String normalizeMime(String raw) {
		if (raw == null || raw.isBlank()) {
			return null;
		}
		int semi = raw.indexOf(';');
		return semi > 0 ? raw.substring(0, semi).trim() : raw.trim();
	}
}
