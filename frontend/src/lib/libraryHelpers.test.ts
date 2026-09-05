/**
 * Unit tests for library helper functions (personalities and prompts).
 *
 * Tests validation logic that mirrors the backend Pydantic constraints.
 * No API or database calls are made.
 */

import { describe, it, expect } from "vitest";
import {
  MIN_NAME_LENGTH,
  MAX_NAME_LENGTH,
  MIN_DESCRIPTION_LENGTH,
  MAX_DESCRIPTION_LENGTH,
  MIN_SYSTEM_PROMPT_LENGTH,
  MIN_PROMPT_TEXT_LENGTH,
  MIN_VERSION_LENGTH,
  MAX_VERSION_LENGTH,
  isValidName,
  isValidDescription,
  isValidSystemPrompt,
  isValidPromptText,
  isValidVersion,
  isValidAmount,
  validatePersonalityCreate,
  validatePersonalityUpdate,
  validatePromptCreate,
  validatePromptUpdate,
} from "@/lib/libraryHelpers";

describe("constants", () => {
  it("has correct name length bounds", () => {
    expect(MIN_NAME_LENGTH).toBe(1);
    expect(MAX_NAME_LENGTH).toBe(100);
  });

  it("has correct description length bounds", () => {
    expect(MIN_DESCRIPTION_LENGTH).toBe(1);
    expect(MAX_DESCRIPTION_LENGTH).toBe(500);
  });

  it("has correct system prompt minimum length", () => {
    expect(MIN_SYSTEM_PROMPT_LENGTH).toBe(10);
  });

  it("has correct prompt text minimum length", () => {
    expect(MIN_PROMPT_TEXT_LENGTH).toBe(10);
  });

  it("has correct version length bounds", () => {
    expect(MIN_VERSION_LENGTH).toBe(1);
    expect(MAX_VERSION_LENGTH).toBe(50);
  });
});

describe("isValidName", () => {
  it("accepts a normal name", () => {
    expect(isValidName("Willful Defaulter")).toBe(true);
  });

  it("accepts a single character", () => {
    expect(isValidName("X")).toBe(true);
  });

  it("rejects an empty string", () => {
    expect(isValidName("")).toBe(false);
  });

  it("accepts exactly the maximum length", () => {
    expect(isValidName("x".repeat(MAX_NAME_LENGTH))).toBe(true);
  });

  it("rejects above the maximum length", () => {
    expect(isValidName("x".repeat(MAX_NAME_LENGTH + 1))).toBe(false);
  });
});

describe("isValidDescription", () => {
  it("accepts a normal description", () => {
    expect(isValidDescription("A person who avoids payment")).toBe(true);
  });

  it("rejects an empty string", () => {
    expect(isValidDescription("")).toBe(false);
  });

  it("accepts exactly the maximum length", () => {
    expect(isValidDescription("x".repeat(MAX_DESCRIPTION_LENGTH))).toBe(true);
  });

  it("rejects above the maximum length", () => {
    expect(isValidDescription("x".repeat(MAX_DESCRIPTION_LENGTH + 1))).toBe(false);
  });
});

describe("isValidSystemPrompt", () => {
  it("accepts a sufficiently long prompt", () => {
    expect(isValidSystemPrompt("You are a debtor who avoids payment.")).toBe(true);
  });

  it("accepts exactly the minimum length", () => {
    expect(isValidSystemPrompt("0123456789")).toBe(true);
  });

  it("rejects below the minimum length", () => {
    expect(isValidSystemPrompt("short")).toBe(false);
  });
});

describe("isValidPromptText", () => {
  it("accepts a sufficiently long prompt text", () => {
    expect(isValidPromptText("You are a debt collection agent.")).toBe(true);
  });

  it("accepts exactly the minimum length", () => {
    expect(isValidPromptText("0123456789")).toBe(true);
  });

  it("rejects below the minimum length", () => {
    expect(isValidPromptText("short")).toBe(false);
  });
});

describe("isValidVersion", () => {
  it("accepts a normal version", () => {
    expect(isValidVersion("1.1")).toBe(true);
  });

  it("accepts a single character", () => {
    expect(isValidVersion("v")).toBe(true);
  });

  it("rejects an empty string", () => {
    expect(isValidVersion("")).toBe(false);
  });

  it("accepts exactly the maximum length", () => {
    expect(isValidVersion("x".repeat(MAX_VERSION_LENGTH))).toBe(true);
  });

  it("rejects above the maximum length", () => {
    expect(isValidVersion("x".repeat(MAX_VERSION_LENGTH + 1))).toBe(false);
  });
});

