/**
 * Text annotation preview component.
 *
 * Displays text annotations with basic formatting.
 */

import type { Annotation } from "../../types/annotation";

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
   */
  const formatText = (text: string): { __html: string } => {
    // Escape HTML tags for safety, then apply basic formatting
    const escaped = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Convert newlines to <br>
    const formatted = escaped.replace(/\n/g, "<br>");

    return { __html: formatted };
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

      <div
        className="preview-content"
        dangerouslySetInnerHTML={formatText(annotation.text_content)}
      />

      <div className="preview-meta">
        <span className="char-count">
          {annotation.text_content.length} characters
        </span>
      </div>
    </div>
  );
}
