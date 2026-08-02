/**
 * Typed client for the backend API (CLAUDE.md §6). No mocked data
 * anywhere in this file or its callers — every function is a real fetch
 * against the FastAPI backend built in this pass.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function actorHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  return {
    "X-User-Id": localStorage.getItem("brandium_user_id") ?? "",
    "X-Organization-Id": localStorage.getItem("brandium_org_id") ?? "",
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { ...actorHeaders(), ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export interface HealthResponse {
  status: string;
}
export const getHealth = () => request<HealthResponse>("/healthz");

/** Pre-Phase-C session bootstrap — see `backend/src/api/routers/session.py`'s
 * module docstring: a real lookup, not simulated authentication. There
 * is no password check yet; this exists only so "Log in" resolves a
 * returning user's real identity instead of faking a credential check. */
export interface SessionLookup {
  user_id: string;
  org_id: string;
  org_name: string;
  email: string;
}
export const lookupSession = (email: string) =>
  request<SessionLookup>(`/session/lookup?email=${encodeURIComponent(email)}`);

export interface Organization {
  id: string;
  name: string;
  status: string;
  created_at: string;
}
export const createOrganization = (name: string) =>
  request<Organization>("/organizations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }) });
export const getOrganization = (id: string) => request<Organization>(`/organizations/${id}`);

export interface Workspace {
  id: string;
  org_id: string;
  name: string;
}
export const createWorkspace = (orgId: string, name: string) =>
  request<Workspace>(`/organizations/${orgId}/workspaces`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }) });

export interface AppUser {
  id: string;
  org_id: string;
  email: string;
}
export const createUser = (orgId: string, email: string) =>
  request<AppUser>(`/organizations/${orgId}/users`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }) });

export interface Brand {
  id: string;
  org_id: string;
  workspace_id: string;
  name: string;
  status: string;
  active_genome_version_id: string | null;
  active_policy_version_id: string | null;
}
export const createBrand = (workspaceId: string, name: string) =>
  request<Brand>("/brands", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspace_id: workspaceId, name }) });
export const getBrand = (id: string) => request<Brand>(`/brands/${id}`);
export const listBrands = (orgId: string) => request<Brand[]>(`/organizations/${orgId}/brands`);

export interface AnalysisRunSummary {
  id: string;
  status: "queued" | "running" | "complete" | "failed";
  failure_reason: string | null;
  started_at: string | null;
  completed_at: string | null;
  asset_name: string;
  asset_modality: "text" | "image";
  score: number | null;
  verdict: string | null;
}
export const listAnalysisRuns = (brandId: string) =>
  request<AnalysisRunSummary[]>(`/brands/${brandId}/analysis-runs`);

export interface GenomeSummary {
  id: string;
  brand_id: string;
  version_number: number;
  status: string;
  activated_by: string | null;
}

export interface GenomeCompileJob {
  job_id: string;
}
export interface GenomeCompileStatus {
  stage: "queued" | "extracting_candidates" | "consolidating" | "assembling_draft" | "complete" | "failed";
  error: string | null;
  genome: GenomeSummary | null;
}
/**
 * Dispatches Genome compilation to the Celery-backed runtime and returns
 * immediately with a job id — compilation itself (one LLM call per
 * ingested Brand History item) used to block this same request, which
 * is why it could look "hung" on anything but a handful of documents.
 * Poll `getGenomeCompileStatus` with the returned `job_id` instead of
 * awaiting a single long response.
 */
export const compileGenomeDraft = (brandId: string) =>
  request<GenomeCompileJob>(`/brands/${brandId}/genomes`, { method: "POST" });
export const getGenomeCompileStatus = (brandId: string, jobId: string) =>
  request<GenomeCompileStatus>(`/brands/${brandId}/genomes/compile-status/${jobId}`);
export const submitGenomeForReview = (brandId: string, genomeId: string) =>
  request<GenomeSummary>(`/brands/${brandId}/genomes/${genomeId}/submit-for-review`, { method: "POST" });
