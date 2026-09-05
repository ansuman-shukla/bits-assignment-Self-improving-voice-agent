/**
 * Unit tests for the usePolling custom hook.
 *
 * Uses fake timers and a mocked fetchFn to verify polling behavior without
 * making any real API calls. No network or database access occurs.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePolling } from "@/hooks/usePolling";

describe("usePolling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  /** Advance fake timers and flush React state updates inside act(). */
  async function flush(ms = 0) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(ms);
    });
  }

  it("does not poll when disabled", () => {
    const fetchFn = vi.fn().mockResolvedValue({ status: "PENDING" });
    const { result } = renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: () => false,
        enabled: false,
      })
    );

    expect(result.current.isPolling).toBe(false);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(fetchFn).not.toHaveBeenCalled();
  });

  it("starts polling immediately when enabled", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ status: "PENDING" });
    const { result } = renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: () => false,
        enabled: true,
        interval: 1000,
      })
    );

    await flush(0);

    expect(result.current.isPolling).toBe(true);
    expect(fetchFn).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual({ status: "PENDING" });
  });

  it("calls onData with the fetched result", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ value: 42 });
    const onData = vi.fn();
    renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: () => false,
        enabled: true,
        interval: 1000,
        onData,
      })
    );

    await flush(0);

    expect(onData).toHaveBeenCalledWith({ value: 42 });
  });

  it("stops polling when shouldStopPolling returns true", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ status: "COMPLETED" });
    const onComplete = vi.fn();
    const { result } = renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: (d) => d.status === "COMPLETED",
        enabled: true,
        interval: 1000,
        onComplete,
      })
    );

    await flush(0);

    expect(result.current.isPolling).toBe(false);
    expect(onComplete).toHaveBeenCalledWith({ status: "COMPLETED" });
    // Should not poll again after stopping
    await flush(2000);
    expect(fetchFn).toHaveBeenCalledTimes(1);
  });

  it("sets error and stops polling when fetchFn throws", async () => {
    const fetchFn = vi.fn().mockRejectedValue(new Error("Network error"));
    const onError = vi.fn();
    const { result } = renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: () => false,
        enabled: true,
        interval: 1000,
        onError,
      })
    );

    await flush(0);

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Network error");
    expect(result.current.isPolling).toBe(false);
    expect(onError).toHaveBeenCalled();
  });

  it("wraps non-Error rejections in an Error instance", async () => {
    const fetchFn = vi.fn().mockRejectedValue("string error");
    const { result } = renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: () => false,
        enabled: true,
        interval: 1000,
      })
    );

    await flush(0);

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("string error");
  });

  it("polls repeatedly at the configured interval", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ status: "RUNNING" });
    renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: () => false,
        enabled: true,
        interval: 1000,
      })
    );

    // Immediate poll
    await flush(0);
    expect(fetchFn).toHaveBeenCalledTimes(1);

    // Advance one interval
    await flush(1000);
    expect(fetchFn).toHaveBeenCalledTimes(2);

    // Advance another interval
    await flush(1000);
    expect(fetchFn).toHaveBeenCalledTimes(3);
  });

  it("clears the interval on unmount", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ status: "RUNNING" });
    const { unmount } = renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: () => false,
        enabled: true,
        interval: 1000,
      })
    );

    await flush(0);
    const callsBefore = fetchFn.mock.calls.length;
    unmount();

    // After unmount, advancing timers should not trigger more fetches
    await flush(5000);
    expect(fetchFn.mock.calls.length).toBe(callsBefore);
  });

  it("exposes a refetch function for manual polling", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ status: "PENDING" });
    const { result } = renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: () => false,
        enabled: false,
        interval: 1000,
      })
    );

    expect(result.current.refetch).toBeDefined();
    expect(typeof result.current.refetch).toBe("function");
  });

  it("does not start a duplicate immediate poll on rerender", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ status: "RUNNING" });
    const { rerender } = renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: () => false,
        enabled: true,
        interval: 1000,
      })
    );

    await flush(0);
    const callsAfterFirstPoll = fetchFn.mock.calls.length;

    // Rerender with same enabled state; should not start a new poll cycle
    rerender();
    await flush(0);
    // The immediate poll should not have been called again just from rerender
    expect(fetchFn.mock.calls.length).toBe(callsAfterFirstPoll);
  });

  it("uses the default interval of 3000ms when not specified", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ status: "RUNNING" });
    renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: () => false,
        enabled: true,
      })
    );

    await flush(0);
    expect(fetchFn).toHaveBeenCalledTimes(1);

    // Advancing less than 3000ms should not trigger another poll
    await flush(2999);
    expect(fetchFn).toHaveBeenCalledTimes(1);

    // Reaching 3000ms triggers the next poll
    await flush(1);
    expect(fetchFn).toHaveBeenCalledTimes(2);
  });

  it("initializes with null data, false isPolling, and null error", () => {
    const fetchFn = vi.fn().mockResolvedValue(null);
    const { result } = renderHook(() =>
      usePolling({
        fetchFn,
        shouldStopPolling: () => true,
        enabled: false,
      })
    );

    expect(result.current.data).toBeNull();
    expect(result.current.isPolling).toBe(false);
    expect(result.current.error).toBeNull();
  });
});
