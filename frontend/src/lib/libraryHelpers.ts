/**
 * Pure helper functions for library entities (personalities and prompts).
 *
 * Mirrors backend Pydantic constraints so the frontend can validate user
 * input before sending it to the API.
 */

import type {
  PersonalityCreate,
  PersonalityUpdate,
  PromptCreate,
  PromptUpdate,
} from "@/types/library";

/** Name length bounds (shared by personalities and prompts). */
export const MIN_NAME_LENGTH = 1;
export const MAX_NAME_LENGTH = 100;

/** Description length bounds. */
export const MIN_DESCRIPTION_LENGTH = 1;
export const MAX_DESCRIPTION_LENGTH = 500;

/** System prompt minimum length. */
export const MIN_SYSTEM_PROMPT_LENGTH = 10;

/** Prompt text minimum length. */
export const MIN_PROMPT_TEXT_LENGTH = 10;

/** Version length bounds. */
export const MIN_VERSION_LENGTH = 1;
export const MAX_VERSION_LENGTH = 50;

/**
 * Returns true when the name is within the allowed length range.
 */
export function isValidName(name: string): boolean {
  return (
    name.length >= MIN_NAME_LENGTH && name.length <= MAX_NAME_LENGTH
  );
}

/**
 * Returns true when the description is within the allowed length range.
 */
export function isValidDescription(description: string): boolean {
  return (
    description.length >= MIN_DESCRIPTION_LENGTH &&
    description.length <= MAX_DESCRIPTION_LENGTH
  );
}

/**
 * Returns true when the system prompt meets the minimum length.
 */
export function isValidSystemPrompt(prompt: string): boolean {
  return prompt.length >= MIN_SYSTEM_PROMPT_LENGTH;
}

/**
 * Returns true when the prompt text meets the minimum length.
 */
export function isValidPromptText(text: string): boolean {
  return text.length >= MIN_PROMPT_TEXT_LENGTH;
}

/**
 * Returns true when the version string is within the allowed length range.
 */
export function isValidVersion(version: string): boolean {
  return (
    version.length >= MIN_VERSION_LENGTH && version.length <= MAX_VERSION_LENGTH
  );
}

/**
 * Returns true when the amount is a positive number (or undefined).
 */
export function isValidAmount(amount?: number): boolean {
  if (amount === undefined || amount === null) {
    return true;
  }
  return typeof amount === "number" && amount > 0;
}

/**
 * Validate a PersonalityCreate payload and return field -> error messages.
 * An empty object means the payload is valid.
 */
export function validatePersonalityCreate(
  data: PersonalityCreate
): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!isValidName(data.name)) {
    errors.name = `Name must be between ${MIN_NAME_LENGTH} and ${MAX_NAME_LENGTH} characters`;
  }
  if (!isValidDescription(data.description)) {
    errors.description = `Description must be between ${MIN_DESCRIPTION_LENGTH} and ${MAX_DESCRIPTION_LENGTH} characters`;
  }
  if (!isValidSystemPrompt(data.system_prompt)) {
    errors.system_prompt = `System prompt must be at least ${MIN_SYSTEM_PROMPT_LENGTH} characters`;
  }
  if (!isValidAmount(data.amount)) {
    errors.amount = "Amount must be a positive number";
  }
  return errors;
}

/**
 * Validate a PersonalityUpdate payload (all fields optional).
 */
export function validatePersonalityUpdate(
  data: PersonalityUpdate
): Record<string, string> {
  const errors: Record<string, string> = {};
  if (data.name !== undefined && !isValidName(data.name)) {
    errors.name = `Name must be between ${MIN_NAME_LENGTH} and ${MAX_NAME_LENGTH} characters`;
  }
  if (data.description !== undefined && !isValidDescription(data.description)) {
    errors.description = `Description must be between ${MIN_DESCRIPTION_LENGTH} and ${MAX_DESCRIPTION_LENGTH} characters`;
  }
  if (data.system_prompt !== undefined && !isValidSystemPrompt(data.system_prompt)) {
    errors.system_prompt = `System prompt must be at least ${MIN_SYSTEM_PROMPT_LENGTH} characters`;
  }
  if (data.amount !== undefined && !isValidAmount(data.amount)) {
    errors.amount = "Amount must be a positive number";
  }
  return errors;
}

/**
 * Validate a PromptCreate payload.
 */
export function validatePromptCreate(
  data: PromptCreate
): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!isValidName(data.name)) {
    errors.name = `Name must be between ${MIN_NAME_LENGTH} and ${MAX_NAME_LENGTH} characters`;
  }
  if (!isValidPromptText(data.prompt_text)) {
    errors.prompt_text = `Prompt text must be at least ${MIN_PROMPT_TEXT_LENGTH} characters`;
  }
  if (!isValidVersion(data.version)) {
    errors.version = `Version must be between ${MIN_VERSION_LENGTH} and ${MAX_VERSION_LENGTH} characters`;
  }
  return errors;
}

/**
 * Validate a PromptUpdate payload (all fields optional).
 */
export function validatePromptUpdate(
  data: PromptUpdate
): Record<string, string> {
  const errors: Record<string, string> = {};
  if (data.name !== undefined && !isValidName(data.name)) {
    errors.name = `Name must be between ${MIN_NAME_LENGTH} and ${MAX_NAME_LENGTH} characters`;
  }
  if (data.prompt_text !== undefined && !isValidPromptText(data.prompt_text)) {
    errors.prompt_text = `Prompt text must be at least ${MIN_PROMPT_TEXT_LENGTH} characters`;
  }
  if (data.version !== undefined && !isValidVersion(data.version)) {
    errors.version = `Version must be between ${MIN_VERSION_LENGTH} and ${MAX_VERSION_LENGTH} characters`;
  }
  return errors;
}
