/**
 * Map view component.
 *
 * Displays interactive Leaflet map with tile layer, viewport management, and clustering.
 */

import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import type { Map as LeafletMap } from "leaflet";
import "leaflet/dist/leaflet.css";
import { initializeLeaflet } from "../../utils/leaflet-config";
import { logger } from "../../utils/logger";
import type { TileLayer as TileLayerType } from "./MapLayerSelector";
import { DEFAULT_TILE_LAYER } from "./MapLayerSelector";

// Initialize Leaflet configuration
initializeLeaflet();

interface MapViewProps {
  center?: [number, number];
  zoom?: number;
  onMapReady?: (map: LeafletMap) => void;
  children?: React.ReactNode;
  tileLayer?: TileLayerType;
}

/**
 * Component to handle map instance after initialization.
 */
function MapEventHandler({
  onMapReady,
}: {
  onMapReady?: (map: LeafletMap) => void;
}) {
  const map = useMap();

  useEffect(() => {
    if (onMapReady) {
      onMapReady(map);
    }
  }, [map, onMapReady]);

  return null;
}

/**
 * Component to add scale control to the map.
 */
function ScaleControlHandler() {
  const map = useMap();
  const scaleAddedRef = useRef(false);

  useEffect(() => {
    if (!scaleAddedRef.current) {
      try {
        // Only add scale if map has the required methods (not in test mocks)
        if (map && typeof map.whenReady === "function") {
          L.control.scale({ position: "bottomleft" }).addTo(map);
          scaleAddedRef.current = true;
        }
      } catch (error) {
        // Silently ignore errors in test environment
        logger.debug("Could not add scale control:", error);
      }
    }
  }, [map]);

  return null;
}

/**
 * Map view component.
 */
export function MapView({
  center = [48.8566, 2.3522], // Default to Paris
  zoom = 13,
  onMapReady,
  children,
  tileLayer,
}: MapViewProps) {
  const mapRef = useRef<LeafletMap | null>(null);

  const activeLayer = tileLayer || DEFAULT_TILE_LAYER;

  return (
    <div className="map-view-container">
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: "100%", width: "100%" }}
        ref={mapRef}
      >
        {/* Dynamic tile layer */}
        <TileLayer
          key={activeLayer.id}
          attribution={activeLayer.attribution}
          url={activeLayer.url}
          maxZoom={activeLayer.maxZoom}
          maxNativeZoom={activeLayer.maxNativeZoom}
        />

        {/* Map event handler */}
        <MapEventHandler onMapReady={onMapReady} />

        {/* Scale control */}
        <ScaleControlHandler />

        {/* Additional children (markers, popups, etc.) */}
        {children}
      </MapContainer>
    </div>
  );
}
