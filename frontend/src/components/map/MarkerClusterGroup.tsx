/**
 * MarkerClusterGroup component for react-leaflet v5.
 *
 * Wraps leaflet.markercluster to provide clustering functionality for markers.
 */

import { useEffect, useRef } from "react";
import { useLeafletContext, LeafletContext } from "@react-leaflet/core";
import L from "leaflet";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "./MarkerClusterGroup.css";

interface MarkerClusterGroupProps extends L.MarkerClusterGroupOptions {
  children?: React.ReactNode;
}

/**
 * MarkerClusterGroup component for react-leaflet v5.
 *
 * This component creates a MarkerClusterGroup layer and provides it as the
 * layerContainer context for child markers, ensuring they are automatically
 * clustered.
 *
 * Usage:
 * ```tsx
 * <MapContainer>
 *   <MarkerClusterGroup>
 *     <Marker position={[51.5, -0.1]} />
 *     <Marker position={[51.51, -0.1]} />
 *   </MarkerClusterGroup>
 * </MapContainer>
 * ```
 */
export function MarkerClusterGroup({ children, ...options }: MarkerClusterGroupProps) {
  const parentContext = useLeafletContext();

  // Create the cluster group once and store in ref
  // We use a ref to avoid recreating it when options object changes
  // (options is a new object on every render from MapPage)
  const clusterGroupRef = useRef<L.MarkerClusterGroup | null>(null);
  if (clusterGroupRef.current === null) {
    // Add options to prevent cluster from refreshing/resetting
    const clusterOptions = {
      ...options,
      animateAddingMarkers: false, // Disable animations to prevent resets
      removeOutsideVisibleBounds: false, // Keep all clusters in DOM
    };
    clusterGroupRef.current = new L.MarkerClusterGroup(clusterOptions);
  }
  const clusterGroup = clusterGroupRef.current;

  // Store context in ref for absolute stability across all browsers
  // Firefox seems to handle context changes differently than Chrome
  const contextRef = useRef<any>(null);
  if (contextRef.current === null) {
    contextRef.current = {
      __version: parentContext.__version,
      map: parentContext.map,
      layerContainer: clusterGroup,
    };
  }

  useEffect(() => {
    // Add to parent container (map) once on mount
    const container = parentContext.layerContainer || parentContext.map;
    container.addLayer(clusterGroup);

    // Cleanup on unmount
    return () => {
      container.removeLayer(clusterGroup);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - only run once on mount

  return (
    <LeafletContext.Provider value={contextRef.current}>{children}</LeafletContext.Provider>
  );
}
