/**
 * Export settings component for selecting data export format
 */

import type { ExportFormat } from '@/types/settings';
import './ExportSettings.css';

interface ExportSettingsProps {
  value: ExportFormat;
  onChange: (format: ExportFormat) => void;
}

const formatOptions: Array<{
  value: ExportFormat;
  label: string;
  description: string;
  icon: string;
}> = [
  {
    value: 'geojson',
    label: 'GeoJSON',
    description: 'Standard geographic data format',
    icon: '🗺️',
  },
  {
    value: 'kml',
    label: 'KML',
    description: 'Google Earth compatible format',
    icon: '🌍',
  },
  {
    value: 'csv',
    label: 'CSV',
    description: 'Spreadsheet compatible format',
    icon: '📊',
  },
];

function ExportSettings({ value, onChange }: ExportSettingsProps) {
  return (
    <div className="export-settings" role="radiogroup" aria-label="Export format selection">
      {formatOptions.map((option) => {
        const isSelected = value === option.value;
        return (
          <label
            key={option.value}
            className={`export-option ${isSelected ? 'selected' : ''}`}
          >
            <input
              type="radio"
              name="export-format"
              value={option.value}
              checked={isSelected}
              onChange={() => onChange(option.value)}
              aria-checked={isSelected}
              aria-label={`${option.label}: ${option.description}`}
            />
            <div className="export-content">
              <span className="export-icon" aria-hidden="true">
                {option.icon}
              </span>
              <div className="export-text">
                <span className="export-label">{option.label}</span>
                <span className="export-description">{option.description}</span>
              </div>
            </div>
          </label>
        );
      })}
    </div>
  );
}

export default ExportSettings;
