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
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch (cause) {
    throw new ApiError(
      "Backend is unreachable. Is the API running?",
      0,
      cause,
    );
  }
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new ApiError(
      `Request to ${path} failed (${response.status} ${response.statusText})`,
      response.status,
      detail,
    );
  }
  return (await response.json()) as T;
}

async function readErrorDetail(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return await response.text();
  }
}

export interface HealthStatus {
  status: string;
}

export function fetchHealth(): Promise<HealthStatus> {
  return apiFetch<HealthStatus>("/health");
}