/**
 * MarkerClusterGroup component for react-leaflet v5.
 *
 * Wraps leaflet.markercluster to provide clustering functionality for markers.
 */

import { useEffect, useMemo } from "react";
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

  // Create the cluster group synchronously so it exists before children render
  const clusterGroup = useMemo(() => {
    return new L.MarkerClusterGroup(options);
  }, [options]);

  useEffect(() => {
    // Add to parent container (map)
    const container = parentContext.layerContainer || parentContext.map;
    container.addLayer(clusterGroup);

    // Cleanup
    return () => {
      container.removeLayer(clusterGroup);
    };
  }, [parentContext, clusterGroup]);

  // Create a new context with the cluster group as the layer container
  const context = useMemo(
    () => ({
      ...parentContext,
      layerContainer: clusterGroup,
    }),
    [parentContext, clusterGroup]
  );

  return (
    <LeafletContext.Provider value={context}>{children}</LeafletContext.Provider>
  );
}
