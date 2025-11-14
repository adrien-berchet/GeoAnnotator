/**
 * Account management API calls.
 */

import { apiClient } from "./client";

/**
 * Account information response.
 */
export interface AccountInfo {
  id: number;
  username: string;
  email: string;
  date_joined: string;
}

/**
 * Username update request.
 */
export interface UsernameUpdateData {
  username: string;
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
 * Username validation request.
 */
export interface UsernameValidationData {
  username: string;
}

/**
 * Username validation response.
 */
export interface UsernameValidationResponse {
  valid: boolean;
  available: boolean | null;
  error?: string;
}

/**
 * Get current user's account information.
 */
export async function getAccount(): Promise<AccountInfo> {
  const response = await apiClient.get<AccountInfo>("/auth/account/");
  return response.data;
}

/**
 * Update account username.
 */
export async function updateUsername(
  data: UsernameUpdateData,
): Promise<AccountInfo> {
  const response = await apiClient.patch<AccountInfo>(
    "/auth/account/update/",
    data,
  );
  return response.data;
}

/**
 * Initiate email change process (sends confirmation email).
 */
export async function changeEmail(
  data: EmailChangeData,
): Promise<EmailChangeResponse> {
  const response = await apiClient.post<EmailChangeResponse>(
    "/auth/account/change-email/",
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
    "/auth/account/confirm-email/",
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
    "/auth/account/password-change/",
    data,
  );
  return response.data;
}

/**
 * Soft delete user account (sends confirmation email).
 */
export async function deleteAccount(): Promise<AccountDeleteResponse> {
  const response = await apiClient.delete<AccountDeleteResponse>(
    "/auth/account/delete/",
  );
  return response.data;
}

/**
 * Confirm account deletion with token from email link.
 */
export async function confirmDeleteAccount(
  data: AccountDeleteConfirmData,
): Promise<AccountDeleteConfirmResponse> {
  const response = await apiClient.post<AccountDeleteConfirmResponse>(
    "/auth/account/confirm-delete/",
    data,
  );
  return response.data;
}

/**
 * Validate username without saving (for frontend inline validation).
 */
export async function validateUsername(
  data: UsernameValidationData,
): Promise<UsernameValidationResponse> {
  const response = await apiClient.post<UsernameValidationResponse>(
    "/auth/account/validate-username/",
    data,
  );
  return response.data;
}
