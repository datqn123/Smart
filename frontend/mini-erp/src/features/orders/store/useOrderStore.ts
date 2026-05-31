import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { OrderItem } from '../types'

type CartItem = OrderItem

interface OrderState {
  cart: CartItem[];
  customerId: number | null;
  customerName: string;
  discount: number;
  voucherCode: string | null;
  
  // Actions
  addItem: (item: CartItem) => void;
  removeItem: (productId: number, unitId: number) => void;
  updateQuantity: (productId: number, unitId: number, quantity: number) => void;
  setCustomer: (id: number | null, name: string) => void;
  setDiscount: (amount: number) => void;
  setVoucher: (code: string | null) => void;
  clearCart: () => void;
  
  // Selectors/Computed
  getTotal: () => number;
  getFinalTotal: () => number;
}

export const useOrderStore = create<OrderState>()(
  persist(
    (set, get) => ({
      cart: [],
      customerId: null,
      customerName: "Khách lẻ",
      discount: 0,

      addItem: (item) => set((state) => {
        const existing = state.cart.find(
          (i) => i.productId === item.productId && i.unitId === item.unitId
        )
        if (existing) {
          return {
            cart: state.cart.map((i) =>
              i.productId === item.productId && i.unitId === item.unitId
                ? {
                    ...i,
                    quantity: i.quantity + item.quantity,
                    lineTotal: (i.quantity + item.quantity) * i.unitPrice,
                  }
                : i
            ),
          }
        }
        return { cart: [...state.cart, item] }
      }),

      removeItem: (productId, unitId) =>
        set((state) => ({
          cart: state.cart.filter((i) => !(i.productId === productId && i.unitId === unitId)),
        })),

      updateQuantity: (productId, unitId, quantity) =>
        set((state) => ({
          cart: state.cart.map((i) =>
            i.productId === productId && i.unitId === unitId
              ? {
                  ...i,
                  quantity: Math.max(1, quantity),
                  lineTotal: Math.max(1, quantity) * i.unitPrice,
                }
              : i
          ),
        })),

      setCustomer: (id, name) => set({ customerId: id, customerName: name }),
      
      setDiscount: (amount) => set({ discount: amount }),

      setVoucher: (code) => set({ voucherCode: code }),

      clearCart: () => set({ cart: [], customerId: null, customerName: "Khách lẻ", discount: 0, voucherCode: null }),

      getTotal: () => {
        return get().cart.reduce((sum, item) => sum + item.lineTotal, 0);
      },

      /** Tạm tính sau giảm giá tay; giảm voucher do BE tính khi checkout (Task060). */
      getFinalTotal: () => {
        const total = get().getTotal()
        const baseDiscount = get().discount
        return Math.max(0, total - baseDiscount)
      },
    }),
    {
      name: "pos-cart-storage-v2",
    }
  )
)
