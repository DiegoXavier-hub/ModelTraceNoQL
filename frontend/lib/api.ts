export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export type ApiResult<T> = {
  data?: T;
  error?: string;
  status: number;
  detail?: unknown;
};

function logApiFailure(
  method: string,
  path: string,
  status: number,
  body: unknown,
  errorMessage: string
) {
  if (typeof console === "undefined") return;
  try {
    console.groupCollapsed(
      `%c[ModelTrace API] ${method} ${path} -> ${status} ${errorMessage}`,
      "color:#f87171;font-weight:600;"
    );
    console.log("status:", status);
    console.log("error:", errorMessage);
    console.log("response body:", body);
    console.log("url:", `${API_URL}${path}`);
    console.groupEnd();
  } catch {
    // ignore logging errors
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<ApiResult<T>> {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const method = (options.method || "GET").toUpperCase();

  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      cache: "no-store",
      credentials: "include"
    });
    const text = await response.text();
    let json: unknown = null;
    if (text) {
      try {
        json = JSON.parse(text);
      } catch {
        json = text;
      }
    }
    if (!response.ok) {
      const errorMessage =
        (typeof json === "object" && json !== null && "detail" in json
          ? String((json as { detail?: unknown }).detail ?? "")
          : "") || response.statusText || `HTTP ${response.status}`;
      logApiFailure(method, path, response.status, json, errorMessage);
      return {
        status: response.status,
        error: errorMessage,
        detail: json
      };
    }
    return { status: response.status, data: json as T };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unexpected error";
    logApiFailure(method, path, 0, error, errorMessage);
    return {
      status: 0,
      error: errorMessage,
      detail: error
    };
  }
}
