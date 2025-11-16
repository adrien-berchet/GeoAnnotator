/**
 * MarkerClusterGroup component for react-leaflet v5.
 *
 * Wraps leaflet.markercluster to provide clustering functionality for markers.
 */

import { useEffect, useRef, useMemo } from "react";
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
    clusterGroupRef.current = new L.MarkerClusterGroup(options);
  }
  const clusterGroup = clusterGroupRef.current;

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

  // Create a completely stable context that never changes
  // Using useMemo with empty deps ensures this object is created once and reused
  const context = useMemo(() => {
    return {
      __version: parentContext.__version,
      map: parentContext.map,
      layerContainer: clusterGroup,
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps - create once and never change

  return (
    <LeafletContext.Provider value={context}>{children}</LeafletContext.Provider>
  );
}
