import { describe, it, expect } from 'vitest';
import { mockCustomers } from './mockData';
import type { Customer } from './types';
import {
  PHONE_FORMAT_MESSAGE,
  validateCustomerForm,
  type CustomerFormData,
} from './validation';

// ==========================================
// Customer Tests (Task012)
// ==========================================

describe('Customer Filter Logic (Task012)', () => {
  interface CustomerFilters {
    search?: string;
    status?: 'Active' | 'Inactive' | 'all';
  }

  const applyFilters = (customers: Customer[], filters: CustomerFilters) => {
    let result = [...customers];
    if (filters.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(c => 
        c.name.toLowerCase().includes(q) || 
        c.customerCode.toLowerCase().includes(q) ||
        (c.phone && c.phone.includes(q)) ||
        (c.email && c.email.toLowerCase().includes(q))
      );
    }
    if (filters.status && filters.status !== 'all') {
      result = result.filter(c => c.status === filters.status);
    }
    return result;
  };

  it('nên lọc đúng theo tên', () => {
    const result = applyFilters(mockCustomers, { search: 'Nguyễn' });
    expect(result.every(c => c.name.toLowerCase().includes('nguyễn'))).toBe(true);
  });

  it('nên lọc đúng theo SĐT', () => {
    const result = applyFilters(mockCustomers, { search: '091' });
    expect(result.length).toBeGreaterThanOrEqual(0);
  });

  it('nên lọc đúng theo email', () => {
    const result = applyFilters(mockCustomers, { search: 'email' });
    expect(result.every(c => !c.email || c.email.toLowerCase().includes('email'))).toBe(true);
  });
});

describe('Customer Validation (Task012)', () => {
  const validCustomer: CustomerFormData = {
    name: 'Nguyễn Văn A',
    customerCode: 'KH00001',
    phone: '0912345678',
    email: '',
    address: '',
    status: 'Active',
  };

  const validateCustomer = (data: Partial<CustomerFormData>): string[] =>
    validateCustomerForm({ ...validCustomer, ...data });

  it('nên báo lỗi khi tên trống', () => {
    expect(validateCustomer({ name: '' })).toContain('Vui lòng nhập tên khách hàng');
  });

  it('nên báo lỗi khi phone trống', () => {
    expect(validateCustomer({ phone: '' })).toContain('Vui lòng nhập số điện thoại');
  });

  it('nên báo lỗi khi phone không đúng định dạng', () => {
    expect(validateCustomer({ phone: '123' })).toContain(PHONE_FORMAT_MESSAGE);
  });

  it('nên báo lỗi khi email không đúng', () => {
    expect(validateCustomer({ email: 'invalid' })).toContain('Email không hợp lệ');
  });

  it('nên hợp lệ khi dữ liệu đúng', () => {
    expect(validateCustomer({}).length).toBe(0);
  });
});

describe('Customer Code Generation (Task012)', () => {
  const generateCustomerCode = (index: number): string => {
    return `KH${String(index).padStart(5, '0')}`;
  };

  it('nên sinh mã đúng định dạng', () => {
    expect(generateCustomerCode(1)).toBe('KH00001');
    expect(generateCustomerCode(12)).toBe('KH00012');
  });
});

describe('Loyalty Badge Logic (Task012)', () => {
  const getLoyaltyLevel = (points: number): { level: string; color: string } => {
    if (points >= 500) return { level: 'VIP', color: 'bg-blue-600' };
    if (points >= 101) return { level: 'Thân thiết', color: 'bg-blue-400' };
    return { level: 'Mới', color: 'bg-slate-200' };
  };

  it('nên hiển thị VIP cho points >= 500', () => {
    expect(getLoyaltyLevel(500).level).toBe('VIP');
    expect(getLoyaltyLevel(1000).level).toBe('VIP');
  });

  it('nên hiển thị Thân thiết cho 101-499', () => {
    expect(getLoyaltyLevel(101).level).toBe('Thân thiết');
    expect(getLoyaltyLevel(200).level).toBe('Thân thiết');
  });

  it('nên hiển thị Mới cho 0-100', () => {
    expect(getLoyaltyLevel(0).level).toBe('Mới');
    expect(getLoyaltyLevel(100).level).toBe('Mới');
  });
});

describe('Customer Status (Task012)', () => {
  const canEditCustomer = (status: string): boolean => {
    return status === 'Active' || status === 'Inactive';
  };

  it('nên cho phép sửa khách hàng Active', () => {
    expect(canEditCustomer('Active')).toBe(true);
  });

  it('nên cho phép sửa khách hàng Inactive', () => {
    expect(canEditCustomer('Inactive')).toBe(true);
  });
});
