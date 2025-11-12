/**
 * Account management hook.
 *
 * Provides functions for managing user account (pseudonym, email, password, deletion).
 */

import { useState, useCallback } from "react";
import {
  getAccount,
  updatePseudonym,
  changeEmail,
  confirmEmail,
  changePassword,
  deleteAccount,
  confirmDeleteAccount,
  validatePseudonym,
} from "../api/account";
import type {
  AccountInfo,
  PseudonymUpdateData,
  EmailChangeData,
  EmailChangeResponse,
  EmailConfirmData,
  EmailConfirmResponse,
  PasswordChangeData,
  PasswordChangeResponse,
  AccountDeleteResponse,
  AccountDeleteConfirmData,
  AccountDeleteConfirmResponse,
  PseudonymValidationData,
  PseudonymValidationResponse,
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
  updateAccountPseudonym: (data: PseudonymUpdateData) => Promise<AccountInfo>;
  requestEmailChange: (data: EmailChangeData) => Promise<EmailChangeResponse>;
  confirmEmailChange: (data: EmailConfirmData) => Promise<EmailConfirmResponse>;
  updatePassword: (data: PasswordChangeData) => Promise<PasswordChangeResponse>;
  requestAccountDeletion: () => Promise<AccountDeleteResponse>;
  confirmAccountDeletion: (
    data: AccountDeleteConfirmData,
  ) => Promise<AccountDeleteConfirmResponse>;
  checkPseudonym: (
    data: PseudonymValidationData,
  ) => Promise<PseudonymValidationResponse>;
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
   * Update account pseudonym.
   */
  const updateAccountPseudonym = useCallback(
    async (data: PseudonymUpdateData): Promise<AccountInfo> => {
      setIsUpdating(true);
      setError(null);

      try {
        const updated = await updatePseudonym(data);
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
   * Validate pseudonym (for inline validation).
   */
  const checkPseudonym = useCallback(
    async (
      data: PseudonymValidationData,
    ): Promise<PseudonymValidationResponse> => {
      setIsValidating(true);
      setError(null);

      try {
        const response = await validatePseudonym(data);
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
    updateAccountPseudonym,
    requestEmailChange,
    confirmEmailChange,
    updatePassword,
    requestAccountDeletion,
    confirmAccountDeletion,
    checkPseudonym,
    clearError,
  };
}
