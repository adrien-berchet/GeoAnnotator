/**
 * Text annotation preview component.
 *
 * Displays text annotations with basic formatting.
 */

import type { Annotation } from "../../types/annotation";
import { SanitizedHTML } from "../common/SanitizedHTML";

interface TextAnnotationPreviewProps {
  annotation: Annotation;
}

/**
 * Text annotation preview component.
 */
export function TextAnnotationPreview({
  annotation,
}: TextAnnotationPreviewProps) {
  if (annotation.type !== "text" || !annotation.text_content) {
    return null;
  }

  /**
   * Format text with basic HTML rendering.
   * Converts newlines to <br> tags. Sanitization is handled by SanitizedHTML component.
   */
  const formatText = (text: string): string => {
    // Convert newlines to <br> tags
    return text.replace(/\n/g, "<br>");
  };

  /**
   * Format date.
   */
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="text-annotation-preview">
      <div className="preview-header">
        <span className="preview-icon">📝</span>
        <div className="preview-info">
          <h4>Text Note</h4>
          <span className="preview-date">
            {formatDate(annotation.created_at)}
          </span>
        </div>
      </div>

      <SanitizedHTML
        html={formatText(annotation.text_content)}
        className="preview-content"
      />

      <div className="preview-meta">
        <span className="char-count">
          {annotation.text_content.length} characters
        </span>
      </div>
    </div>
  );
}
