import type {
  ChatRequest,
  ChatResponse,
  ConversationHistoryResponse,
  ConversationListParams,
  ConversationListResponse,
} from "../types/conversations";

import type {
  ApiErrorShape,
  AuthCredentials,
  TokenResponse,
  User,
} from "../types/auth";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getErrorMessage(payload: ApiErrorShape | null): string {
  if (!payload?.detail) return "Request failed";
  if (typeof payload.detail === "string") return payload.detail;
  return payload.detail[0]?.msg ?? "Request validation failed";
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
    });
  } catch {
    throw new ApiError(
      "Unable to reach the backend. Check that the API is running.",
      0,
    );
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    throw new ApiError(getErrorMessage(payload), response.status);
  }

  return payload as T;
}

export const authApi = {
  login(credentials: AuthCredentials) {
    return request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  },

  register(credentials: AuthCredentials) {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  },

  me(token: string) {
    return request<User>("/auth/me", {}, token);
  },
};


export const chatApi = {
  sendMessage(token: string, chatRequest: ChatRequest) {
    return request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify(chatRequest),
    }, token);
  },
};

export const conversationApi = {
  getConversations(
    token: string,
    params: ConversationListParams = {},
  ) {
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
      ? `/conversations?${queryString}`
      : "/conversations";

    return request<ConversationListResponse>(path, {}, token);
  },

  getConversationMessages(
    token: string,
    conversationId: string,
  ) {
    return request<ConversationHistoryResponse>(
      `/conversations/${conversationId}/messages`,
      {},
      token,
    );
  },

  deleteConversation(token: string, conversationId: string) {
    return request<void>(
      `/conversations/${conversationId}`,
      {
        method: "DELETE",
      },
      token,
    );
  },
};
