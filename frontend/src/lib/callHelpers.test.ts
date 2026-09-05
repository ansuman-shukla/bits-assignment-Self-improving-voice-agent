/**
 * Unit tests for call helper functions.
 *
 * Tests status labels/colors, phone formatting, Rupee formatting,
 * transcript role counting, and risk score averaging. No API or DB calls.
 */

import { describe, it, expect } from "vitest";
import {
  getCallStatusLabel,
  getCallStatusColor,
  hasTranscript,
  isCallCompleted,
  isCallInProgress,
  formatPhoneNumber,
  formatRupeeAmount,
  countTranscriptRoles,
  getAverageRiskScore,
} from "@/lib/callHelpers";
import type { CallRecord, TranscriptMessage } from "@/types/call";

describe("getCallStatusLabel", () => {
  it("returns the correct label for each status", () => {
    expect(getCallStatusLabel("in_progress")).toBe("In Progress");
    expect(getCallStatusLabel("completed")).toBe("Completed");
    expect(getCallStatusLabel("failed")).toBe("Failed");
  });
});

describe("getCallStatusColor", () => {
  it("returns the correct color class for each status", () => {
    expect(getCallStatusColor("in_progress")).toBe("text-blue-400");
    expect(getCallStatusColor("completed")).toBe("text-green-400");
    expect(getCallStatusColor("failed")).toBe("text-red-400");
  });
});

describe("hasTranscript", () => {
  it("returns true when transcript_file is present", () => {
    expect(hasTranscript({ transcript_file: "transcript.json" })).toBe(true);
  });

  it("returns false when transcript_file is undefined", () => {
    expect(hasTranscript({ transcript_file: undefined })).toBe(false);
  });

  it("returns false when transcript_file is an empty string", () => {
    expect(hasTranscript({ transcript_file: "" })).toBe(false);
  });
});

describe("isCallCompleted", () => {
  it("returns true for completed status", () => {
    expect(isCallCompleted({ status: "completed" })).toBe(true);
  });

  it("returns false for in_progress status", () => {
    expect(isCallCompleted({ status: "in_progress" })).toBe(false);
  });

  it("returns false for failed status", () => {
    expect(isCallCompleted({ status: "failed" })).toBe(false);
  });
});

describe("isCallInProgress", () => {
  it("returns true for in_progress status", () => {
    expect(isCallInProgress({ status: "in_progress" })).toBe(true);
  });

  it("returns false for completed status", () => {
    expect(isCallInProgress({ status: "completed" })).toBe(false);
  });
});

describe("formatPhoneNumber", () => {
  it("combines country code and phone number", () => {
    expect(formatPhoneNumber("+91", "9262561716")).toBe("+919262561716");
  });

  it("works with US country code", () => {
    expect(formatPhoneNumber("+1", "5551234567")).toBe("+15551234567");
  });

  it("works with empty phone number", () => {
    expect(formatPhoneNumber("+44", "")).toBe("+44");
  });
});

describe("formatRupeeAmount", () => {
  it("formats a simple amount", () => {
    expect(formatRupeeAmount(5000)).toBe("₹5,000.00");
  });

  it("formats an amount with decimals", () => {
    expect(formatRupeeAmount(1250.5)).toBe("₹1,250.50");
  });

  it("formats zero", () => {
    expect(formatRupeeAmount(0)).toBe("₹0.00");
  });

  it("formats a large amount with Indian grouping", () => {
    // Indian numbering: 1,00,000.00
    expect(formatRupeeAmount(100000)).toBe("₹1,00,000.00");
  });

  it("formats a very large amount", () => {
    expect(formatRupeeAmount(1000000)).toBe("₹10,00,000.00");
  });
});

describe("countTranscriptRoles", () => {
  const msg = (role: TranscriptMessage["role"], message: string): TranscriptMessage => ({
    role,
    message,
    timestamp: "2025-10-04T10:00:00Z",
  });

  it("counts agent and user messages", () => {
    const transcript = [
      msg("agent", "Hello"),
      msg("user", "Hi"),
      msg("agent", "How are you?"),
      msg("user", "Fine"),
    ];
    const result = countTranscriptRoles(transcript);
    expect(result.agent).toBe(2);
    expect(result.user).toBe(2);
    expect(result.total).toBe(4);
  });

  it("returns zeros for an empty transcript", () => {
    const result = countTranscriptRoles([]);
    expect(result.agent).toBe(0);
    expect(result.user).toBe(0);
    expect(result.total).toBe(0);
  });

  it("counts only agent messages", () => {
    const transcript = [msg("agent", "A"), msg("agent", "B")];
    const result = countTranscriptRoles(transcript);
    expect(result.agent).toBe(2);
    expect(result.user).toBe(0);
  });
});

describe("getAverageRiskScore", () => {
  it("returns null when no scores are present", () => {
    expect(getAverageRiskScore({})).toBeNull();
  });

  it("returns the single score when only one is present", () => {
    const result = getAverageRiskScore({ loan_recovery_score: 75.0 });
    expect(result).toBe(75.0);
  });

  it("averages all present scores", () => {
    const result = getAverageRiskScore({
      loan_recovery_score: 80.0,
      willingness_to_pay_score: 60.0,
      escalation_risk_score: 70.0,
      customer_sentiment_score: 90.0,
      promise_to_pay_reliability_index: 50.0,
    });
    // (80 + 60 + 70 + 90 + 50) / 5 = 70
    expect(result).toBe(70.0);
  });

  it("averages a subset of scores", () => {
    const result = getAverageRiskScore({
      loan_recovery_score: 100.0,
      customer_sentiment_score: 50.0,
    });
    expect(result).toBe(75.0);
  });

  it("ignores null scores", () => {
    const result = getAverageRiskScore({
      loan_recovery_score: 80.0,
      willingness_to_pay_score: null,
      escalation_risk_score: 60.0,
    });
    // (80 + 60) / 2 = 70
    expect(result).toBe(70.0);
  });

  it("rounds to two decimal places", () => {
    const result = getAverageRiskScore({
      loan_recovery_score: 70.0,
      willingness_to_pay_score: 71.0,
      escalation_risk_score: 72.0,
    });
    // (70 + 71 + 72) / 3 = 71.0
    expect(result).toBe(71.0);
  });
});
