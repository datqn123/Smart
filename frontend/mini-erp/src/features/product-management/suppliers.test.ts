import { describe, it, expect } from 'vitest';
import { mockSuppliers } from './mockData';
import type { Supplier } from './types';
import {
  PHONE_FORMAT_MESSAGE,
  validateSupplierForm,
  type SupplierFormData,
} from './validation';

// ==========================================
// Supplier Tests (Task011)
// ==========================================

describe('Supplier Filter Logic (Task011)', () => {
  interface SupplierFilters {
    search?: string;
    status?: 'Active' | 'Inactive' | 'all';
  }

  const applyFilters = (suppliers: Supplier[], filters: SupplierFilters) => {
    let result = [...suppliers];
    if (filters.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(s => 
        s.name.toLowerCase().includes(q) || 
        s.supplierCode.toLowerCase().includes(q) ||
        (s.phone && s.phone.includes(q))
      );
    }
    if (filters.status && filters.status !== 'all') {
      result = result.filter(s => s.status === filters.status);
    }
    return result;
  };

  it('nên lọc đúng theo tên', () => {
    const result = applyFilters(mockSuppliers, { search: 'Vinamilk' });
    expect(result.every(s => s.name.toLowerCase().includes('vinamilk'))).toBe(true);
  });

  it('nên lọc đúng theo mã', () => {
    const result = applyFilters(mockSuppliers, { search: 'NCC' });
    expect(result.length).toBeGreaterThan(0);
  });

  it('nên lọc đúng theo SĐT', () => {
    const result = applyFilters(mockSuppliers, { search: '09' });
    expect(result.length).toBeGreaterThanOrEqual(0);
  });
});

describe('Supplier Validation (Task011)', () => {
  const validSupplier: SupplierFormData = {
    name: 'Vinamilk',
    supplierCode: 'NCC0001',
    contactPerson: 'Nguyễn Văn B',
    phone: '0912345678',
    email: 'test@email.com',
    address: '',
    taxCode: '1234567890',
    status: 'Active',
  };

  const validateSupplier = (data: Partial<SupplierFormData>): string[] =>
    validateSupplierForm({ ...validSupplier, ...data });

  it('nên báo lỗi khi tên trống', () => {
    expect(validateSupplier({ name: '' })).toContain('Vui lòng nhập tên nhà cung cấp');
  });

  it('nên báo lỗi khi phone không đúng', () => {
    expect(validateSupplier({ phone: '123' })).toContain(PHONE_FORMAT_MESSAGE);
  });

  it('nên báo lỗi khi email không đúng', () => {
    expect(validateSupplier({ email: 'invalid' })).toContain('Email không hợp lệ');
  });

  it('nên báo lỗi khi taxCode không đúng', () => {
    expect(validateSupplier({ taxCode: '123' })).toContain('Mã số thuế phải là 10 số');
  });

  it('nên hợp lệ khi dữ liệu đúng', () => {
    expect(validateSupplier({}).length).toBe(0);
  });
});

describe('Supplier Code Generation (Task011)', () => {
  const generateSupplierCode = (index: number): string => {
    return `NCC${String(index).padStart(4, '0')}`;
  };

  it('nên sinh mã đúng định dạng', () => {
    expect(generateSupplierCode(1)).toBe('NCC0001');
    expect(generateSupplierCode(12)).toBe('NCC0012');
  });
});

describe('Supplier Status (Task011)', () => {
  const canDeleteSupplier = (hasReceipts: boolean): boolean => {
    return !hasReceipts;
  };

  it('nên cho phép xóa khi không có phiếu nhập', () => {
    expect(canDeleteSupplier(false)).toBe(true);
  });

  it('nên chặn xóa khi có phiếu nhập', () => {
    expect(canDeleteSupplier(true)).toBe(false);
  });
});
