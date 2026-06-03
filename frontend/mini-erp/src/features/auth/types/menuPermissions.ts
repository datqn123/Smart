/**
 * Cùng nine keys với {@code MenuPermissionClaims} (BE Task101) / claim `mp` trong JWT.
 */
export type MenuPermissions = {
  can_view_dashboard: boolean
  can_use_ai: boolean
  can_manage_inventory: boolean
  can_manage_products: boolean
  /** SRS Task048 / JWT `mp` — quản lý KH tách với sản phẩm. */
  can_manage_customers: boolean
  can_manage_orders: boolean
  can_approve: boolean
  can_view_finance: boolean
  can_manage_staff: boolean
  can_configure_alerts: boolean
  can_manage_custom_builder: boolean
  can_use_custom_entities: boolean
}
