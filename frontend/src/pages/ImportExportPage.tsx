/**
 * Import/Export page component.
 *
 * Allows users to import and export GPS points with annotations
 * in multiple formats: GeoJSON, GPX, KML, CSV, and ZIP.
 */

import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { exportPoints, importPoints, type ExportFormat, type ImportFormat, type MergeStrategy, type ImportResult } from '../api/export';
import { getPoints } from '../api/points';
import type { GPSPoint } from '../types/point';
import './ImportExportPage.css';

export function ImportExportPage() {
  const { t } = useLanguage();

  // Export state
  const [exportFormat, setExportFormat] = useState<ExportFormat>('geojson');
  const [includeAnnotations, setIncludeAnnotations] = useState(true);
  const [selectedPoints, setSelectedPoints] = useState<string[]>([]);
  const [exportAll, setExportAll] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [points, setPoints] = useState<GPSPoint[]>([]);

  // Import state
  const [importFormat, setImportFormat] = useState<ImportFormat>('geojson');
  const [mergeStrategy, setMergeStrategy] = useState<MergeStrategy>('create_new');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load points for selection
  useEffect(() => {
    loadPoints();
  }, []);

  const loadPoints = async () => {
    try {
      const data = await getPoints();
      setPoints(data.results || []);
    } catch (err) {
      console.error('Failed to load points:', err);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const data = {
        format: exportFormat,
        point_ids: exportAll ? undefined : selectedPoints,
        include_annotations: includeAnnotations && (exportFormat === 'geojson' || exportFormat === 'zip'),
      };

      const blob = await exportPoints(data);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Set filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const extension = exportFormat === 'geojson' ? 'geojson' : exportFormat;
      link.download = `geoannotator_export_${timestamp}.${extension}`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      alert(t('importExport.exportError', 'Failed to export points. Please try again.'));
    } finally {
      setIsExporting(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setImportResult(null);
      setImportError(null);

      // Auto-detect format from file extension
      const extension = file.name.split('.').pop()?.toLowerCase();
      if (extension === 'geojson' || extension === 'json') {
        setImportFormat('geojson');
      } else if (extension === 'gpx') {
        setImportFormat('gpx');
      } else if (extension === 'csv') {
        setImportFormat('csv');
      } else if (extension === 'kml') {
        setImportFormat('kml');
      } else if (extension === 'zip') {
        setImportFormat('zip');
      }
    }
  };

  const handleImport = async () => {
    if (!selectedFile) {
      alert(t('importExport.selectFile', 'Please select a file to import.'));
      return;
    }

    setIsImporting(true);
    setImportResult(null);
    setImportError(null);

    try {
      const result = await importPoints(selectedFile, importFormat, mergeStrategy);
      setImportResult(result);

      // Reload points after successful import
      if (result.imported_points > 0) {
        await loadPoints();
      }
    } catch (err: any) {
      console.error('Import failed:', err);
      setImportError(err.response?.data?.error || t('importExport.importError', 'Failed to import points. Please check the file format.'));
    } finally {
      setIsImporting(false);
    }
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setImportResult(null);
    setImportError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const togglePointSelection = (pointId: string) => {
    setSelectedPoints(prev =>
      prev.includes(pointId)
        ? prev.filter(id => id !== pointId)
        : [...prev, pointId]
    );
  };

  const selectAllPoints = () => {
    setSelectedPoints(points.map(p => p.id));
  };

  const deselectAllPoints = () => {
    setSelectedPoints([]);
  };

  return (
    <div className="import-export-page">
      <div className="page-header">
        <h1>💾 {t('importExport.title', 'Import & Export')}</h1>
        <p className="page-description">
          {t('importExport.description', 'Export your points and annotations to various formats, or import data from existing files.')}
        </p>
      </div>

      <div className="import-export-container">
        {/* Export Section */}
        <section className="export-section">
          <h2>📤 {t('importExport.export', 'Export')}</h2>

          <div className="form-group">
            <label htmlFor="export-format">
              {t('importExport.exportFormat', 'Export Format')}
            </label>
            <select
              id="export-format"
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
              className="form-select"
            >
              <option value="geojson">GeoJSON (Standard geographic format)</option>
              <option value="gpx">GPX (GPS Exchange Format)</option>
              <option value="kml">KML (Google Earth format)</option>
              <option value="csv">CSV (Spreadsheet format)</option>
              <option value="zip">ZIP (GeoJSON + Annotations)</option>
            </select>
          </div>

          {(exportFormat === 'geojson' || exportFormat === 'zip') && (
            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={includeAnnotations}
                  onChange={(e) => setIncludeAnnotations(e.target.checked)}
                />
                <span>{t('importExport.includeAnnotations', 'Include annotations')}</span>
              </label>
              <p className="field-hint">
                {exportFormat === 'zip'
                  ? t('importExport.zipHint', 'ZIP format includes annotation files in a separate folder')
                  : t('importExport.annotationsHint', 'Include annotation metadata in the export')
                }
              </p>
            </div>
          )}

          <div className="form-group">
            <label>
              {t('importExport.selectPoints', 'Points to Export')}
            </label>
            <div className="radio-group">
              <label>
                <input
                  type="radio"
                  checked={exportAll}
                  onChange={() => setExportAll(true)}
                />
                <span>{t('importExport.exportAll', 'Export all points')} ({points.length})</span>
              </label>
              <label>
                <input
                  type="radio"
                  checked={!exportAll}
                  onChange={() => setExportAll(false)}
                />
                <span>{t('importExport.exportSelected', 'Export selected points')} ({selectedPoints.length})</span>
              </label>
            </div>
          </div>

          {!exportAll && (
            <div className="points-selection">
              <div className="selection-actions">
                <button onClick={selectAllPoints} className="btn btn-secondary btn-sm">
                  {t('importExport.selectAll', 'Select All')}
                </button>
                <button onClick={deselectAllPoints} className="btn btn-secondary btn-sm">
                  {t('importExport.deselectAll', 'Deselect All')}
                </button>
              </div>
              <div className="points-list">
                {points.map(point => (
                  <label key={point.id} className="point-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedPoints.includes(point.id)}
                      onChange={() => togglePointSelection(point.id)}
                    />
                    <span className="point-info">
                      <span className="point-title">{point.title}</span>
                      <span className="point-meta">
                        {point.latitude.toFixed(6)}, {point.longitude.toFixed(6)}
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={handleExport}
            disabled={isExporting || (!exportAll && selectedPoints.length === 0)}
            className="btn btn-primary btn-large"
          >
            {isExporting ? (
              <>⏳ {t('importExport.exporting', 'Exporting...')}</>
            ) : (
              <>📥 {t('importExport.exportButton', 'Export Points')}</>
            )}
          </button>
        </section>

        {/* Import Section */}
        <section className="import-section">
          <h2>📥 {t('importExport.import', 'Import')}</h2>

          <div className="form-group">
            <label htmlFor="import-format">
              {t('importExport.importFormat', 'Import Format')}
            </label>
            <select
              id="import-format"
              value={importFormat}
              onChange={(e) => setImportFormat(e.target.value as ImportFormat)}
              className="form-select"
            >
              <option value="geojson">GeoJSON</option>
              <option value="gpx">GPX</option>
              <option value="kml">KML</option>
              <option value="csv">CSV</option>
              <option value="zip">ZIP (with annotations)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="merge-strategy">
              {t('importExport.mergeStrategy', 'Merge Strategy')}
            </label>
            <select
              id="merge-strategy"
              value={mergeStrategy}
              onChange={(e) => setMergeStrategy(e.target.value as MergeStrategy)}
              className="form-select"
            >
              <option value="create_new">
                {t('importExport.createNew', 'Create new (allow duplicates)')}
              </option>
              <option value="skip">
                {t('importExport.skip', 'Skip duplicates (within 1 meter)')}
              </option>
              <option value="replace">
                {t('importExport.replace', 'Replace existing (within 1 meter)')}
              </option>
            </select>
            <p className="field-hint">
              {mergeStrategy === 'create_new' && t('importExport.createNewHint', 'All points will be imported as new, even if similar points exist')}
              {mergeStrategy === 'skip' && t('importExport.skipHint', 'Points within 1 meter of existing points will be skipped')}
              {mergeStrategy === 'replace' && t('importExport.replaceHint', 'Existing points within 1 meter will be updated with new data')}
            </p>
          </div>

          <div className="form-group">
            <label>
              {t('importExport.selectFileLabel', 'Select File')}
            </label>
            <div className="file-input-wrapper">
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileSelect}
                accept=".geojson,.json,.gpx,.kml,.csv,.zip"
                className="file-input"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="file-input-label">
                📁 {t('importExport.chooseFile', 'Choose File')}
              </label>
              {selectedFile && (
                <div className="selected-file">
                  <span className="file-name">{selectedFile.name}</span>
                  <span className="file-size">
                    ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </span>
                  <button onClick={handleClearFile} className="btn-clear-file">
                    ✕
                  </button>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={handleImport}
            disabled={isImporting || !selectedFile}
            className="btn btn-primary btn-large"
          >
            {isImporting ? (
              <>⏳ {t('importExport.importing', 'Importing...')}</>
            ) : (
              <>📤 {t('importExport.importButton', 'Import Points')}</>
            )}
          </button>

          {/* Import Results */}
          {importResult && (
            <div className="import-result success">
              <h3>✅ {t('importExport.importSuccess', 'Import Complete')}</h3>
              <div className="result-stats">
                <div className="stat">
                  <span className="stat-label">{t('importExport.totalPoints', 'Total Points')}:</span>
                  <span className="stat-value">{importResult.total_points}</span>
                </div>
                <div className="stat success">
                  <span className="stat-label">{t('importExport.imported', 'Imported')}:</span>
                  <span className="stat-value">{importResult.imported_points}</span>
                </div>
                {importResult.skipped_points > 0 && (
                  <div className="stat warning">
                    <span className="stat-label">{t('importExport.skipped', 'Skipped')}:</span>
                    <span className="stat-value">{importResult.skipped_points}</span>
                  </div>
                )}
                {importResult.failed_points > 0 && (
                  <div className="stat error">
                    <span className="stat-label">{t('importExport.failed', 'Failed')}:</span>
                    <span className="stat-value">{importResult.failed_points}</span>
                  </div>
                )}
              </div>

              {importResult.errors.length > 0 && (
                <div className="import-errors">
                  <h4>{t('importExport.errors', 'Errors')}:</h4>
                  <ul>
                    {importResult.errors.slice(0, 10).map((error, idx) => (
                      <li key={idx}>
                        <strong>{t('importExport.line', 'Line')} {error.line_number}:</strong> {error.message}
                      </li>
                    ))}
                    {importResult.errors.length > 10 && (
                      <li>...{t('importExport.moreErrors', 'and {count} more errors').replace('{count}', String(importResult.errors.length - 10))}</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}

          {importError && (
            <div className="import-result error">
              <h3>❌ {t('importExport.importFailed', 'Import Failed')}</h3>
              <p>{importError}</p>
            </div>
          )}
        </section>
      </div>

      {/* Help Section */}
      <section className="help-section">
        <h2>ℹ️ {t('importExport.help', 'Format Information')}</h2>
        <div className="format-info-grid">
          <div className="format-info">
            <h3>GeoJSON</h3>
            <p>{t('importExport.geojsonInfo', 'Standard geographic data format. Supports all point data and annotation metadata.')}</p>
          </div>
          <div className="format-info">
            <h3>GPX</h3>
            <p>{t('importExport.gpxInfo', 'GPS Exchange Format. Compatible with most GPS devices and mapping software.')}</p>
          </div>
          <div className="format-info">
            <h3>KML</h3>
            <p>{t('importExport.kmlInfo', 'Google Earth format. Great for visualization in Google Earth and Google Maps.')}</p>
          </div>
          <div className="format-info">
            <h3>CSV</h3>
            <p>{t('importExport.csvInfo', 'Spreadsheet format. Easy to edit in Excel or Google Sheets.')}</p>
          </div>
          <div className="format-info">
            <h3>ZIP</h3>
            <p>{t('importExport.zipInfo', 'Archive containing GeoJSON and all annotation files (images, documents, etc.).')}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
