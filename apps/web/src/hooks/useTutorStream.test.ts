import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useTutorStream } from "./useTutorStream";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  React.createElement(QueryClientProvider, { client: queryClient }, children)
);

describe("useTutorStream", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("initializes with empty messages and idle state", () => {
    const { result } = renderHook(() => useTutorStream(), { wrapper });
    expect(result.current.messages).toEqual([]);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.limitInfo).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("handles 429 rate limit response gracefully without throwing", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => ({ detail: "Too many requests. Please slow down." }),
    });

    const { result } = renderHook(() => useTutorStream(), { wrapper });

    await act(async () => {
      await result.current.sendMessage("Why is my code failing?");
    });

    expect(result.current.isStreaming).toBe(false);
    expect(result.current.limitInfo).toEqual({
      reason: "user_rate_limit",
      message: "Too many requests. Please slow down.",
    });
    expect(result.current.error).toBeNull();
  });

  it("clears limit state via clearLimit", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => ({ detail: "Too many requests." }),
    });

    const { result } = renderHook(() => useTutorStream(), { wrapper });

    await act(async () => {
      await result.current.sendMessage("Hello");
    });

    expect(result.current.limitInfo).not.toBeNull();

    act(() => {
      result.current.clearLimit();
    });

    expect(result.current.limitInfo).toBeNull();
  });
});
