/**
 * Pure helper functions for evaluation scores and display logic.
 *
 * These functions were extracted from the evaluation detail page so they can
 * be unit tested in isolation without rendering any React components or
 * making API calls.
 */

import type { Evaluation, EvaluationScores } from "@/types/evaluation";

/**
 * Compute the average of task_completion and conversation_efficiency, rounded
 * to the nearest integer. Returns null when scores are not present.
 */
export function getAverageScore(scores?: EvaluationScores | null): number | null {
  if (!scores) {
    return null;
  }
  return Math.round(
    (scores.task_completion + scores.conversation_efficiency) / 2
  );
}

/**
 * Return a Tailwind text-color class based on a numeric score.
 *   >= 80 -> green
 *   >= 60 -> yellow
 *   <  60 -> red
 */
export function getScoreColor(score: number): string {
  if (score >= 80) return "text-green-400";
  if (score >= 60) return "text-yellow-400";
  return "text-red-400";
}

/**
 * Return a human-readable label for an evaluation status.
 */
export function getStatusLabel(status: Evaluation["status"]): string {
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
 * Type guard: returns true when an evaluation has completed with scores.
 */
export function isCompletedWithScores(
  evaluation: Pick<Evaluation, "status" | "scores">
): boolean {
  return evaluation.status === "COMPLETED" && evaluation.scores != null;
}

/**
 * Type guard: returns true when an evaluation has failed and carries an
 * error message.
 */
export function hasFailedWithError(
  evaluation: Pick<Evaluation, "status" | "error_message">
): boolean {
  return (
    evaluation.status === "FAILED" &&
    evaluation.error_message != null &&
    evaluation.error_message.length > 0
  );
}

/**
 * Count the number of messages from each speaker in a transcript.
 */
export function countTranscriptSpeakers(
  transcript: Evaluation["transcript"]
): { agent: number; debtor: number; total: number } {
  if (!transcript) {
    return { agent: 0, debtor: 0, total: 0 };
  }
  let agent = 0;
  let debtor = 0;
  for (const msg of transcript) {
    if (msg.speaker === "agent") {
      agent += 1;
    } else if (msg.speaker === "debtor") {
      debtor += 1;
    }
  }
  return { agent, debtor, total: agent + debtor };
}
