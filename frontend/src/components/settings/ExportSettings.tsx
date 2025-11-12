/**
 * Export settings component for selecting data export format
 */

import { useLanguage } from "@/contexts/LanguageContext";
import type { ExportFormat } from "@/types/settings";
import "./ExportSettings.css";

interface ExportSettingsProps {
  value: ExportFormat;
  onChange: (format: ExportFormat) => void;
}

const formatOptions: Array<{
  value: ExportFormat;
  icon: string;
}> = [
  {
    value: "geojson",
    icon: "🗺️",
  },
  {
    value: "kml",
    icon: "🌍",
  },
  {
    value: "csv",
    icon: "📊",
  },
];

function ExportSettings({ value, onChange }: ExportSettingsProps) {
  const { t } = useLanguage();
  return (
    <div
      className="export-settings"
      role="radiogroup"
      aria-label={t("settings.defaultExportFormat", "Export format selection")}
    >
      {formatOptions.map((option) => {
        const isSelected = value === option.value;
        const label = t(`exportFormat.${option.value}`, option.value);
        const description = t(`exportFormat.${option.value}Desc`, "");
        return (
          <label
            key={option.value}
            className={`export-option ${isSelected ? "selected" : ""}`}
          >
            <input
              type="radio"
              name="export-format"
              value={option.value}
              checked={isSelected}
              onChange={() => onChange(option.value)}
              aria-checked={isSelected}
              aria-label={`${label}: ${description}`}
            />
            <div className="export-content">
              <span className="export-icon" aria-hidden="true">
                {option.icon}
              </span>
              <div className="export-text">
                <span className="export-label">{label}</span>
                <span className="export-description">{description}</span>
              </div>
            </div>
          </label>
        );
      })}
    </div>
  );
}

export default ExportSettings;
