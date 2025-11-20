/**
 * Map layer selector component.
 *
 * Allows users to switch between different map tile layers (street, satellite, topographic, etc.).
 */

import { useState } from "react";
import "./MapLayerSelector.css";

export interface TileLayer {
  id: string;
  name: string;
  url: string;
  attribution: string;
  maxZoom: number;
}

/**
 * Available tile layers for the map.
 * Exported as a constant to avoid ESLint issues with react-refresh/only-export-components.
 */
// eslint-disable-next-line react-refresh/only-export-components
export const TILE_LAYERS: TileLayer[] = [
  {
    id: "osm",
    name: "Street Map",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 22,
  },
  {
    id: "satellite",
    name: "Satellite",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; <a href="https://www.esri.com/">Esri</a>',
    maxZoom: 22,
  },
  {
    id: "topo",
    name: "Topographic",
    url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    attribution:
      '&copy; <a href="https://opentopomap.org">OpenTopoMap</a> contributors',
    maxZoom: 22,
  },
  {
    id: "cycle",
    name: "Cycle Map",
    url: "https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png",
    attribution:
      '&copy; <a href="https://www.cyclosm.org">CyclOSM</a> contributors',
    maxZoom: 22,
  },
];

interface MapLayerSelectorProps {
  currentLayerId: string;
  onLayerChange: (layer: TileLayer) => void;
}

/**
 * Map layer selector component.
 */
export function MapLayerSelector({
  currentLayerId,
  onLayerChange,
}: MapLayerSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const currentLayer =
    TILE_LAYERS.find((layer) => layer.id === currentLayerId) || TILE_LAYERS[0];

  const handleLayerSelect = (layer: TileLayer) => {
    onLayerChange(layer);
    setIsOpen(false);
  };

  return (
    <div className="map-layer-selector">
      <button
        className="layer-selector-button"
        onClick={() => setIsOpen(!isOpen)}
        title="Change map type"
      >
        <span className="layer-icon">🗺️</span>
        <span className="layer-name">{currentLayer.name}</span>
        <span className={`dropdown-arrow ${isOpen ? "open" : ""}`}>▼</span>
      </button>

      {isOpen && (
        <>
          <div
            className="layer-selector-backdrop"
            onClick={() => setIsOpen(false)}
          />
          <div className="layer-selector-menu">
            {TILE_LAYERS.map((layer) => (
              <button
                key={layer.id}
                className={`layer-option ${layer.id === currentLayerId ? "active" : ""}`}
                onClick={() => handleLayerSelect(layer)}
              >
                <span className="layer-option-name">{layer.name}</span>
                {layer.id === currentLayerId && (
                  <span className="checkmark">✓</span>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
