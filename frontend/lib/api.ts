/**
 * Thin typed client for the Citizen Intelligence Layer backend.
 *
 * Server components reach the FastAPI backend directly through API_BASE_URL.
 * Client components use the same-origin NEXT_PUBLIC_API_URL prefix, which
 * next.config.ts rewrites to the backend at runtime.
 */

const serverBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";
const clientBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1";

export function getApiBaseUrl(): string {
  return typeof window === "undefined" ? serverBaseUrl : clientBaseUrl;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly detail?: unknown,
    readonly retryAfter?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(!init?.body || !(init.body instanceof FormData)
          ? { "Content-Type": "application/json" }
          : {}),
        ...init?.headers,
      },
    });
  } catch (cause) {
    throw new ApiError("Backend is unreachable. Is the API running?", 0, cause);
  }

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    const retryAfter = parseRetryAfter(response.headers.get("Retry-After"));
    throw new ApiError(
      `Request to ${path} failed (${response.status} ${response.statusText})`,
      response.status,
      detail,
      retryAfter,
    );
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function apiFetchBlob(
  path: string,
  init?: RequestInit,
): Promise<Blob> {
  const url = `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (cause) {
    throw new ApiError("Backend is unreachable. Is the API running?", 0, cause);
  }

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    const retryAfter = parseRetryAfter(response.headers.get("Retry-After"));
    throw new ApiError(
      `Request to ${path} failed (${response.status} ${response.statusText})`,
      response.status,
      detail,
      retryAfter,
    );
  }

  return response.blob();
}

async function readErrorDetail(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return await response.text();
  }
}

function parseRetryAfter(value: string | null): number | undefined {
  if (!value) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export interface HealthStatus {
  status: string;
}

export type ProjectStatus =
  | "PLANNED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "ON_HOLD";

export type VerificationStatus =
  | "PENDING"
  | "VERIFIED"
  | "REJECTED"
  | "UNVERIFIED";

export interface SourceReference {
  source_id: string;
  source_record_id: string;
  publisher: string;
  title: string;
  source_type: string;
  url: string;
  publication_date: string | null;
  retrieved_at: string;
  record_summary: string;
}

export interface ClaimEvidence {
  id: string;
  claim_kind: string;
  field_name: string;
  value_text: string;
  numeric_value: number | null;
  currency: string | null;
  financial_period: string | null;
  sources: SourceReference[];
}

export interface ProjectCategoryLabel {
  id: string;
  code: string;
  name: string;
}

export interface ProjectSubtypeLabel {
  id: string;
  code: string;
  name: string;
}

export interface LocationInfo {
  county_id: string;
  county: string;
  sub_county_id: string;
  sub_county: string;
  ward_id: string;
  ward: string;
}

export interface ProjectListItem {
  id: string;
  name: string;
  description: string;
  project_type: string | null;
  category: ProjectCategoryLabel;
  subtype: ProjectSubtypeLabel | null;
  status: ProjectStatus;
  location: LocationInfo;
}

export interface FinancialFact {
  kind: string;
  amount: number;
  currency: string;
  financial_period: string;
  evidence: { claim_id: string; sources: SourceReference[] };
}

export interface FinancialSummary {
  allocated: FinancialFact | null;
  committed: FinancialFact | null;
  contracted: FinancialFact | null;
  spent: FinancialFact | null;
  reported: FinancialFact | null;
}

export interface Contractor {
  id: string;
  legal_name: string;
  award_reference: string;
  contract_status: string;
  contract_start_date: string | null;
  contract_end_date: string | null;
  evidence: { claim_id: string; sources: SourceReference[] };
}

export interface ProgressInfo {
  percentage: number;
  reported_at: string;
  evidence: { claim_id: string; sources: SourceReference[] };
}

export interface TimelineInfo {
  planned_start_date: string;
  planned_completion_date: string;
  actual_start_date: string | null;
  expected_completion_date: string | null;
}

export interface ProjectAnomaly {
  type: string;
  status: string;
  message: string;
  requires_verification: boolean;
  reported_progress_percentage: number;
  spent_budget_percentage: number;
  supporting_claims: Array<{ claim_id: string; sources: SourceReference[] }>;
}

export interface SourceReferenceResponse {
  source: SourceReference;
}

export interface ProjectVerification {
  status: VerificationStatus;
  verification_date: string | null;
  recorded_at: string;
  notes: string;
  source: SourceReference | null;
}

export interface ProjectDetail {
  id: string;
  name: string;
  description: string;
  project_type: string | null;
  category: ProjectCategoryLabel;
  subtype: ProjectSubtypeLabel | null;
  status: ProjectStatus;
  location: LocationInfo;
  financial_summary: FinancialSummary;
  contractor: Contractor | null;
  progress: ProgressInfo | null;
  timeline: TimelineInfo;
  last_verified_at: string | null;
  verification: ProjectVerification | null;
  anomalies: ProjectAnomaly[];
  evidence: ClaimEvidence[];
}

export interface ProjectPage {
  items: ProjectListItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface ProjectFilters {
  page?: number;
  page_size?: number;
  county?: string;
  ward?: string;
  project_type?: string;
  category_id?: string;
  subtype_id?: string;
  status?: ProjectStatus;
  search?: string;
}

export interface CitizenComment {
  id: string;
  project_id: string;
  parent_comment_id: string | null;
  author_id: string;
  content: string;
  status: string;
  moderation_state: string;
  visibility: string;
  is_citizen_submitted: boolean;
  trust_label: string;
  created_at: string;
  updated_at: string;
}

export interface CommentReport {
  id: string;
  comment_id: string;
  reporter_id: string;
  reason: string;
  status: string;
  submitted_at: string;
}

export interface Evidence {
  id: string;
  project_id: string | null;
  comment_id: string | null;
  report_id: string | null;
  uploader_id: string;
  source_class: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  checksum_sha256: string;
  moderation_state: string;
  processing_state: string;
  visibility: string;
  is_deleted: boolean;
  uploaded_at: string;
  is_official_source: boolean;
  trust_label: string;
}

export interface EvidenceProcessingEvent {
  id: string;
  from_state: string | null;
  to_state: string;
  event_type: string;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
}

export interface EvidenceDerivedArtifact {
  id: string;
  evidence_id: string;
  artifact_type: string;
  content_hash: string | null;
  source_class: string;
  trust_classification: string;
  created_at: string;
}

export interface EvidenceProcessing {
  evidence_id: string;
  processing_state: string;
  events: EvidenceProcessingEvent[];
  derived_artifacts: EvidenceDerivedArtifact[];
}

export interface ModerationHistory {
  id: string;
  target_type: string;
  target_id: string;
  actor_id: string;
  action: string;
  reason: string;
  previous_state: string;
  resulting_state: string;
  notes: string | null;
  created_at: string;
}

export interface CitizenReport {
  id: string;
  project_id: string;
  category: string;
  status: string;
  submitted_at: string;
}

export interface ReportDetail {
  id: string;
  project_id: string;
  category: string;
  status: string;
  submitted_at: string;
  status_history: Array<{ from_status: string; to_status: string; created_at: string }>;
}

export interface ReportingChannel {
  id: string;
  office_name: string;
  channel_type: string;
  destination: string;
  display_label: string | null;
  priority: number;
}

export interface Institution {
  institution_id: string;
  institution_name: string;
  institution_role: string;
  relationship_type: string;
}

export interface InstitutionResponse {
  response_id: string;
  institution_id: string;
  institution_name: string;
  institution_role: string;
  relationship_type: string;
  content: string;
  created_at: string;
}

export interface ReportComparison {
  issue: {
    report_id: string;
    category: string;
    description: string;
    submitted_at: string;
  };
  responses: InstitutionResponse[];
}

export interface TaxonomyCategory {
  id: string;
  code: string;
  name: string;
  description: string;
  subtypes: Array<{ id: string; code: string; name: string; description: string }>;
}

export function fetchHealth(): Promise<HealthStatus> {
  return apiFetch<HealthStatus>("/health");
}

export function fetchProjects(filters: ProjectFilters = {}): Promise<ProjectPage> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return apiFetch<ProjectPage>(`/projects${query ? `?${query}` : ""}`);
}

export function fetchProject(projectId: string): Promise<ProjectDetail> {
  return apiFetch<ProjectDetail>(`/projects/${projectId}`);
}

export function fetchProjectSources(projectId: string): Promise<ClaimEvidence[]> {
  return apiFetch<ClaimEvidence[]>(`/projects/${projectId}/sources`);
}

export function fetchVerification(projectId: string): Promise<ProjectVerification | null> {
  return apiFetch<ProjectVerification | null>(`/projects/${projectId}/verification`);
}

export function fetchAnomalies(projectId: string): Promise<ProjectAnomaly[]> {
  return apiFetch<ProjectAnomaly[]>(`/projects/${projectId}/anomalies`);
}

export function fetchCategories(): Promise<TaxonomyCategory[]> {
  return apiFetch<TaxonomyCategory[]>("/project-categories");
}

export function fetchComments(projectId: string): Promise<CitizenComment[]> {
  return apiFetch<CitizenComment[]>(`/projects/${projectId}/comments`);
}

export function createComment(
  projectId: string,
  payload: { author_id: string; content: string; parent_comment_id?: string | null },
): Promise<CitizenComment> {
  return apiFetch<CitizenComment>(`/projects/${projectId}/comments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function reportComment(
  commentId: string,
  payload: { reporter_id: string; reason: string },
): Promise<CommentReport> {
  return apiFetch<CommentReport>(`/comments/${commentId}/reports`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createReport(
  projectId: string,
  payload: {
    category: string;
    description: string;
    contact_information?: string;
  },
): Promise<CitizenReport> {
  return apiFetch<CitizenReport>(`/projects/${projectId}/reports`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function uploadEvidence(
  path: string,
  form: FormData,
): Promise<Evidence> {
  return apiFetch<Evidence>(path, {
    method: "POST",
    body: form,
    headers: { Accept: "application/json" },
  });
}

export function fetchEvidence(evidenceId: string): Promise<Evidence> {
  return apiFetch<Evidence>(`/evidence/${evidenceId}`);
}

export function fetchEvidenceProcessing(evidenceId: string): Promise<EvidenceProcessing> {
  return apiFetch<EvidenceProcessing>(`/evidence/${evidenceId}/processing`);
}

export function downloadEvidenceFile(evidenceId: string): Promise<Blob> {
  return apiFetchBlob(`/evidence/${evidenceId}/download`);
}

export function fetchModerationHistory(
  target: "comments" | "evidence",
  id: string,
): Promise<ModerationHistory[]> {
  return apiFetch<ModerationHistory[]>(`/${target}/${id}/moderation-history`);
}

export function moderate(
  target: "comments" | "evidence",
  id: string,
  payload: { action: string; reason: string; notes?: string },
): Promise<ModerationHistory> {
  return apiFetch<ModerationHistory>(`/${target}/${id}/moderation`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchReport(reportId: string): Promise<ReportDetail> {
  return apiFetch<ReportDetail>(`/reports/${reportId}`);
}

export function fetchReportChannels(reportId: string): Promise<ReportingChannel[]> {
  return apiFetch<ReportingChannel[]>(`/reports/${reportId}/channels`);
}

export function fetchInstitutions(reportId: string): Promise<Institution[]> {
  return apiFetch<Institution[]>(`/reports/${reportId}/institutions`);
}

export function fetchReportResponses(reportId: string): Promise<InstitutionResponse[]> {
  return apiFetch<InstitutionResponse[]>(`/reports/${reportId}/responses`);
}

export function fetchReportComparison(reportId: string): Promise<ReportComparison> {
  return apiFetch<ReportComparison>(`/reports/${reportId}/comparison`);
}

export function fetchReportStatus(reportId: string): Promise<ReportDetail> {
  return fetchReport(reportId);
}

export function fetchReportSearch(): Promise<unknown> {
  return Promise.resolve({});
}
