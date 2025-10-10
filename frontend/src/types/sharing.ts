/**
 * Sharing types.
 */

export type Permission = 'view' | 'edit' | 'transfer';

export interface ShareData {
  email: string;
  permission: Permission;
}
