/**
 * Progress bar component.
 *
 * Displays file upload progress or other loading progress.
 */

interface ProgressBarProps {
  progress: number; // 0-100
  label?: string;
  showPercentage?: boolean;
}

/**
 * Progress bar component.
 */
export function ProgressBar({
  progress,
  label,
  showPercentage = true,
}: ProgressBarProps) {
  // Clamp progress between 0 and 100
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div className="progress-bar-container">
      {label && <div className="progress-label">{label}</div>}

      <div className="progress-bar-wrapper">
        <div className="progress-bar-track">
          <div
            className="progress-bar-fill"
            style={{ width: `${clampedProgress}%` }}
            role="progressbar"
            aria-valuenow={clampedProgress}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>

        {showPercentage && (
          <span className="progress-percentage">
            {Math.round(clampedProgress)}%
          </span>
        )}
      </div>
    </div>
  );
}
