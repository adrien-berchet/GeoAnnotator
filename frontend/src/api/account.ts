/**
 * Account management API calls.
 */

import { apiClient } from "./client";

/**
 * Account information response.
 */
export interface AccountInfo {
  id: number;
  pseudonym: string;
  email: string;
  created_at: string;
  updated_at: string;
}

/**
 * Pseudonym update request.
 */
export interface PseudonymUpdateData {
  pseudonym: string;
}

/**
 * Email change request.
 */
export interface EmailChangeData {
  new_email: string;
}

/**
 * Email change response.
 */
export interface EmailChangeResponse {
  detail: string;
  expires_at: string;
}

/**
 * Email confirmation request.
 */
export interface EmailConfirmData {
  token: string;
  user_id: string; // UUID
}

/**
 * Email confirmation response.
 */
export interface EmailConfirmResponse {
  detail: string;
  new_email: string;
}

/**
 * Password change request.
 */
export interface PasswordChangeData {
  old_password: string;
  new_password: string;
}

/**
 * Password change response.
 */
export interface PasswordChangeResponse {
  detail: string;
}

/**
 * Account deletion response.
 */
export interface AccountDeleteResponse {
  detail: string;
  warning: string;
}

/**
 * Account deletion confirmation request.
 */
export interface AccountDeleteConfirmData {
  token: string;
  user_id: string; // UUID
}

/**
 * Account deletion confirmation response.
 */
export interface AccountDeleteConfirmResponse {
  detail: string;
  deleted_at: string;
  permanent_deletion_date: string;
}

/**
 * Pseudonym validation request.
 */
export interface PseudonymValidationData {
  pseudonym: string;
}

/**
 * Pseudonym validation response.
 */
export interface PseudonymValidationResponse {
  valid: boolean;
  available: boolean | null;
  error?: string;
}

/**
 * Get current user's account information.
 */
export async function getAccount(): Promise<AccountInfo> {
  const response = await apiClient.get<AccountInfo>("/account/");
  return response.data;
}

/**
 * Update account pseudonym.
 */
export async function updatePseudonym(
  data: PseudonymUpdateData,
): Promise<AccountInfo> {
  const response = await apiClient.patch<AccountInfo>("/account/", data);
  return response.data;
}

/**
 * Initiate email change process (sends confirmation email).
 */
export async function changeEmail(
  data: EmailChangeData,
): Promise<EmailChangeResponse> {
  const response = await apiClient.post<EmailChangeResponse>(
    "/account/change-email/",
    data,
  );
  return response.data;
}

/**
 * Confirm email change with token from email link.
 */
export async function confirmEmail(
  data: EmailConfirmData,
): Promise<EmailConfirmResponse> {
  const response = await apiClient.post<EmailConfirmResponse>(
    "/account/confirm-email/",
    data,
  );
  return response.data;
}

/**
 * Change user password.
 */
export async function changePassword(
  data: PasswordChangeData,
): Promise<PasswordChangeResponse> {
  const response = await apiClient.post<PasswordChangeResponse>(
    "/account/change-password/",
    data,
  );
  return response.data;
}

/**
 * Soft delete user account (sends confirmation email).
 */
export async function deleteAccount(): Promise<AccountDeleteResponse> {
  const response = await apiClient.delete<AccountDeleteResponse>("/account/");
  return response.data;
}

/**
 * Confirm account deletion with token from email link.
 */
export async function confirmDeleteAccount(
  data: AccountDeleteConfirmData,
): Promise<AccountDeleteConfirmResponse> {
  const response = await apiClient.post<AccountDeleteConfirmResponse>(
    "/account/confirm-delete/",
    data,
  );
  return response.data;
}

/**
 * Validate pseudonym without saving (for frontend inline validation).
 */
export async function validatePseudonym(
  data: PseudonymValidationData,
): Promise<PseudonymValidationResponse> {
  const response = await apiClient.post<PseudonymValidationResponse>(
    "/account/validate-pseudonym/",
    data,
  );
  return response.data;
}
