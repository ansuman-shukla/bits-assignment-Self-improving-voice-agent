/**
 * Pure helper functions for call records and transcripts.
 *
 * Extracted from call-related components so they can be unit tested without
 * rendering React components or making API calls.
 */

import type { CallRecord, TranscriptResponse, TranscriptMessage } from "@/types/call";

/**
 * Return a human-readable label for a call status.
 */
export function getCallStatusLabel(status: CallRecord["status"]): string {
  switch (status) {
    case "in_progress":
      return "In Progress";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    default:
      return "Unknown";
  }
}

/**
 * Return a Tailwind text-color class for a call status.
 */
export function getCallStatusColor(status: CallRecord["status"]): string {
  switch (status) {
    case "in_progress":
      return "text-blue-400";
    case "completed":
      return "text-green-400";
    case "failed":
      return "text-red-400";
    default:
      return "text-gray-400";
  }
}

/**
 * Type guard: returns true when a call record has a transcript file available.
 */
export function hasTranscript(call: Pick<CallRecord, "transcript_file">): boolean {
  return call.transcript_file != null && call.transcript_file.length > 0;
}

/**
 * Type guard: returns true when a call is completed.
 */
export function isCallCompleted(call: Pick<CallRecord, "status">): boolean {
  return call.status === "completed";
}

/**
 * Type guard: returns true when a call is still in progress.
 */
export function isCallInProgress(call: Pick<CallRecord, "status">): boolean {
  return call.status === "in_progress";
}

/**
 * Format a phone number with country code into a single display string.
 */
export function formatPhoneNumber(
  countryCode: string,
  phoneNumber: string
): string {
  return `${countryCode}${phoneNumber}`;
}

/**
 * Format an amount as an Indian Rupee string.
 */
export function formatRupeeAmount(amount: number): string {
  return `₹${amount.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Count the number of messages from each role in a transcript.
 */
export function countTranscriptRoles(
  transcript: TranscriptMessage[]
): { agent: number; user: number; total: number } {
  let agent = 0;
  let user = 0;
  for (const msg of transcript) {
    if (msg.role === "agent") {
      agent += 1;
    } else if (msg.role === "user") {
      user += 1;
    }
  }
  return { agent, user, total: agent + user };
}

/**
 * Compute the average of all available risk scores on a transcript response.
 * Returns null when no scores are present.
 */
export function getAverageRiskScore(
  transcript: Pick<
    TranscriptResponse,
    | "loan_recovery_score"
    | "willingness_to_pay_score"
    | "escalation_risk_score"
    | "customer_sentiment_score"
    | "promise_to_pay_reliability_index"
  >
): number | null {
  const scores: number[] = [];
  if (transcript.loan_recovery_score != null)
    scores.push(transcript.loan_recovery_score);
  if (transcript.willingness_to_pay_score != null)
    scores.push(transcript.willingness_to_pay_score);
  if (transcript.escalation_risk_score != null)
    scores.push(transcript.escalation_risk_score);
  if (transcript.customer_sentiment_score != null)
    scores.push(transcript.customer_sentiment_score);
  if (transcript.promise_to_pay_reliability_index != null)
    scores.push(transcript.promise_to_pay_reliability_index);

  if (scores.length === 0) {
    return null;
  }
  const sum = scores.reduce((acc, s) => acc + s, 0);
  return Math.round((sum / scores.length) * 100) / 100;
}
