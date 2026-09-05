/**
 * Unit tests for evaluation helper functions.
 *
 * These tests cover pure functions that compute score averages, pick color
 * classes, and classify evaluation state. No API or database calls are made.
 */

import { describe, it, expect } from "vitest";
import {
  getAverageScore,
  getScoreColor,
  getStatusLabel,
  isCompletedWithScores,
  hasFailedWithError,
  countTranscriptSpeakers,
} from "@/lib/evaluationHelpers";
import type { Evaluation, EvaluationScores } from "@/types/evaluation";

const scores = (task: number, eff: number): EvaluationScores => ({
  task_completion: task,
  conversation_efficiency: eff,
});

describe("getAverageScore", () => {
  it("returns the rounded average of both scores", () => {
    expect(getAverageScore(scores(80, 70))).toBe(75);
  });

  it("rounds to the nearest integer", () => {
    expect(getAverageScore(scores(81, 82))).toBe(82); // 81.5 -> 82 (round half up)
  });

  it("returns 0 when both scores are 0", () => {
    expect(getAverageScore(scores(0, 0))).toBe(0);
  });

  it("returns 100 when both scores are 100", () => {
    expect(getAverageScore(scores(100, 100))).toBe(100);
  });

  it("returns null when scores are undefined", () => {
    expect(getAverageScore(undefined)).toBeNull();
  });

  it("returns null when scores are null", () => {
    expect(getAverageScore(null)).toBeNull();
  });
});

describe("getScoreColor", () => {
  it("returns green for scores >= 80", () => {
    expect(getScoreColor(80)).toBe("text-green-400");
    expect(getScoreColor(100)).toBe("text-green-400");
  });

  it("returns yellow for scores >= 60 and < 80", () => {
    expect(getScoreColor(60)).toBe("text-yellow-400");
    expect(getScoreColor(79)).toBe("text-yellow-400");
  });

  it("returns red for scores < 60", () => {
    expect(getScoreColor(59)).toBe("text-red-400");
    expect(getScoreColor(0)).toBe("text-red-400");
  });

  it("returns red for negative scores", () => {
    expect(getScoreColor(-1)).toBe("text-red-400");
  });
});

describe("getStatusLabel", () => {
  it("returns the correct label for each status", () => {
    expect(getStatusLabel("PENDING")).toBe("Pending");
    expect(getStatusLabel("RUNNING")).toBe("Running");
    expect(getStatusLabel("COMPLETED")).toBe("Completed");
    expect(getStatusLabel("FAILED")).toBe("Failed");
  });
});

describe("isCompletedWithScores", () => {
  it("returns true when status is COMPLETED and scores exist", () => {
    expect(
      isCompletedWithScores({ status: "COMPLETED", scores: scores(80, 70) })
    ).toBe(true);
  });

  it("returns false when status is COMPLETED but scores are missing", () => {
    expect(isCompletedWithScores({ status: "COMPLETED", scores: undefined })).toBe(false);
  });

  it("returns false when status is not COMPLETED", () => {
    expect(
      isCompletedWithScores({ status: "RUNNING", scores: scores(80, 70) })
    ).toBe(false);
  });

  it("returns false when status is FAILED", () => {
    expect(isCompletedWithScores({ status: "FAILED", scores: scores(80, 70) })).toBe(false);
  });
});

describe("hasFailedWithError", () => {
  it("returns true when status is FAILED and error_message is present", () => {
    expect(
      hasFailedWithError({ status: "FAILED", error_message: "Timeout" })
    ).toBe(true);
  });

  it("returns false when status is FAILED but error_message is empty", () => {
    expect(
      hasFailedWithError({ status: "FAILED", error_message: "" })
    ).toBe(false);
  });

  it("returns false when status is FAILED but error_message is undefined", () => {
    expect(
      hasFailedWithError({ status: "FAILED", error_message: undefined })
    ).toBe(false);
  });

  it("returns false when status is not FAILED", () => {
    expect(
      hasFailedWithError({ status: "COMPLETED", error_message: "Timeout" })
    ).toBe(false);
  });
});

describe("countTranscriptSpeakers", () => {
  it("counts agent and debtor messages correctly", () => {
    const transcript: Evaluation["transcript"] = [
      { speaker: "agent", message: "Hello" },
      { speaker: "debtor", message: "Hi" },
      { speaker: "agent", message: "How are you?" },
      { speaker: "debtor", message: "Fine" },
    ];
    const result = countTranscriptSpeakers(transcript);
    expect(result.agent).toBe(2);
    expect(result.debtor).toBe(2);
    expect(result.total).toBe(4);
  });

  it("returns zeros when transcript is undefined", () => {
    const result = countTranscriptSpeakers(undefined);
    expect(result.agent).toBe(0);
    expect(result.debtor).toBe(0);
    expect(result.total).toBe(0);
  });

  it("returns zeros when transcript is empty", () => {
    const result = countTranscriptSpeakers([]);
    expect(result.total).toBe(0);
  });

  it("counts only agent messages", () => {
    const transcript: Evaluation["transcript"] = [
      { speaker: "agent", message: "A" },
      { speaker: "agent", message: "B" },
      { speaker: "agent", message: "C" },
    ];
    const result = countTranscriptSpeakers(transcript);
    expect(result.agent).toBe(3);
    expect(result.debtor).toBe(0);
    expect(result.total).toBe(3);
  });
});
