# Markdown Support in Text Annotations

GeoAnnotator supports **Markdown formatting** for text annotations, allowing you to create rich, formatted notes with headings, lists, links, code blocks, and more.

## What is Markdown?

Markdown is a lightweight markup language that lets you format text using simple syntax. It's easy to learn and widely used for documentation, notes, and web content.

## Supported Markdown Elements

### Headings

Create headings using `#` symbols (1-6 levels):

```markdown
# Heading 1
## Heading 2
### Heading 3
```

**Renders as**:
# Heading 1
## Heading 2
### Heading 3

### Text Formatting

- **Bold**: `**bold text**` → **bold text**
- *Italic*: `*italic text*` → *italic text*
- ***Bold and Italic***: `***bold italic***` → ***bold italic***

### Lists

**Unordered lists** (bullets):
```markdown
- Item 1
- Item 2
  - Nested item
  - Another nested item
```

**Ordered lists** (numbers):
```markdown
1. First item
2. Second item
   1. Nested item
   2. Another nested item
```

### Links

Create clickable links:

```markdown
[Link text](https://example.com)
```

**Security**: External links automatically open in a new tab with security attributes to prevent malicious redirects.

### Code

**Inline code**: Use backticks for short code snippets:
```markdown
Use the `console.log()` function
```

**Code blocks**: Use triple backticks for longer code:
````markdown
```javascript
function hello() {
  console.log("Hello, world!");
}
```
````

**Supported languages**: JavaScript, Python, TypeScript, JSON, HTML, CSS, Bash, and many more.

### Blockquotes

Create quotes using `>`:

```markdown
> This is a quoted text.
> It can span multiple lines.
```

**Renders as**:
> This is a quoted text.
> It can span multiple lines.

### Horizontal Rules

Create visual separators:

```markdown
---
```

### Line Breaks

- **Single line break**: Add two spaces at the end of a line
- **Paragraph break**: Leave an empty line between paragraphs

## Example Annotation

Here's a complete example showing various Markdown elements:

```markdown
# Field Observation: Site A

## Weather Conditions
- Temperature: 22°C
- Humidity: 65%
- Wind: Light breeze from SE

## Species Found
1. **Quercus robur** (English Oak)
2. *Fagus sylvatica* (European Beech)
3. **Betula pendula** (Silver Birch)

## Notes
The oak tree shows signs of **disease** on the lower branches. Further investigation needed.

Reference: [Tree Disease Guide](https://example.com/guide)

> "The health of the forest is the health of the community."

### Data
```json
{
  "tree_id": "OAK-2024-001",
  "height_m": 12.5,
  "dbh_cm": 45
}
```

---

**Next visit**: 2024-12-15
```

## Creating a Text Annotation

1. **Navigate to a GPS point** on the map
2. **Click "Add Annotation"**
3. **Select "Text Note"**
4. **Write your content** using Markdown syntax
5. **Preview** your formatted text (optional)
6. **Save** the annotation

## Editing Annotations

1. **Open the point details** page
2. **Find the annotation** you want to edit
3. **Click "Edit"** (for text annotations)
4. **Modify the Markdown** content
5. **Save** your changes

## Theme Support

Markdown rendering automatically adapts to your system's light/dark theme:
- **Light mode**: Dark text on light background
- **Dark mode**: Light text on dark background

Code blocks, links, and other elements adjust their colors for optimal readability.

## Security & Safety

### XSS Protection

All Markdown content is **automatically sanitized** to prevent cross-site scripting (XSS) attacks. Malicious HTML and JavaScript are stripped before rendering.

**What's allowed**:
- Standard Markdown elements (headings, lists, links, code, blockquotes)
- Safe HTML elements (emphasis, strong, paragraphs)

**What's blocked**:
- `<script>` tags
- `<iframe>` elements
- `onclick` and other event handlers
- Potentially dangerous HTML attributes

### Link Security

