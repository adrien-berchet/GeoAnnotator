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
import { useLanguage } from '../../contexts/LanguageContext';
import './AnnotationForm.css';

interface AnnotationFormProps {
  pointId: string | undefined;
  onAnnotationCreated: (annotation: Annotation) => void;
  onCancel?: () => void;
}

type AnnotationType = 'text' | 'image' | 'document' | 'file';

export function AnnotationForm({ pointId, onAnnotationCreated, onCancel }: AnnotationFormProps) {
  const { t } = useLanguage();
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
      setError(t('annotations.pointIdMissing', 'Point ID is missing'));
      setIsSubmitting(false);
      return;
    }

    try {
      let annotation: Annotation;

      if (annotationType === 'text') {
        if (!textContent.trim()) {
          setError(t('annotations.pleaseEnterText', 'Please enter some text'));
          setIsSubmitting(false);
          return;
        }

        annotation = await createTextAnnotation(pointId, {
          text_content: textContent,
        });
      } else {
        if (!selectedFile) {
          setError(t('annotations.pleaseSelectFile', 'Please select a file'));
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
        <h3>{t('annotations.addAnnotation', 'Add Annotation')}</h3>
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
            📝 {t('annotations.text', 'Text')}
          </button>
          <button
            type="button"
            className={`type-button ${annotationType === 'image' ? 'active' : ''}`}
            onClick={() => setAnnotationType('image')}
          >
            🖼️ {t('annotations.image', 'Image')}
          </button>
          <button
            type="button"
            className={`type-button ${annotationType === 'document' ? 'active' : ''}`}
            onClick={() => setAnnotationType('document')}
          >
            📄 {t('annotations.document', 'Document')}
          </button>
          <button
            type="button"
            className={`type-button ${annotationType === 'file' ? 'active' : ''}`}
            onClick={() => setAnnotationType('file')}
          >
            📎 {t('annotations.file', 'File')}
          </button>
        </div>

        {/* Text Input */}
        {annotationType === 'text' && (
          <div className="form-group">
            <div data-color-mode={colorMode}>
              <MDEditor
                value={textContent}
                onChange={(val) => setTextContent(val || '')}
                preview="edit"
                height={300}
                visibleDragbar={false}
              />
              <div className="input-hint">
                💡 {t('annotations.markdownHint', 'Use Markdown for formatting (bold, italic, lists, links, etc.)')}
              </div>
            </div>
          </div>
        )}

        {/* File Input */}
        {annotationType !== 'text' && (
          <div className="form-group">
            <label htmlFor="file-input">
              {annotationType === 'image' && t('annotations.selectImage', 'Select Image')}
              {annotationType === 'document' && t('annotations.selectDocument', 'Select Document')}
              {annotationType === 'file' && t('annotations.selectFile', 'Select File')}
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
              {annotationType === 'image' && t('annotations.maxSizeImage', 'Max size: 1GB (JPG, PNG, GIF, etc.)')}
              {annotationType === 'document' && t('annotations.maxSizeDocument', 'Max size: 1GB (PDF, DOC, TXT, etc.)')}
              {annotationType === 'file' && t('annotations.maxSizeFile', 'Max size: 1GB (Any file type)')}
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
              {t('common.cancel', 'Cancel')}
            </button>
          )}
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? t('annotations.adding', 'Adding...') : t('annotations.addAnnotation', 'Add Annotation')}
          </button>
        </div>
      </form>
    </div>
  );
}
