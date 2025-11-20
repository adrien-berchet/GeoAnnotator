/**
 * Sharing types.
 */

export type Permission = "view" | "edit" | "manage";

export interface ShareData {
  email: string;
  permission: Permission;
}
