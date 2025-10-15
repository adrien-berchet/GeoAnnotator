/**
 * Rehype plugin to add security attributes to external links.
 *
 * This plugin modifies all anchor elements in the markdown Abstract Syntax Tree (AST)
 * to open in new tabs with security attributes that prevent tabnapping attacks.
 *
 * @module rehypeExternalLinks
 *
 * ## Security Features
 *
 * - **target="_blank"**: Opens links in a new tab/window for better UX
 * - **rel="noopener"**: Prevents the new page from accessing `window.opener`
 * - **rel="noreferrer"**: Prevents the browser from sending the HTTP Referer header
 *
 * ## Tabnapping Attack Prevention
 *
 * Without `rel="noopener noreferrer"`, a malicious external page opened via a link
 * could use `window.opener.location` to redirect the original page to a phishing site.
 * This plugin mitigates that attack vector.
 *
 * @see https://owasp.org/www-community/attacks/Reverse_Tabnapping
 *
 * @example
 * ```tsx
 * import rehypeSanitize from 'rehype-sanitize';
 * import { rehypeExternalLinks } from './utils/rehypeExternalLinks';
 *
 * <MDEditor.Markdown
 *   source="[Example](https://example.com)"
 *   rehypePlugins={[rehypeSanitize, rehypeExternalLinks]}
 * />
 * // Renders: <a href="https://example.com" target="_blank" rel="noopener noreferrer">Example</a>
 * ```
 */

import { visit } from 'unist-util-visit';
import type { Element, Root } from 'hast';

/**
 * Rehype plugin that adds security attributes to all anchor elements.
 *
 * This plugin traverses the HAST (HTML Abstract Syntax Tree) and modifies
 * all `<a>` elements to include security attributes.
 *
 * **Usage**:
 * Add this plugin to the `rehypePlugins` array of MDEditor.Markdown:
 *
 * ```tsx
 * <MDEditor.Markdown
 *   source={markdownContent}
 *   rehypePlugins={[rehypeSanitize, rehypeExternalLinks]}
 * />
 * ```
 *
 * **Note**: This plugin should be applied **after** `rehypeSanitize` to ensure
 * only safe content is processed.
 *
 * @returns {(tree: Root) => void} A rehype transformer function
 *
 * @example
 * // Input markdown:
 * "[Click here](https://example.com)"
 *
 * // Output HTML:
 * <a href="https://example.com" target="_blank" rel="noopener noreferrer">
 *   Click here
 * </a>
 */
export function rehypeExternalLinks() {
  return (tree: Root) => {
    visit(tree, 'element', (node: Element) => {
      if (node.tagName === 'a' && node.properties) {
        // Add target="_blank" to open in new tab
        node.properties.target = '_blank';

        // Add security attributes to prevent tabnapping
        // - noopener: Prevents access to window.opener
        // - noreferrer: Prevents sending HTTP Referer header
        node.properties.rel = 'noopener noreferrer';
      }
    });
  };
}
