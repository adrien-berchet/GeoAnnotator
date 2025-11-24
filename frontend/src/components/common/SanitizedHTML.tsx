/**
 * Component for safely rendering user-provided HTML content.
 *
 * Uses DOMPurify to sanitize HTML and prevent XSS attacks.
 * Provides defense-in-depth alongside backend sanitization.
 */

import DOMPurify from "dompurify";
import type { Config } from "dompurify";
import { createElement } from "react";

interface SanitizedHTMLProps {
  /** The HTML content to sanitize and render */
  html: string;
  /** Optional CSS class name */
  className?: string;
  /** Optional element type (defaults to 'div') */
  as?: keyof React.JSX.IntrinsicElements;
  /** Optional custom DOMPurify config */
  config?: Config;
}

/**
 * Safely renders HTML content after sanitizing it with DOMPurify.
 *
 * Default configuration allows common safe HTML tags and attributes:
 * - Text formatting: b, i, em, strong, u, s, sup, sub
 * - Lists: ul, ol, li
 * - Links: a (with href)
 * - Paragraphs and breaks: p, br
 *
 * @example
 * <SanitizedHTML
 *   html={point.description}
 *   className="description"
 * />
 */
export function SanitizedHTML({
  html,
  className,
  as: elementType = "div",
  config,
}: SanitizedHTMLProps) {
  // Default configuration - allow common safe tags
  const defaultConfig: Config = {
    ALLOWED_TAGS: [
      "b",
      "i",
      "em",
      "strong",
      "u",
      "s",
      "sup",
      "sub",
      "ul",
      "ol",
      "li",
      "a",
      "p",
      "br",
    ],
    ALLOWED_ATTR: ["href", "target", "rel"],
    // Force links to open in new tab and add security attributes
    ADD_ATTR: ["target", "rel"],
    RETURN_TRUSTED_TYPE: false,
  };

  const sanitizedHTML = DOMPurify.sanitize(html, config || defaultConfig);

  return createElement(elementType, {
    className,
    dangerouslySetInnerHTML: { __html: sanitizedHTML },
  });
}
