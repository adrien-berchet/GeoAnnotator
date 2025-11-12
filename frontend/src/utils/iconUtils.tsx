/**
 * Utility functions for handling point type icons.
 *
 * Supports emojis, URLs, and base64 data URIs.
 */

/**
 * Check if an icon string represents an image (URL or data URI) vs an emoji.
 *
 * @param icon - The icon string (emoji, URL, or data URI)
 * @returns true if icon is an image URL or data URI, false if it's an emoji
 */
export function isImageIcon(icon: string): boolean {
  if (!icon) return false;
  return (
    icon.startsWith("http") || icon.startsWith("/") || icon.startsWith("data:")
  );
}

/**
 * Render an icon as JSX (either img tag or emoji span).
 *
 * @param icon - The icon string
 * @param className - CSS class for the icon element
 * @param alt - Alt text for image icons
 * @returns JSX element
 */
export function renderIcon(
  icon: string | undefined,
  className: string = "type-icon",
  alt: string = "",
) {
  if (!icon || icon === "/icons/default.svg") {
    return <span className={`${className}-emoji`}>📍</span>;
  }

  if (isImageIcon(icon)) {
    return (
      <img
        src={icon}
        alt={alt}
        className={className}
        onError={(e) => {
          // Fallback to placeholder on error
          e.currentTarget.style.display = "none";
        }}
      />
    );
  }

  // It's an emoji
  return <span className={`${className}-emoji`}>{icon}</span>;
}
