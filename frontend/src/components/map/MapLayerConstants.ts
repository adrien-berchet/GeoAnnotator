/**
 * Constants for map layer configuration.
 * Separated to solve react-refresh/only-export-components eslint issue.
 */

import type { MapType } from "../../types/settings";

export const MAP_TYPE_LAYERS: Record<MapType, string> = {
  osm: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  satellite:
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  topo: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
  cycle: "https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png",
};
