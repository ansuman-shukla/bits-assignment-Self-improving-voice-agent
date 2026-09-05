/**
 * Unit tests for scenario helper functions.
 *
 * Tests weight validation, backstory/brief length validation, star rendering,
 * and sorting/filtering logic. No API or database calls.
 */

import { describe, it, expect } from "vitest";
import {
  MIN_WEIGHT,
  MAX_WEIGHT,
  MIN_BACKSTORY_LENGTH,
  MAX_BACKSTORY_LENGTH,
  MIN_BRIEF_LENGTH,
  MAX_BRIEF_LENGTH,
  isValidWeight,
  isValidBackstory,
  isValidBrief,
  validateScenarioUpdate,
  weightToStars,
  sortByWeightDescending,
  filterByMinWeight,
} from "@/lib/scenarioHelpers";
import type { Scenario } from "@/types/scenario";

const scenario = (id: string, weight: number): Scenario => ({
  _id: id,
  personality_id: "pers-1",
  title: `Scenario ${id}`,
  brief: "A brief",
  backstory: "A backstory",
  objective: "An objective",
  weight,
  created_at: "2025-10-04T10:00:00Z",
});

describe("constants", () => {
  it("has weight bounds 1 and 5", () => {
    expect(MIN_WEIGHT).toBe(1);
    expect(MAX_WEIGHT).toBe(5);
  });

  it("has backstory length bounds", () => {
    expect(MIN_BACKSTORY_LENGTH).toBe(10);
    expect(MAX_BACKSTORY_LENGTH).toBe(2000);
  });

  it("has brief length bounds", () => {
    expect(MIN_BRIEF_LENGTH).toBe(1);
    expect(MAX_BRIEF_LENGTH).toBe(500);
  });
});

describe("isValidWeight", () => {
  it("accepts weights 1 through 5", () => {
    for (let w = 1; w <= 5; w++) {
      expect(isValidWeight(w)).toBe(true);
    }
  });

  it("rejects 0", () => {
    expect(isValidWeight(0)).toBe(false);
  });

  it("rejects 6", () => {
    expect(isValidWeight(6)).toBe(false);
  });

  it("rejects non-integers", () => {
    expect(isValidWeight(3.5)).toBe(false);
    expect(isValidWeight(2.9)).toBe(false);
  });

  it("rejects negative numbers", () => {
    expect(isValidWeight(-1)).toBe(false);
  });
});

describe("isValidBackstory", () => {
  it("accepts a backstory within bounds", () => {
    expect(isValidBackstory("A valid backstory.")).toBe(true);
  });

  it("accepts exactly the minimum length", () => {
    expect(isValidBackstory("0123456789")).toBe(true);
  });

  it("rejects below the minimum length", () => {
    expect(isValidBackstory("short")).toBe(false);
  });

  it("accepts exactly the maximum length", () => {
    expect(isValidBackstory("x".repeat(MAX_BACKSTORY_LENGTH))).toBe(true);
  });

  it("rejects above the maximum length", () => {
    expect(isValidBackstory("x".repeat(MAX_BACKSTORY_LENGTH + 1))).toBe(false);
  });
});

describe("isValidBrief", () => {
  it("accepts a brief within bounds", () => {
    expect(isValidBrief("A brief description")).toBe(true);
  });

  it("accepts exactly 1 character", () => {
    expect(isValidBrief("x")).toBe(true);
  });

  it("rejects an empty brief", () => {
    expect(isValidBrief("")).toBe(false);
  });

  it("accepts exactly the maximum length", () => {
    expect(isValidBrief("x".repeat(MAX_BRIEF_LENGTH))).toBe(true);
  });

  it("rejects above the maximum length", () => {
    expect(isValidBrief("x".repeat(MAX_BRIEF_LENGTH + 1))).toBe(false);
  });
});

describe("validateScenarioUpdate", () => {
  it("returns no errors for a valid update", () => {
    const errors = validateScenarioUpdate({
      backstory: "A sufficiently long backstory.",
      weight: 3,
    });
    expect(errors).toEqual({});
  });

  it("returns no errors for an empty update", () => {
    expect(validateScenarioUpdate({})).toEqual({});
  });

  it("reports a backstory error when too short", () => {
    const errors = validateScenarioUpdate({ backstory: "short" });
    expect(errors.backstory).toBeDefined();
    expect(errors.weight).toBeUndefined();
  });

  it("reports a weight error when out of range", () => {
    const errors = validateScenarioUpdate({ weight: 0 });
    expect(errors.weight).toBeDefined();
    expect(errors.backstory).toBeUndefined();
  });

  it("reports both errors when both fields are invalid", () => {
    const errors = validateScenarioUpdate({ backstory: "short", weight: 99 });
    expect(errors.backstory).toBeDefined();
    expect(errors.weight).toBeDefined();
  });
});

describe("weightToStars", () => {
  it("renders 5 filled stars for weight 5", () => {
    expect(weightToStars(5)).toBe("★★★★★");
  });

  it("renders 3 filled and 2 empty stars for weight 3", () => {
    expect(weightToStars(3)).toBe("★★★☆☆");
  });

  it("renders all empty stars for weight 0", () => {
    expect(weightToStars(0)).toBe("☆☆☆☆☆");
  });

  it("clamps values above 5 to 5", () => {
    expect(weightToStars(10)).toBe("★★★★★");
  });

  it("clamps negative values to 0", () => {
    expect(weightToStars(-3)).toBe("☆☆☆☆☆");
  });

  it("rounds non-integer weights", () => {
    expect(weightToStars(2.4)).toBe("★★☆☆☆");
    expect(weightToStars(2.6)).toBe("★★★☆☆");
  });

  it("always returns exactly 5 characters", () => {
    for (let w = -2; w <= 8; w++) {
      expect(weightToStars(w).length).toBe(5);
    }
  });
});

describe("sortByWeightDescending", () => {
  it("sorts scenarios by weight descending", () => {
    const scenarios = [
      scenario("a", 2),
      scenario("b", 5),
      scenario("c", 3),
      scenario("d", 1),
    ];
    const sorted = sortByWeightDescending(scenarios);
    expect(sorted.map((s) => s.weight)).toEqual([5, 3, 2, 1]);
  });

  it("does not mutate the original array", () => {
    const scenarios = [scenario("a", 1), scenario("b", 5)];
    const original = [...scenarios];
    sortByWeightDescending(scenarios);
    expect(scenarios.map((s) => s.weight)).toEqual(original.map((s) => s.weight));
  });

  it("handles an empty array", () => {
    expect(sortByWeightDescending([])).toEqual([]);
  });
});

describe("filterByMinWeight", () => {
  it("filters scenarios below the threshold", () => {
    const scenarios = [
      scenario("a", 1),
      scenario("b", 3),
      scenario("c", 5),
      scenario("d", 2),
    ];
    const filtered = filterByMinWeight(scenarios, 3);
    expect(filtered.map((s) => s._id)).toEqual(["b", "c"]);
  });

  it("returns all scenarios when threshold is 1", () => {
    const scenarios = [scenario("a", 1), scenario("b", 5)];
    expect(filterByMinWeight(scenarios, 1).length).toBe(2);
  });

  it("returns no scenarios when threshold is above max", () => {
    const scenarios = [scenario("a", 1), scenario("b", 5)];
    expect(filterByMinWeight(scenarios, 6)).toEqual([]);
  });

  it("handles an empty array", () => {
    expect(filterByMinWeight([], 3)).toEqual([]);
  });
});
