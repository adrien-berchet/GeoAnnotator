/**
 * Leaflet configuration and icon fixes.
 */

import L from "leaflet";

/**
 * Fix Leaflet default icon paths for Vite.
 * Leaflet's default icon images don't work out of the box with Vite.
 */
export function initializeLeaflet() {
  // Fix default icon paths
  delete (L.Icon.Default.prototype as any)._getIconUrl;

  L.Icon.Default.mergeOptions({
    iconRetinaUrl:
      "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  });
}
