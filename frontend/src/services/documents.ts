import { ApiError } from "./api";
import type {
  DocumentItem,
  DocumentListResponse,
} from "../types/documents";

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

type DocumentListParams = {
  search?: string;
  page?: number;
  page_size?: number;
};

function listDocuments(token: string): Promise<DocumentItem[]>;
function listDocuments(
  token: string,
  params: DocumentListParams,
): Promise<DocumentListResponse>;
async function listDocuments(
  token: string,
  params?: DocumentListParams,
): Promise<DocumentItem[] | DocumentListResponse> {
  if (params === undefined) {
    const response = await authenticatedRequest(
      "/documents",
      token,
    ) as DocumentListResponse;

    return response.items;
  }

  const query = new URLSearchParams();

  if (params.search !== undefined) {
    query.set("search", params.search);
  }

  if (params.page !== undefined) {
    query.set("page", String(params.page));
  }

  if (params.page_size !== undefined) {
    query.set("page_size", String(params.page_size));
  }

  const queryString = query.toString();
  const path = queryString
    ? `/documents?${queryString}`
    : "/documents";

  return authenticatedRequest(
    path,
    token,
  ) as Promise<DocumentListResponse>;
}

export const documentsApi = {
  list: listDocuments,

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

  delete(token: string, documentId: string) {
    return authenticatedRequest(
      `/documents/${documentId}`,
      token,
      {
        method: "DELETE",
      },
    ) as Promise<null>;
  },
};
