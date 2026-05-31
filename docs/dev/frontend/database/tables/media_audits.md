# MediaAudits Table

## 📋 Overview

**Purpose**: Media file audit trail (images, voice)  
**Use Cases**: UC12, UC13  
**Group**: AI & Media

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `file_type` | VARCHAR(20) | NOT NULL, CHECK (OCR_Image/Voice_Audio) | - | File type |
| `cloud_url` | VARCHAR(1000) | NOT NULL | - | Cloud storage URL |
| `entity_type` | VARCHAR(50) | NOT NULL | - | Entity type (polymorphic) |
| `entity_id` | INT | NOT NULL | - | Entity ID (polymorphic) |
| `file_size_bytes` | INT | NULL | - | File size in bytes |
| `mime_type` | VARCHAR(100) | NULL | - | MIME type |
| `uploaded_by` | INT | NULL, FK → Users(id) | - | User who uploaded |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Users (uploaded_by) | Child | SET NULL |

---

## 📝 Business Rules

1. `entity_type` + `entity_id` is polymorphic FK (validated at application layer)
2. Stores URLs to cloud storage (S3, Firebase, etc.)
3. Keep media records even when uploader is deleted (null uploaded_by)

---

## 📦 TypeScript Interface

```typescript
interface MediaAudit {
  id: number;
  fileType: "OCR_Image" | "Voice_Audio";
  cloudUrl: string;
  entityType: string; // 'StockReceipt', 'SalesOrder', 'Inventory'
  entityId: number;
  fileSizeBytes?: number;
  mimeType?: string;
  uploadedBy?: number; // FK → User
  createdAt: Date;

  // Relations
  uploader?: User;
}
```

---

## 💡 Polymorphic Reference Examples

```
entity_type = 'StockReceipt', entity_id = 123 → StockReceipts table
entity_type = 'SalesOrder', entity_id = 456 → SalesOrders table
entity_type = 'Inventory', entity_id = 789 → Inventory table
```
