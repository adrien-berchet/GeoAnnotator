/**
 * Account management hook.
 *
 * Provides functions for managing user account (username, email, password, deletion).
 */

import { useState, useCallback } from "react";
import {
  getAccount,
  updateUsername,
  changeEmail,
  confirmEmail,
  changePassword,
  deleteAccount,
  confirmDeleteAccount,
  validateUsername,
} from "../api/account";
import type {
  AccountInfo,
  UsernameUpdateData,
  EmailChangeData,
  EmailChangeResponse,
  EmailConfirmData,
  EmailConfirmResponse,
  PasswordChangeData,
  PasswordChangeResponse,
  AccountDeleteResponse,
  AccountDeleteConfirmData,
  AccountDeleteConfirmResponse,
  UsernameValidationData,
  UsernameValidationResponse,
} from "../api/account";
import { getErrorMessage } from "../api/client";

/**
 * Account management hook state.
 */
export interface UseAccountResult {
  // Data
  account: AccountInfo | null;

  // Loading states
  isLoading: boolean;
  isUpdating: boolean;
  isValidating: boolean;

  // Error states
  error: string | null;

  // Actions
  fetchAccount: () => Promise<void>;
  updateAccountUsername: (data: UsernameUpdateData) => Promise<AccountInfo>;
  requestEmailChange: (data: EmailChangeData) => Promise<EmailChangeResponse>;
  confirmEmailChange: (data: EmailConfirmData) => Promise<EmailConfirmResponse>;
  updatePassword: (data: PasswordChangeData) => Promise<PasswordChangeResponse>;
  requestAccountDeletion: () => Promise<AccountDeleteResponse>;
  confirmAccountDeletion: (
    data: AccountDeleteConfirmData,
  ) => Promise<AccountDeleteConfirmResponse>;
  checkUsername: (
    data: UsernameValidationData,
  ) => Promise<UsernameValidationResponse>;
  clearError: () => void;
}

/**
 * Hook for account management operations.
 */
export function useAccount(): UseAccountResult {
  const [account, setAccount] = useState<AccountInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch current account information.
   */
  const fetchAccount = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getAccount();
      setAccount(data);
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Update account username.
   */
  const updateAccountUsername = useCallback(
    async (data: UsernameUpdateData): Promise<AccountInfo> => {
      setIsUpdating(true);
      setError(null);

      try {
        const updated = await updateUsername(data);
        setAccount(updated);
        return updated;
      } catch (err) {
        const message = getErrorMessage(err);
        setError(message);
        throw err;
      } finally {
        setIsUpdating(false);
      }
    },
    [],
  );

  /**
   * Request email change (sends confirmation email).
   */
  const requestEmailChange = useCallback(
    async (data: EmailChangeData): Promise<EmailChangeResponse> => {
      setIsUpdating(true);
      setError(null);

      try {
        const response = await changeEmail(data);
        return response;
      } catch (err) {
        const message = getErrorMessage(err);
        setError(message);
        throw err;
      } finally {
        setIsUpdating(false);
      }
    },
    [],
  );

  /**
   * Confirm email change with token.
   */
  const confirmEmailChange = useCallback(
    async (data: EmailConfirmData): Promise<EmailConfirmResponse> => {
      setIsUpdating(true);
      setError(null);

      try {
        const response = await confirmEmail(data);
        // Refresh account info to get updated email
        await fetchAccount();
        return response;
      } catch (err) {
        const message = getErrorMessage(err);
        setError(message);
        throw err;
      } finally {
        setIsUpdating(false);
      }
    },
    [fetchAccount],
  );

  /**
   * Change password.
   */
  const updatePassword = useCallback(
    async (data: PasswordChangeData): Promise<PasswordChangeResponse> => {
      setIsUpdating(true);
      setError(null);

      try {
        const response = await changePassword(data);
        return response;
      } catch (err) {
        const message = getErrorMessage(err);
        setError(message);
        throw err;
      } finally {
        setIsUpdating(false);
      }
    },
    [],
  );

  /**
   * Request account deletion (sends confirmation email).
   */
  const requestAccountDeletion =
    useCallback(async (): Promise<AccountDeleteResponse> => {
      setIsUpdating(true);
      setError(null);

      try {
        const response = await deleteAccount();
        return response;
      } catch (err) {
        const message = getErrorMessage(err);
        setError(message);
        throw err;
      } finally {
        setIsUpdating(false);
      }
    }, []);

  /**
   * Confirm account deletion with token.
   */
  const confirmAccountDeletion = useCallback(
    async (
      data: AccountDeleteConfirmData,
    ): Promise<AccountDeleteConfirmResponse> => {
      setIsUpdating(true);
      setError(null);

      try {
        const response = await confirmDeleteAccount(data);
        return response;
      } catch (err) {
        const message = getErrorMessage(err);
        setError(message);
        throw err;
      } finally {
        setIsUpdating(false);
      }
    },
    [],
  );

  /**
   * Validate username (for inline validation).
   */
  const checkUsername = useCallback(
    async (
      data: UsernameValidationData,
    ): Promise<UsernameValidationResponse> => {
      setIsValidating(true);
      setError(null);

      try {
        const response = await validateUsername(data);
        return response;
      } catch (err) {
        const message = getErrorMessage(err);
        setError(message);
        throw err;
      } finally {
        setIsValidating(false);
      }
    },
    [],
  );

  /**
   * Clear error message.
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    account,
    isLoading,
    isUpdating,
    isValidating,
    error,
    fetchAccount,
    updateAccountUsername,
    requestEmailChange,
    confirmEmailChange,
    updatePassword,
    requestAccountDeletion,
    confirmAccountDeletion,
    checkUsername,
    clearError,
  };
}
