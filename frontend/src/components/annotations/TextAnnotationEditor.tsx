import { useState, useEffect } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { updateTextAnnotation } from '../../api/annotations';
import { getErrorMessage } from '../../api/client';
import type { Annotation } from '../../types/annotation';
import { useColorMode } from '../../hooks/useColorMode';
import './TextAnnotationEditor.css';

interface TextAnnotationEditorProps {
  annotation: Annotation;
  pointId: string;
  onSave: (annotation: Annotation) => void;
  onCancel: () => void;
}

export function TextAnnotationEditor({
  annotation,
  pointId,
  onSave,
  onCancel,
}: TextAnnotationEditorProps) {
  const [content, setContent] = useState(annotation.text_content || '');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const colorMode = useColorMode();

  // Apply color mode to document root for MDEditor
  useEffect(() => {
    document.documentElement.setAttribute('data-color-mode', colorMode);
  }, [colorMode]);

  const handleSave = async () => {
    if (!content.trim()) {
      setError('Text content cannot be empty');
      return;
    }

    setIsSaving(true);
    setError('');

    try {
      const updatedAnnotation = await updateTextAnnotation(pointId, annotation.id, {
        text_content: content,
      });
      onSave(updatedAnnotation);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="text-annotation-editor">
      <div className="editor-header">
        <h4>Edit Text Annotation</h4>
        <button
          type="button"
          onClick={onCancel}
          className="close-button"
          disabled={isSaving}
        >
          ✕
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="editor-content">
        <div data-color-mode={colorMode}>
          <MDEditor
            value={content}
            onChange={(val) => setContent(val || '')}
            preview="edit"
            height={300}
            visibleDragbar={false}
          />
          <div className="editor-hint">
            💡 Use Markdown for formatting (bold, italic, lists, links, etc.)
          </div>
        </div>
      </div>

      <div className="editor-actions">
        <button
          type="button"
          onClick={onCancel}
          className="btn btn-secondary"
          disabled={isSaving}
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleSave}
          className="btn btn-primary"
          disabled={isSaving}
        >
          {isSaving ? 'Saving...' : 'Save'}
        </button>
      </div>
    </div>
  );
}
