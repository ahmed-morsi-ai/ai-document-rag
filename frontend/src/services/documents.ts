import { ApiError } from "./api";
import type { DocumentItem } from "../types/documents";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

async function parseResponse(
  response: Response,
): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  return contentType.includes("application/json")
    ? response.json()
    : null;
}

function getMessage(payload: unknown): string {
  if (
    typeof payload === "object" &&
    payload !== null &&
    "detail" in payload
  ) {
    const detail = (
      payload as {
        detail?: string | Array<{ msg?: string }>;
      }
    ).detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail[0]?.msg ?? "Request validation failed";
    }
  }

  return "Request failed";
}

async function authenticatedRequest(
  path: string,
  token: string,
  init: RequestInit = {},
) {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...init,
      headers,
    },
  );

  const payload = await parseResponse(response);

  if (!response.ok) {
    throw new ApiError(
      getMessage(payload),
      response.status,
    );
  }

  return payload;
}

export const documentsApi = {
  list(token: string) {
    return authenticatedRequest(
      "/documents",
      token,
    ) as Promise<DocumentItem[]>;
  },

  upload(
    token: string,
    file: File,
  ) {
    const formData = new FormData();
    formData.append("file", file);

    return authenticatedRequest(
      "/documents/upload",
      token,
      {
        method: "POST",
        body: formData,
      },
    ) as Promise<DocumentItem>;
  },
};
