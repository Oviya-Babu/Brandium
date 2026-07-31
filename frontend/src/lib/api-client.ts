/**
 * Thin typed client for the backend API (CLAUDE.md §6 — "typed API
 * client, shared with backend Pydantic-derived types"). Only the health
 * check is wired up in this milestone; every future endpoint's request/
 * response types should be added here, not scattered across components.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/healthz`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}
