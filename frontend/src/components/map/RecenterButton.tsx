/**
 * Recenter button component.
 *
 * Button to recenter the map on the user's current device position.
 * Disabled when device position is unavailable.
 */

import "./RecenterButton.css";

interface RecenterButtonProps {
  onClick: () => void;
  disabled?: boolean;
}

/**
 * Button to recenter map on device position.
 *
 * @param onClick - Callback when button is clicked
 * @param disabled - Whether button is disabled
 */
export function RecenterButton({
  onClick,
  disabled = false,
}: RecenterButtonProps) {
  return (
    <button
      className={`recenter-button ${disabled ? "disabled" : ""}`}
      onClick={onClick}
      disabled={disabled}
      title={disabled ? "Location unavailable" : "Recenter on my location"}
      aria-label={
        disabled
          ? "Recenter on my location (disabled)"
          : "Recenter on my location"
      }
      type="button"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <circle
          cx="12"
          cy="12"
          r="3"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
        />
        <path
          d="M12 2V5M12 19V22M22 12H19M5 12H2"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    </button>
  );
}
