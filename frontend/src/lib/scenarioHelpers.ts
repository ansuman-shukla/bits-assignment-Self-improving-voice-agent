/**
 * Pure helper functions for scenario weight and validation logic.
 *
 * These mirror the backend Pydantic constraints so the frontend can validate
 * user input before sending it to the API.
 */

import type { Scenario, ScenarioUpdate } from "@/types/scenario";

/** Minimum and maximum allowed weight for a scenario. */
export const MIN_WEIGHT = 1;
export const MAX_WEIGHT = 5;

/** Minimum and maximum allowed backstory length. */
export const MIN_BACKSTORY_LENGTH = 10;
export const MAX_BACKSTORY_LENGTH = 2000;

/** Minimum and maximum allowed brief length. */
export const MIN_BRIEF_LENGTH = 1;
export const MAX_BRIEF_LENGTH = 500;

/**
 * Returns true when the given weight is within the allowed 1-5 range.
 */
export function isValidWeight(weight: number): boolean {
  return Number.isInteger(weight) && weight >= MIN_WEIGHT && weight <= MAX_WEIGHT;
}

/**
 * Returns true when the backstory meets the length constraints.
 */
export function isValidBackstory(backstory: string): boolean {
  return (
    backstory.length >= MIN_BACKSTORY_LENGTH &&
    backstory.length <= MAX_BACKSTORY_LENGTH
  );
}

/**
 * Returns true when the brief meets the length constraints.
 */
export function isValidBrief(brief: string): boolean {
  return (
    brief.length >= MIN_BRIEF_LENGTH && brief.length <= MAX_BRIEF_LENGTH
  );
}

/**
 * Validate a ScenarioUpdate payload and return an object of field -> error
 * messages. An empty object means the payload is valid.
 */
export function validateScenarioUpdate(
  update: ScenarioUpdate
): { backstory?: string; weight?: string } {
  const errors: { backstory?: string; weight?: string } = {};
  if (update.backstory !== undefined && !isValidBackstory(update.backstory)) {
    errors.backstory = `Backstory must be between ${MIN_BACKSTORY_LENGTH} and ${MAX_BACKSTORY_LENGTH} characters`;
  }
  if (update.weight !== undefined && !isValidWeight(update.weight)) {
    errors.weight = `Weight must be an integer between ${MIN_WEIGHT} and ${MAX_WEIGHT}`;
  }
  return errors;
}

/**
 * Render a weight value as a string of filled/empty star characters.
 * Useful for lightweight rendering and snapshot testing.
 */
export function weightToStars(weight: number): string {
  const filled = Math.max(0, Math.min(MAX_WEIGHT, Math.round(weight)));
  return "★".repeat(filled) + "☆".repeat(MAX_WEIGHT - filled);
}

/**
 * Sort scenarios by weight (descending). Returns a new array.
 */
export function sortByWeightDescending(scenarios: Scenario[]): Scenario[] {
  return [...scenarios].sort((a, b) => b.weight - a.weight);
}

/**
 * Filter scenarios to only those with a weight at or above the given threshold.
 */
export function filterByMinWeight(
  scenarios: Scenario[],
  minWeight: number
): Scenario[] {
  return scenarios.filter((s) => s.weight >= minWeight);
}
