-- PRD / SRS_PRD_system-audit-unified-admin-view (Approved 02/05/2026): chỉ Admin xem nhật ký hệ thống.
-- Điều chỉnh V30 (Owner + Admin = true) → Owner = false; Admin = true; Staff = false.

UPDATE roles
SET permissions = COALESCE(permissions, '{}'::jsonb) || jsonb_build_object('can_view_system_logs', FALSE)
WHERE name = 'Owner';

UPDATE roles
SET permissions = COALESCE(permissions, '{}'::jsonb) || jsonb_build_object('can_view_system_logs', TRUE)
WHERE name = 'Admin';

UPDATE roles
SET permissions = COALESCE(permissions, '{}'::jsonb) || jsonb_build_object('can_view_system_logs', FALSE)
WHERE name = 'Staff';
