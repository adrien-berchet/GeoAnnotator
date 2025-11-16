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
  const clusterGroupRef = useRef<L.MarkerClusterGroup | null>(null);

  useEffect(() => {
    // Create the cluster group
    const clusterGroup = new L.MarkerClusterGroup(options);
    clusterGroupRef.current = clusterGroup;

    // Add to parent container (map)
    const container = parentContext.layerContainer || parentContext.map;
    container.addLayer(clusterGroup);

    // Cleanup
    return () => {
      if (clusterGroupRef.current) {
        container.removeLayer(clusterGroupRef.current);
        clusterGroupRef.current = null;
      }
    };
  }, [parentContext, options]);

  // Create a new context with the cluster group as the layer container
  const context = useMemo(
    () => ({
      ...parentContext,
      layerContainer: clusterGroupRef.current || parentContext.layerContainer,
    }),
    [parentContext]
  );

  return clusterGroupRef.current ? (
    <LeafletContext.Provider value={context}>{children}</LeafletContext.Provider>
  ) : null;
}
