/**
 * Annotation upload component.
 *
 * Handles text notes and file uploads with progress tracking.
 */

import { useState } from 'react';
import type { FormEvent, ChangeEvent } from 'react';
import { createTextAnnotation, createFileAnnotation } from '../../api/annotations';
import { getErrorMessage } from '../../api/client';
import { ProgressBar } from '../common/ProgressBar';
import type { Annotation } from '../../types/annotation';

interface AnnotationUploadProps {
  pointId: string;
  onSuccess: (annotation: Annotation) => void;
}

type UploadMode = 'text' | 'image' | 'document' | 'file';

/**
 * Annotation upload component.
 */
export function AnnotationUpload({ pointId, onSuccess }: AnnotationUploadProps) {
  const [mode, setMode] = useState<UploadMode>('text');
  const [textContent, setTextContent] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  /**
   * Handle file selection.
   */
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];

      // Validate file size (1GB limit)
      if (file.size > 1024 * 1024 * 1024) {
        setError('File size must be less than 1GB');
        return;
      }

      setSelectedFile(file);
      setError('');
    }
  };

  /**
   * Handle text note submission.
   */
  const handleTextSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!textContent.trim()) {
      setError('Text content is required');
      return;
    }

    setIsUploading(true);

    try {
      const annotation = await createTextAnnotation(pointId, {
        text_content: textContent.trim(),
      });

      setTextContent('');
      onSuccess(annotation);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * Handle file upload.
   */
  const handleFileSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress (in real app, use axios onUploadProgress)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const annotation = await createFileAnnotation(pointId, selectedFile, mode as 'image' | 'document' | 'file');

      clearInterval(progressInterval);
      setUploadProgress(100);

      // Reset form
      setSelectedFile(null);
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }

      setTimeout(() => {
        setUploadProgress(0);
        onSuccess(annotation);
      }, 500);
    } catch (err) {
      setError(getErrorMessage(err));
      setUploadProgress(0);
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * Get accepted file types based on mode.
   */
  const getAcceptedFileTypes = (): string => {
    switch (mode) {
      case 'image':
        return 'image/*';
      case 'document':
        return '.pdf,.doc,.docx,.txt,.md';
      case 'file':
        return '*';
      default:
        return '';
    }
  };

  return (
    <div className="annotation-upload">
      <h3>Add Annotation</h3>

      {/* Mode selector */}
      <div className="mode-selector">
        <button
          type="button"
          className={`mode-button ${mode === 'text' ? 'active' : ''}`}
          onClick={() => setMode('text')}
        >
          📝 Text Note
        </button>
        <button
          type="button"
          className={`mode-button ${mode === 'image' ? 'active' : ''}`}
          onClick={() => setMode('image')}
        >
          🖼️ Image
        </button>
        <button
          type="button"
          className={`mode-button ${mode === 'document' ? 'active' : ''}`}
          onClick={() => setMode('document')}
        >
          📄 Document
        </button>
        <button
          type="button"
          className={`mode-button ${mode === 'file' ? 'active' : ''}`}
          onClick={() => setMode('file')}
        >
          📎 File
        </button>
      </div>

      {/* Error display */}
      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      {/* Text mode */}
      {mode === 'text' && (
        <form onSubmit={handleTextSubmit} className="upload-form">
          <div className="form-group">
            <label htmlFor="text-content">Text Content *</label>
            <textarea
              id="text-content"
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              placeholder="Enter your text note..."
              rows={8}
              disabled={isUploading}
              required
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isUploading || !textContent.trim()}
          >
            {isUploading ? 'Adding...' : 'Add Text Note'}
          </button>
        </form>
      )}

      {/* File mode */}
      {mode !== 'text' && (
        <form onSubmit={handleFileSubmit} className="upload-form">
          <div className="form-group">
            <label htmlFor="file-input">
              Select {mode === 'image' ? 'Image' : mode === 'document' ? 'Document' : 'File'} *
            </label>
            <input
              id="file-input"
              type="file"
              accept={getAcceptedFileTypes()}
              onChange={handleFileChange}
              disabled={isUploading}
              required
            />
            {selectedFile && (
              <div className="selected-file-info">
                <span className="file-name">{selectedFile.name}</span>
                <span className="file-size">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </span>
              </div>
            )}
          </div>

          {uploadProgress > 0 && (
            <ProgressBar
              progress={uploadProgress}
              label="Uploading..."
              showPercentage
            />
          )}

          <button
            type="submit"
            className="btn-primary"
            disabled={isUploading || !selectedFile}
          >
            {isUploading ? 'Uploading...' : `Upload ${mode === 'image' ? 'Image' : mode === 'document' ? 'Document' : 'File'}`}
          </button>
        </form>
      )}
    </div>
  );
}
