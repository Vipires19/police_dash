export type OperationalPublicationStatus = "DRAFT" | "READY" | "PUBLISHED" | "ARCHIVED";
export type ChecklistItemLevel = "OK" | "WARN" | "ERROR" | "PENDING";

export interface ChecklistItem {
  key: string;
  title: string;
  level: ChecklistItemLevel;
  detail: string;
  blocking: boolean;
}

export interface OperationalPublicationChecklist {
  items: ChecklistItem[];
  ready: boolean;
  has_errors: boolean;
  has_warnings: boolean;
  can_publish_with_risk: boolean;
}

export interface OperationalPublicationPublic {
  id: number;
  service_scale_id: number;
  scale_date: string;
  publication_number: number;
  version: number;
  status: OperationalPublicationStatus;
  created_by_id: number;
  created_by_label: string | null;
  published_by_id: number | null;
  published_by_label: string | null;
  published_at: string | null;
  generated_message: string | null;
  generated_pdf: string | null;
  change_summary: string | null;
  publish_reason: string | null;
  risk_acknowledged: boolean;
  previous_publication_id: number | null;
  checklist: OperationalPublicationChecklist | null;
  created_at: string;
  updated_at: string;
}

export interface OperationalPublicationAuditPublic {
  id: number;
  action: string;
  actor_id: number;
  actor_label: string | null;
  details: string | null;
  created_at: string;
}

export interface OperationalPublicationDetail extends OperationalPublicationPublic {
  snapshot: Record<string, unknown> | null;
  audits: OperationalPublicationAuditPublic[];
}

export interface OperationalPublicationHistoryItem {
  id: number;
  service_scale_id: number;
  scale_date: string;
  publication_number: number;
  version: number;
  status: OperationalPublicationStatus;
  published_by_label: string | null;
  published_at: string | null;
  publish_reason: string | null;
  change_summary: string | null;
  risk_acknowledged: boolean;
}

export interface OperationalPublicationHistoryResponse {
  items: OperationalPublicationHistoryItem[];
  total: number;
}

export interface OperationalPublicationCenterDay {
  scale_date: string;
  service_scale_id: number | null;
  scale_title: string | null;
  scale_status: string | null;
  active_publication: OperationalPublicationPublic | null;
  checklist: OperationalPublicationChecklist | null;
  latest_published: OperationalPublicationHistoryItem | null;
}
