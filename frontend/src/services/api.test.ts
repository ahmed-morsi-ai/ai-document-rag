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
