/**
 * Pure helper functions for tuning loop display logic.
 *
 * Extracted from the tuning detail page so they can be unit tested without
 * rendering React components or making API calls.
 */

import type { TuningLoop, TuningStatus } from "@/types/tuning";

/**
 * Return a Tailwind text-color class for a tuning status.
 */
export function getTuningStatusColor(status: TuningStatus): string {
  switch (status) {
    case "PENDING":
      return "text-yellow-400";
    case "RUNNING":
      return "text-blue-400";
    case "COMPLETED":
      return "text-green-400";
    case "FAILED":
      return "text-red-400";
    default:
      return "text-gray-400";
  }
}

/**
 * Return a human-readable label for a tuning status.
 */
export function getTuningStatusLabel(status: TuningStatus): string {
  switch (status) {
    case "PENDING":
      return "Pending";
    case "RUNNING":
      return "Running";
    case "COMPLETED":
      return "Completed";
    case "FAILED":
      return "Failed";
    default:
      return "Unknown";
  }
}

/**
 * Compute the score improvement between the first and latest iteration.
 * Returns null when there are fewer than 2 iterations.
 */
export function getScoreImprovement(
  loop: Pick<TuningLoop, "iterations">
): number | null {
  if (!loop || loop.iterations.length < 2) {
    return null;
  }
  const firstScore = loop.iterations[0].weighted_score;
  const latestScore = loop.iterations[loop.iterations.length - 1].weighted_score;
  return latestScore - firstScore;
}

/**
 * Determine whether a tuning loop has reached its target score.
 */
export function hasReachedTarget(
  loop: Pick<TuningLoop, "iterations" | "config">
): boolean {
  if (loop.iterations.length === 0) {
    return false;
  }
  const latest = loop.iterations[loop.iterations.length - 1].weighted_score;
  return latest >= loop.config.target_score;
}

/**
 * Find the best (highest scoring) iteration in a tuning loop.
 * Returns null when there are no iterations.
 */
export function getBestIteration(
  loop: Pick<TuningLoop, "iterations">
): { iterationNumber: number; score: number } | null {
  if (loop.iterations.length === 0) {
    return null;
  }
  let best = loop.iterations[0];
  for (const it of loop.iterations) {
    if (it.weighted_score > best.weighted_score) {
      best = it;
    }
  }
  return { iterationNumber: best.iteration_number, score: best.weighted_score };
}

/**
 * Compute the total weight across all scenario weights in a tuning config.
 */
export function getTotalScenarioWeight(
  loop: Pick<TuningLoop, "config">
): number {
  return loop.config.scenario_weights.reduce((sum, sw) => sum + sw.weight, 0);
}

/**
 * Determine whether the tuning loop is still in progress (PENDING or RUNNING).
 */
export function isTuningInProgress(status: TuningStatus): boolean {
  return status === "PENDING" || status === "RUNNING";
}