External links in annotations:
- Open in **new tabs** (`target="_blank"`)
- Include **security attributes** (`rel="noopener noreferrer"`)
- Prevent **tabnapping attacks** (malicious sites redirecting the original page)

## Accessibility

Markdown rendering is **WCAG 2.1 Level AA compliant**:
- **Semantic HTML**: Headings, lists, and links use proper HTML elements
- **Keyboard accessible**: Navigate through links and buttons using Tab key
- **Screen reader friendly**: Content is announced correctly by assistive technologies
- **Sufficient contrast**: Text colors meet accessibility standards (4.5:1 ratio)

## Performance

Markdown rendering is optimized for speed:
- **Fast parsing**: <50ms per annotation
- **Efficient rendering**: Up to 20 annotations load in <500ms
- **No lag**: Smooth scrolling even with many annotations

## Tips & Best Practices

### Use Headings for Structure

Organize long notes with headings:
```markdown
## Observation 1
Details...

## Observation 2
Details...
```

### Break Up Large Blocks of Text

Use paragraphs and lists for better readability:
```markdown
Species observed:
- Oak
- Birch
- Beech

All trees appear healthy.
```

### Include Links for References

Add external resources:
```markdown
More info: [Species Database](https://example.com)
```

### Use Code Blocks for Data

Store structured data:
```markdown
```json
{"latitude": 51.5074, "longitude": -0.1278}
```

### Avoid Overly Long Annotations

Keep annotations focused. If a note becomes too long, consider:
- Splitting into multiple annotations
- Uploading a separate document file
- Creating a new GPS point for related observations

## Limitations

### No Images in Markdown

Markdown image syntax (`![alt](url)`) is not supported. To include images:
- Upload an **image annotation** (separate from text)
- Link to external image URLs (will open in new tab)

### No Tables

Markdown tables are not currently supported. Alternatives:
- Use lists for simple data
- Use code blocks for tabular data
- Upload a CSV or spreadsheet file

### No HTML

Raw HTML is sanitized for security. Use standard Markdown syntax instead.

## Markdown Cheat Sheet

| Element | Syntax | Example |
|---------|--------|---------|
| Heading 1 | `# H1` | # Large Heading |
| Heading 2 | `## H2` | ## Medium Heading |
| Bold | `**text**` | **bold** |
| Italic | `*text*` | *italic* |
| Link | `[text](url)` | [Example](https://example.com) |
| Inline code | `` `code` `` | `code` |
| Code block | ` ``` code ``` ` | ```js\ncode\n``` |
| Unordered list | `- item` | • item |
| Ordered list | `1. item` | 1. item |
| Blockquote | `> quote` | > quote |
| Horizontal rule | `---` | --- |

## Additional Resources

- [Markdown Guide](https://www.markdownguide.org/) - Comprehensive Markdown reference
- [CommonMark Spec](https://commonmark.org/) - Official Markdown specification
- [Markdown Tutorial](https://www.markdowntutorial.com/) - Interactive learning tool

## Troubleshooting

### My Markdown isn't rendering

**Possible causes**:
1. **Syntax error**: Check for typos or incorrect formatting
2. **Unsupported element**: Verify the element is in the supported list above
3. **HTML blocked**: Raw HTML is sanitized for security

**Solution**: Preview your annotation before saving to verify formatting.

### Links don't work

**Possible causes**:
1. **Missing protocol**: URLs must start with `http://` or `https://`
2. **Malformed URL**: Check for typos in the link

**Example**:
- ✅ `[Example](https://example.com)` - Correct
- ❌ `[Example](example.com)` - Missing protocol
- ❌ `[Example](htp://example.com)` - Typo in protocol

### Code blocks have no syntax highlighting

**Note**: Syntax highlighting is applied via CSS classes but actual coloring depends on your browser's rendering engine. The code is still formatted and readable.

---

**Last Updated**: October 15, 2025
**Version**: 1.0
**Feature Status**: Production-ready
