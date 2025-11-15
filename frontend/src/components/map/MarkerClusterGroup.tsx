/**
 * MarkerClusterGroup component for react-leaflet v5.
 *
 * Wraps leaflet.markercluster to provide clustering functionality for markers.
 */

import { createPathComponent } from "@react-leaflet/core";
import L from "leaflet";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "./MarkerClusterGroup.css";

interface MarkerClusterGroupProps extends L.MarkerClusterGroupOptions {
  children: React.ReactNode;
}

/**
 * Create a MarkerClusterGroup component using the react-leaflet v5 API.
 */
const createClusterCustomComponent = (props: MarkerClusterGroupProps) => {
  const clusterProps: L.MarkerClusterGroupOptions = { ...props };
  const clusterEvents = {};

  const cluster = new L.MarkerClusterGroup(clusterProps);

  return {
    instance: cluster,
    context: { layerContainer: cluster } as any,
    clusterEvents,
  };
};

const updateClusterCustomComponent = (
  _instance: L.MarkerClusterGroup,
  _props: MarkerClusterGroupProps,
  _prevProps: MarkerClusterGroupProps
) => {
  // Handle prop updates if needed
  // For now, we don't need to update anything dynamically
};

/**
 * MarkerClusterGroup component for react-leaflet v5.
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
export const MarkerClusterGroup = createPathComponent<
  L.MarkerClusterGroup,
  MarkerClusterGroupProps
>(createClusterCustomComponent, updateClusterCustomComponent);
