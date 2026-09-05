/**
 * Unit tests for tuning helper functions.
 *
 * Tests pure functions for status colors, score improvement, target
 * detection, and best-iteration selection. No API or database calls.
 */

import { describe, it, expect } from "vitest";
import {
  getTuningStatusColor,
  getTuningStatusLabel,
  getScoreImprovement,
  hasReachedTarget,
  getBestIteration,
  getTotalScenarioWeight,
  isTuningInProgress,
} from "@/lib/tuningHelpers";
import type { TuningLoop, TuningIteration } from "@/types/tuning";

const iteration = (n: number, score: number): TuningIteration => ({
  iteration_number: n,
  prompt_id: `prompt-${n}`,
  evaluation_ids: [`eval-${n}`],
  weighted_score: score,
  timestamp: "2025-10-04T10:00:00Z",
});

const loop = (
  iterations: TuningIteration[],
  target: number,
  status: TuningLoop["status"] = "RUNNING"
): TuningLoop => ({
  _id: "tuning-1",
  status,
  config: {
    target_score: target,
    max_iterations: 5,
    scenario_weights: [
      { scenario_id: "s1", weight: 3 },
      { scenario_id: "s2", weight: 2 },
    ],
  },
  iterations,
  created_at: "2025-10-04T10:00:00Z",
});

describe("getTuningStatusColor", () => {
  it("returns yellow for PENDING", () => {
    expect(getTuningStatusColor("PENDING")).toBe("text-yellow-400");
  });

  it("returns blue for RUNNING", () => {
    expect(getTuningStatusColor("RUNNING")).toBe("text-blue-400");
  });

  it("returns green for COMPLETED", () => {
    expect(getTuningStatusColor("COMPLETED")).toBe("text-green-400");
  });

  it("returns red for FAILED", () => {
    expect(getTuningStatusColor("FAILED")).toBe("text-red-400");
  });
});

describe("getTuningStatusLabel", () => {
  it("returns the correct label for each status", () => {
    expect(getTuningStatusLabel("PENDING")).toBe("Pending");
    expect(getTuningStatusLabel("RUNNING")).toBe("Running");
    expect(getTuningStatusLabel("COMPLETED")).toBe("Completed");
    expect(getTuningStatusLabel("FAILED")).toBe("Failed");
  });
});

describe("getScoreImprovement", () => {
  it("returns the difference between latest and first score", () => {
    const l = loop([iteration(1, 60), iteration(2, 75), iteration(3, 85)], 90);
    expect(getScoreImprovement(l)).toBe(25);
  });

  it("returns a negative value when score decreased", () => {
    const l = loop([iteration(1, 80), iteration(2, 70)], 90);
    expect(getScoreImprovement(l)).toBe(-10);
  });

  it("returns 0 when score did not change", () => {
    const l = loop([iteration(1, 75), iteration(2, 75)], 90);
    expect(getScoreImprovement(l)).toBe(0);
  });

  it("returns null when there are fewer than 2 iterations", () => {
    expect(getScoreImprovement({ iterations: [] })).toBeNull();
    expect(getScoreImprovement({ iterations: [iteration(1, 50)] })).toBeNull();
  });
});

describe("hasReachedTarget", () => {
  it("returns true when the latest score meets or exceeds the target", () => {
    const l = loop([iteration(1, 60), iteration(2, 90)], 85);
    expect(hasReachedTarget(l)).toBe(true);
  });

  it("returns true when the latest score equals the target exactly", () => {
    const l = loop([iteration(1, 85)], 85);
    expect(hasReachedTarget(l)).toBe(true);
  });

  it("returns false when the latest score is below the target", () => {
    const l = loop([iteration(1, 60), iteration(2, 80)], 85);
    expect(hasReachedTarget(l)).toBe(false);
  });

  it("returns false when there are no iterations", () => {
    const l = loop([], 85);
    expect(hasReachedTarget(l)).toBe(false);
  });
});

describe("getBestIteration", () => {
  it("returns the iteration with the highest score", () => {
    const l = loop([iteration(1, 60), iteration(2, 90), iteration(3, 75)], 95);
    const best = getBestIteration(l);
    expect(best).toEqual({ iterationNumber: 2, score: 90 });
  });

  it("returns the first iteration when all scores are equal", () => {
    const l = loop([iteration(1, 70), iteration(2, 70)], 90);
    const best = getBestIteration(l);
    expect(best).toEqual({ iterationNumber: 1, score: 70 });
  });

  it("returns null when there are no iterations", () => {
    expect(getBestIteration({ iterations: [] })).toBeNull();
  });

  it("handles a single iteration", () => {
    const l = loop([iteration(1, 50)], 90);
    expect(getBestIteration(l)).toEqual({ iterationNumber: 1, score: 50 });
  });
});

describe("getTotalScenarioWeight", () => {
  it("sums all scenario weights", () => {
    const l = loop([], 90);
    expect(getTotalScenarioWeight(l)).toBe(5); // 3 + 2
  });

  it("returns 0 when there are no scenario weights", () => {
    const l: Pick<TuningLoop, "config"> = {
      config: { target_score: 90, max_iterations: 5, scenario_weights: [] },
    };
    expect(getTotalScenarioWeight(l)).toBe(0);
  });
});

describe("isTuningInProgress", () => {
  it("returns true for PENDING", () => {
    expect(isTuningInProgress("PENDING")).toBe(true);
  });

  it("returns true for RUNNING", () => {
    expect(isTuningInProgress("RUNNING")).toBe(true);
  });

  it("returns false for COMPLETED", () => {
    expect(isTuningInProgress("COMPLETED")).toBe(false);
  });

  it("returns false for FAILED", () => {
    expect(isTuningInProgress("FAILED")).toBe(false);
  });
});
