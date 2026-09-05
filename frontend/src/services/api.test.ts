import { describe, expect, it, vi } from "vitest";

import { authApi } from "./api";

describe("auth API client", () => {
  it("targets the local backend auth endpoint", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            access_token: "test-token",
            token_type: "bearer",
          }),
          {
            status: 200,
            headers: {
              "content-type": "application/json",
            },
          },
        ),
      );

    await authApi.login({
      email: "user@example.com",
      password: "password",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/auth/login",
      expect.objectContaining({
        method: "POST",
        headers: expect.any(Headers),
      }),
    );

    fetchMock.mockRestore();
  });
});

describe("chat API client", () => {
  it("sends the exact chat request to the backend", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            query: "hello",
            answer: "hello answer",
            sources: [],
          }),
          {
            status: 200,
            headers: {
              "content-type": "application/json",
            },
          },
        ),
      );

    const { chatApi } = await import("./api");

    await chatApi.sendMessage("test-token", {
      query: "hello",
      conversation_id: "22222222-2222-4222-8222-222222222222",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          query: "hello",
          conversation_id: "22222222-2222-4222-8222-222222222222",
        }),
      }),
    );

    const init = fetchMock.mock.calls[0]?.[1];
    const headers = new Headers(init?.headers);

    expect(headers.get("Authorization")).toBe(
      "Bearer test-token",
    );
    expect(headers.get("Content-Type")).toBe(
      "application/json",
    );

    fetchMock.mockRestore();
  });
});


describe("conversation API client", () => {
  it("loads conversations with the default endpoint", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            conversations: [],
            total_count: 0,
            page: 1,
            page_size: 20,
          }),
          {
            status: 200,
            headers: {
              "content-type": "application/json",
            },
          },
        ),
      );

    const { conversationApi } = await import("./api");

    await conversationApi.getConversations("test-token");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/conversations",
      expect.objectContaining({
        headers: expect.any(Headers),
      }),
    );

    const init = fetchMock.mock.calls[0]?.[1];
    const headers = new Headers(init?.headers);

    expect(headers.get("Authorization")).toBe(
      "Bearer test-token",
    );

    fetchMock.mockRestore();
  });

  it("serializes conversation search and pagination parameters", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            conversations: [],
            total_count: 0,
            page: 2,
            page_size: 5,
          }),
          {
            status: 200,
            headers: {
              "content-type": "application/json",
            },
          },
        ),
      );

    const { conversationApi } = await import("./api");

    await conversationApi.getConversations("test-token", {
      search: "quarterly report",
      page: 2,
      page_size: 5,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/conversations?search=quarterly+report&page=2&page_size=5",
      expect.objectContaining({
        headers: expect.any(Headers),
      }),
    );

    fetchMock.mockRestore();
  });

  it("omits undefined conversation query parameters", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            conversations: [],
            total_count: 0,
            page: 1,
            page_size: 20,
          }),
          {
            status: 200,
            headers: {
              "content-type": "application/json",
            },
          },
        ),
      );

    const { conversationApi } = await import("./api");

    await conversationApi.getConversations("test-token", {
      page: 2,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/conversations?page=2",
      expect.objectContaining({
        headers: expect.any(Headers),
      }),
    );

    fetchMock.mockRestore();
  });
});