describe("isValidAmount", () => {
  it("accepts a positive number", () => {
    expect(isValidAmount(5000)).toBe(true);
    expect(isValidAmount(0.01)).toBe(true);
  });

  it("accepts undefined", () => {
    expect(isValidAmount(undefined)).toBe(true);
  });

  it("accepts null", () => {
    expect(isValidAmount(null)).toBe(true);
  });

  it("rejects zero", () => {
    expect(isValidAmount(0)).toBe(false);
  });

  it("rejects negative numbers", () => {
    expect(isValidAmount(-100)).toBe(false);
  });
});

describe("validatePersonalityCreate", () => {
  const valid = {
    name: "Test Personality",
    description: "A test description",
    core_traits: { Attitude: "Calm" },
    system_prompt: "You are a test personality.",
  };

  it("returns no errors for a valid payload", () => {
    expect(validatePersonalityCreate(valid)).toEqual({});
  });

  it("returns no errors for a valid payload with amount", () => {
    expect(validatePersonalityCreate({ ...valid, amount: 5000 })).toEqual({});
  });

  it("reports a name error for an empty name", () => {
    const errors = validatePersonalityCreate({ ...valid, name: "" });
    expect(errors.name).toBeDefined();
  });

  it("reports a description error for an empty description", () => {
    const errors = validatePersonalityCreate({ ...valid, description: "" });
    expect(errors.description).toBeDefined();
  });

  it("reports a system_prompt error for a short prompt", () => {
    const errors = validatePersonalityCreate({ ...valid, system_prompt: "short" });
    expect(errors.system_prompt).toBeDefined();
  });

  it("reports an amount error for a non-positive amount", () => {
    const errors = validatePersonalityCreate({ ...valid, amount: -10 });
    expect(errors.amount).toBeDefined();
  });

  it("reports multiple errors at once", () => {
    const errors = validatePersonalityCreate({
      name: "",
      description: "",
      core_traits: {},
      system_prompt: "short",
      amount: -1,
    });
    expect(Object.keys(errors).length).toBe(4);
  });
});

describe("validatePersonalityUpdate", () => {
  it("returns no errors for an empty update", () => {
    expect(validatePersonalityUpdate({})).toEqual({});
  });

  it("returns no errors for a valid partial update", () => {
    expect(validatePersonalityUpdate({ name: "New Name" })).toEqual({});
  });

  it("reports an error for an invalid name", () => {
    const errors = validatePersonalityUpdate({ name: "" });
    expect(errors.name).toBeDefined();
  });

  it("reports an error for an invalid amount", () => {
    const errors = validatePersonalityUpdate({ amount: 0 });
    expect(errors.amount).toBeDefined();
  });
});

describe("validatePromptCreate", () => {
  const valid = {
    name: "v1.0-test",
    prompt_text: "You are a debt collection agent.",
    version: "1.0",
  };

  it("returns no errors for a valid payload", () => {
    expect(validatePromptCreate(valid)).toEqual({});
  });

  it("reports a name error for an empty name", () => {
    const errors = validatePromptCreate({ ...valid, name: "" });
    expect(errors.name).toBeDefined();
  });

  it("reports a prompt_text error for short text", () => {
    const errors = validatePromptCreate({ ...valid, prompt_text: "short" });
    expect(errors.prompt_text).toBeDefined();
  });

  it("reports a version error for an empty version", () => {
    const errors = validatePromptCreate({ ...valid, version: "" });
    expect(errors.version).toBeDefined();
  });
});

describe("validatePromptUpdate", () => {
  it("returns no errors for an empty update", () => {
    expect(validatePromptUpdate({})).toEqual({});
  });

  it("returns no errors for a valid partial update", () => {
    expect(validatePromptUpdate({ version: "2.0" })).toEqual({});
  });

  it("reports an error for an invalid name", () => {
    const errors = validatePromptUpdate({ name: "" });
    expect(errors.name).toBeDefined();
  });

  it("reports an error for short prompt text", () => {
    const errors = validatePromptUpdate({ prompt_text: "short" });
    expect(errors.prompt_text).toBeDefined();
  });

  it("reports an error for an invalid version", () => {
    const errors = validatePromptUpdate({ version: "" });
    expect(errors.version).toBeDefined();
  });
});