export const activateGenome = (brandId: string, genomeId: string) =>
  request<GenomeSummary>(`/brands/${brandId}/genomes/${genomeId}/activate`, { method: "POST" });

export interface GenomeTree {
  genome_id: string;
  categories: {
    id: string;
    name: string;
    components: { id: string; name: string; assertions: { id: string; content: string; confidence: number; status: string }[] }[];
  }[];
}
export const getGenomeTree = (brandId: string, genomeId: string) =>
  request<GenomeTree>(`/brands/${brandId}/genomes/${genomeId}/tree`);

export interface BrandHistoryItem {
  id: string;
  brand_id: string;
  source_type: string;
  modality: string;
  authority_level: string;
  era_tag: string | null;
  storage_ref: string;
}
export const ingestBrandHistory = (brandId: string, formData: FormData) =>
  request<BrandHistoryItem>(`/brands/${brandId}/history`, { method: "POST", body: formData });
export const getBrandHistory = (brandId: string) => request<BrandHistoryItem[]>(`/brands/${brandId}/history`);

/** `storage_ref` is `{org_id}/{prefix}/{uuid}-{original_filename}` — the
 * original filename is the only human-readable label available without
 * exposing a direct-to-storage download route (object access is always
 * mediated through the backend, never direct). A UUID is always exactly
 * 36 characters, so the filename starts right after it — splitting on
 * every `-` instead (the previous approach) breaks because the UUID
 * itself contains four hyphens, leaving most of the UUID stuck onto
 * the front of the "label". */
export function brandHistoryLabel(item: BrandHistoryItem): string {
  const lastSegment = item.storage_ref.split("/").at(-1) ?? item.storage_ref;
  const looksLikeUuidPrefix = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-/i.test(lastSegment);
  return looksLikeUuidPrefix ? lastSegment.slice(37) : lastSegment;
}

export interface PolicySummary {
  id: string;
  brand_id: string;
  version_number: number;
  status: string;
  rules: {
    category_weights: Record<string, number>;
    critical_rules: unknown[];
    verdict_thresholds: { min_score: number; max_score: number; verdict: string }[];
    improvement_threshold: number;
  } | null;
}
export const createPolicy = (brandId: string, rules: Record<string, unknown>) =>
  request<PolicySummary>(`/brands/${brandId}/policies`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ rules }) });
export const getPolicy = (brandId: string, policyId: string) =>
  request<PolicySummary>(`/brands/${brandId}/policies/${policyId}`);
export const activatePolicy = (brandId: string, policyId: string) =>
  request<PolicySummary>(`/brands/${brandId}/policies/${policyId}/activate`, { method: "POST" });

export const createCampaign = (brandId: string, name: string) =>
  request<{ id: string }>("/campaigns", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ brand_id: brandId, name }) });
export const createAsset = (campaignId: string, name: string, modality: "text" | "image") =>
  request<{ id: string }>(`/campaigns/${campaignId}/assets?name=${encodeURIComponent(name)}&modality=${modality}`, { method: "POST" });
export const uploadAssetVersion = (assetId: string, formData: FormData) =>
  request<{ id: string }>(`/assets/${assetId}/versions`, { method: "POST", body: formData });

/** A plain `<img src>` can't carry the `X-User-Id`/`X-Organization-Id`
 * headers every other request uses instead of cookies — object access
 * is mediated through the backend (never a public URL), so the caller
 * fetches the bytes here and renders them via `URL.createObjectURL`. */
