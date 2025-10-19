/**
 * Map type selector component for settings
 */

import { useLanguage } from '@/contexts/LanguageContext';
import type { MapType } from '@/types/settings';
import './MapTypeSelector.css';

interface MapTypeSelectorProps {
  value: MapType;
  onChange: (mapType: MapType) => void;
}

const MAP_TYPE_OPTIONS: Array<{
  value: MapType;
  icon: string;
}> = [
  { value: 'osm', icon: '🗺️' },
  { value: 'satellite', icon: '🛰️' },
  { value: 'topo', icon: '⛰️' },
  { value: 'cycle', icon: '🚴' },
];

export default function MapTypeSelector({ value, onChange }: MapTypeSelectorProps) {
  const { t } = useLanguage();

  return (
    <div className="map-type-selector" role="radiogroup" aria-label={t('settings.defaultMapType', 'Default Map Type')}>
      {MAP_TYPE_OPTIONS.map((option) => {
        const isSelected = value === option.value;
        return (
          <label
            key={option.value}
            className={`map-type-option ${isSelected ? 'selected' : ''}`}
          >
            <input
              type="radio"
              name="map-type"
              value={option.value}
              checked={isSelected}
              onChange={() => onChange(option.value)}
              aria-checked={isSelected}
              aria-label={t(`mapType.${option.value}`, option.value)}
            />
            <div className="map-type-content">
              <span className="map-type-icon" aria-hidden="true">
                {option.icon}
              </span>
              <span className="map-type-label">{t(`mapType.${option.value}`, option.value)}</span>
            </div>
          </label>
        );
      })}
    </div>
  );
}
