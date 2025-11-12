/**
 * Permission selector component.
 *
 * Dropdown for selecting share permission levels.
 */

import type { Permission } from "../../types/sharing";

interface PermissionSelectorProps {
  value: Permission;
  onChange: (permission: Permission) => void;
  disabled?: boolean;
}

/**
 * Permission descriptions.
 */
const PERMISSION_INFO: Record<
  Permission,
  { label: string; description: string; icon: string }
> = {
  view: {
    label: "View",
    description: "Can view point and annotations",
    icon: "👁️",
  },
  edit: {
    label: "Edit",
    description: "Can view and modify point",
    icon: "✏️",
  },
  transfer: {
    label: "Transfer",
    description: "Can transfer ownership",
    icon: "👑",
  },
};

/**
 * Permission selector component.
 */
export function PermissionSelector({
  value,
  onChange,
  disabled = false,
}: PermissionSelectorProps) {
  return (
    <div className="permission-selector">
      <select
        id="share-permission"
        value={value}
        onChange={(e) => onChange(e.target.value as Permission)}
        disabled={disabled}
        className="permission-select"
      >
        {(Object.keys(PERMISSION_INFO) as Permission[]).map((permission) => (
          <option key={permission} value={permission}>
            {PERMISSION_INFO[permission].icon}{" "}
            {PERMISSION_INFO[permission].label}
          </option>
        ))}
      </select>

      {/* Permission description */}
      <div className="permission-description">
        <small>{PERMISSION_INFO[value].description}</small>
      </div>

      {/* Permission hierarchy info */}
      <div className="permission-hierarchy">
        <small className="hierarchy-hint">
          {value === "view" && "• Basic access level"}
          {value === "edit" && "• Includes View permissions"}
          {value === "transfer" && "• Includes View and Edit permissions"}
        </small>
      </div>
    </div>
  );
}