export async function getAssetVersionBlobUrl(versionId: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/asset-versions/${versionId}/content`, { headers: actorHeaders() });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export interface AnalysisRun {
  id: string;
  asset_version_id: string;
  genome_version_id: string;
  policy_version_id: string;
  status: "queued" | "running" | "complete" | "failed";
  failure_reason: string | null;
  started_at: string | null;
  completed_at: string | null;
  brand_id: string;
  asset_name: string;
  asset_modality: "text" | "image";
}
export const triggerAnalysis = (assetVersionId: string) =>
  request<AnalysisRun>("/analysis-runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ asset_version_id: assetVersionId }) });
export const getAnalysisRun = (runId: string) => request<AnalysisRun>(`/analysis-runs/${runId}`);
export interface EvidenceItem {
  id: string;
  assertion_id: string;
  alignment_indicator: string;
  confidence: number;
  observed_characteristic: { description?: string } | null;
  source_observation_ids: string[];
}
export const getEvidence = (runId: string) => request<EvidenceItem[]>(`/analysis-runs/${runId}/evidence`);

export interface RecommendationItem {
  id: string;
  component_id: string;
  text: string;
  priority: number;
  related_evidence_ids: string[];
}
export const getRecommendations = (runId: string) => request<RecommendationItem[]>(`/analysis-runs/${runId}/recommendations`);

interface ExplainabilityResult {
  value: number;
  coverage: number;
  raw_confidence: number;
  reported_confidence: number;
}
/** Shape of the evidence nested inside `/explainability`'s assertion tree
 * (`explainability_service.py`'s `assertion_evidence` dicts) — distinct
 * from the flat `EvidenceItem` returned by `/analysis-runs/{id}/evidence`:
 * this one is keyed `evidence_id`, not `id`. */
export interface ExplainabilityEvidence {
  evidence_id: string;
  alignment_indicator: string;
  confidence: number;
  observed_characteristic: { description?: string } | null;
  source_observation_ids: string[];
}
export interface ExplainabilityAssertion {
  id: string;
  content: string;
  result: ExplainabilityResult | null;
  source_reference_ids: string[];
  evidence: ExplainabilityEvidence[];
}
export interface ExplainabilityComponent {
  id: string;
  name: string;
  result: ExplainabilityResult | null;
  assertions: ExplainabilityAssertion[];
}
export interface ExplainabilityCategory {
  id: string;
  name: string;
  result: ExplainabilityResult | null;
  components: ExplainabilityComponent[];
}
export interface ExplainabilityChain {
  overall: ExplainabilityResult | null;
  score: number;
  verdict: string;
  verdict_source: string;
  brand_id: string;
  asset: { id: string; name: string; modality: string };
  categories: ExplainabilityCategory[];
}
export const getExplainability = (runId: string) => request<ExplainabilityChain>(`/analysis-runs/${runId}/explainability`);

export interface ReportRecord {
  id: string;
  analysis_run_id: string;
  decision_id: string;
  review_status: string;
  flag_reason: string | null;
}
export const getReportForRun = (runId: string) => request<ReportRecord>(`/reports/by-run/${runId}`);
export const approveReport = (reportId: string) => request<ReportRecord>(`/reports/${reportId}/approve`, { method: "POST" });
export const flagReport = (reportId: string, reason: string) =>
  request<ReportRecord>(`/reports/${reportId}/flag`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason }) });

/** Phase 4 §11's real-time execution view — the pipeline stage plus every
 * Work Unit's state, backing the Live Analysis Progress screen. */
export type PipelineStage =
  | "queued"
  | "applicability"
  | "planning"
  | "worker_execution"
  | "evidence_fusion"
  | "completeness_verification"
  | "decision_engine"
  | "recommendation_generation"
  | "report_ready"
  | "complete"
  | "failed";

export interface WorkUnitProgress {
  work_unit_id: string;
  worker_type: string;
  assertion_ids: string[];
  state: "assigned" | "executing" | "succeeded" | "failed" | "timed_out";
}

export interface AnalysisProgress {
  run_status: AnalysisRun["status"];
  stage: PipelineStage;
  work_units: WorkUnitProgress[];
  counts: Record<string, number>;
}
export const getAnalysisProgress = (runId: string) => request<AnalysisProgress>(`/analysis-runs/${runId}/progress`);
