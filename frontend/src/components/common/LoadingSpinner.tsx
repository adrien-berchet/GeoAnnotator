/**
 * Loading spinner component.
 *
 * Displays consistent loading state across the application.
 */

interface LoadingSpinnerProps {
  size?: "small" | "medium" | "large";
  message?: string;
}

/**
 * Loading spinner component.
 */
export function LoadingSpinner({
  size = "medium",
  message,
}: LoadingSpinnerProps) {
  const sizeClasses = {
    small: "spinner-small",
    medium: "spinner-medium",
    large: "spinner-large",
  };

  return (
    <div className="loading-spinner-container">
      <div className={`spinner ${sizeClasses[size]}`}>
        <div className="spinner-circle"></div>
      </div>
      {message && <p className="loading-message">{message}</p>}
    </div>
  );
}
