/**
 * Annotation form component.
 *
 * Allows adding different types of annotations: text, image, document, or file.
 */

import { useState, useEffect } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { createTextAnnotation, createFileAnnotation } from '../../api/annotations';
import { getErrorMessage } from '../../api/client';
import type { Annotation } from '../../types/annotation';
import { useColorMode } from '../../hooks/useColorMode';
import './AnnotationForm.css';

interface AnnotationFormProps {
  pointId: string | undefined;
  onAnnotationCreated: (annotation: Annotation) => void;
  onCancel?: () => void;
}

type AnnotationType = 'text' | 'image' | 'document' | 'file';

export function AnnotationForm({ pointId, onAnnotationCreated, onCancel }: AnnotationFormProps) {
  const colorMode = useColorMode();
  const [annotationType, setAnnotationType] = useState<AnnotationType>('text');
  const [textContent, setTextContent] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Apply color mode to document root for MDEditor
  useEffect(() => {
    document.documentElement.setAttribute('data-color-mode', colorMode);
  }, [colorMode]);  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    if (!pointId) {
      setError('Point ID is missing');
      setIsSubmitting(false);
      return;
    }

    try {
      let annotation: Annotation;

      if (annotationType === 'text') {
        if (!textContent.trim()) {
          setError('Please enter some text');
          setIsSubmitting(false);
          return;
        }

        annotation = await createTextAnnotation(pointId, {
          text_content: textContent,
        });
      } else {
        if (!selectedFile) {
          setError('Please select a file');
          setIsSubmitting(false);
          return;
        }

        annotation = await createFileAnnotation(pointId, selectedFile, annotationType);
      }

      onAnnotationCreated(annotation);

      // Reset form
      setTextContent('');
      setSelectedFile(null);
      setAnnotationType('text');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="annotation-form">
      <div className="annotation-form-header">
        <h3>Add Annotation</h3>
        {onCancel && (
          <button type="button" onClick={onCancel} className="close-button">
            ✕
          </button>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit}>
        {/* Annotation Type Selector */}
        <div className="annotation-type-selector">
          <button
            type="button"
            className={`type-button ${annotationType === 'text' ? 'active' : ''}`}
            onClick={() => setAnnotationType('text')}
          >
            📝 Text
          </button>
          <button
            type="button"
            className={`type-button ${annotationType === 'image' ? 'active' : ''}`}
            onClick={() => setAnnotationType('image')}
          >
            🖼️ Image
          </button>
          <button
            type="button"
            className={`type-button ${annotationType === 'document' ? 'active' : ''}`}
            onClick={() => setAnnotationType('document')}
          >
            📄 Document
          </button>
          <button
            type="button"
            className={`type-button ${annotationType === 'file' ? 'active' : ''}`}
            onClick={() => setAnnotationType('file')}
          >
            📎 File
          </button>
        </div>

        {/* Text Input */}
        {annotationType === 'text' && (
          <div className="form-group">
            <label htmlFor="text-content">Text Content</label>
            <div data-color-mode={colorMode}>
              <MDEditor
                value={textContent}
                onChange={(val) => setTextContent(val || '')}
                preview="edit"
                height={300}
                visibleDragbar={false}
              />
            </div>
            <div className="input-hint">
              💡 Use Markdown for formatting (bold, italic, lists, links, etc.)
            </div>
          </div>
        )}

        {/* File Input */}
        {annotationType !== 'text' && (
          <div className="form-group">
            <label htmlFor="file-input">
              {annotationType === 'image' && 'Select Image'}
              {annotationType === 'document' && 'Select Document'}
              {annotationType === 'file' && 'Select File'}
            </label>
            <input
              id="file-input"
              type="file"
              onChange={handleFileChange}
              accept={
                annotationType === 'image'
                  ? 'image/*'
                  : annotationType === 'document'
                  ? '.pdf,.doc,.docx,.txt'
                  : undefined
              }
              disabled={isSubmitting}
              className="file-input"
            />
            {selectedFile && (
              <div className="selected-file">
                <span className="file-icon">
                  {annotationType === 'image' && '🖼️'}
                  {annotationType === 'document' && '📄'}
                  {annotationType === 'file' && '📎'}
                </span>
                <span className="file-name">{selectedFile.name}</span>
                <span className="file-size">
                  ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </span>
              </div>
            )}
            <div className="input-hint">
              {annotationType === 'image' && 'Max size: 1GB (JPG, PNG, GIF, etc.)'}
              {annotationType === 'document' && 'Max size: 1GB (PDF, DOC, TXT, etc.)'}
              {annotationType === 'file' && 'Max size: 1GB (Any file type)'}
            </div>
          </div>
        )}

        {/* Submit Buttons */}
        <div className="form-actions">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="btn btn-secondary"
              disabled={isSubmitting}
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Adding...' : 'Add Annotation'}
          </button>
        </div>
      </form>
    </div>
  );
}
