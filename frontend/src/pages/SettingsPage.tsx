/**
 * Settings page component
 */

import { useEffect, useState } from 'react';
import { useBlocker } from 'react-router-dom';
import ThemeSelector from '@/components/settings/ThemeSelector';
import LanguageSelector from '@/components/settings/LanguageSelector';
import ExportSettings from '@/components/settings/ExportSettings';
import { useTheme } from '@/contexts/ThemeContext';
import { getSettings, updateSettings } from '@/api/settings';
import type { UserPreferences, ThemeMode, ExportFormat } from '@/types/settings';
import './SettingsPage.css';

export function SettingsPage() {
  const { themeMode: contextThemeMode, setThemeMode: setContextThemeMode } = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [isDirty, setIsDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [themeMode, setThemeMode] = useState<ThemeMode>(contextThemeMode);
  const [language, setLanguage] = useState<string>('en');
  const [exportFormat, setExportFormat] = useState<ExportFormat>('geojson');

  // Block navigation when there are unsaved changes
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      isDirty && currentLocation.pathname !== nextLocation.pathname
  );

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  // Sync local theme state with context when it changes
  useEffect(() => {
    setThemeMode(contextThemeMode);
  }, [contextThemeMode]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSettings();
      setPreferences(data);
      // Use theme from context (which is loaded from backend)
      setThemeMode(contextThemeMode);
      setLanguage(data.language);
      setExportFormat(data.export_format);
      setIsDirty(false);
    } catch (err) {
      setError('Failed to load settings. Please try again.');
      console.error('Error loading settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleThemeChange = async (mode: ThemeMode) => {
    setThemeMode(mode);
    setSuccessMessage(null);

    // Apply theme immediately through context (which also persists to backend)
    try {
      await setContextThemeMode(mode);
      // Theme is now persisted, so we don't mark as dirty for theme changes
      // But we still update the local state to show the current selection
    } catch (err) {
      setError('Failed to update theme. Please try again.');
      console.error('Error updating theme:', err);
    }
  };

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    setIsDirty(true);
    setSuccessMessage(null);
  };

  const handleExportFormatChange = (format: ExportFormat) => {
    setExportFormat(format);
    setIsDirty(true);
    setSuccessMessage(null);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      // Theme is already persisted via context, only update other settings
      const updated = await updateSettings({
        language,
        export_format: exportFormat,
      });
      setPreferences(updated);
      setIsDirty(false);
      setSuccessMessage('Settings saved successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to save settings. Please try again.');
      console.error('Error saving settings:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="settings-page">
        <div className="settings-loading">
          <div className="spinner" role="status" aria-label="Loading settings">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error && !preferences) {
    return (
      <div className="settings-page">
        <div className="settings-error">
          <p className="error-message">{error}</p>
          <button type="button" onClick={loadSettings} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <header className="settings-header">
        <h1>Settings</h1>
        <p className="settings-subtitle">Manage your preferences and application settings</p>
      </header>

      {successMessage && (
        <div className="success-message" role="status" aria-live="polite">
          {successMessage}
        </div>
      )}

      {error && (
        <div className="error-message" role="alert" aria-live="assertive">
          {error}
        </div>
      )}

      <form className="settings-form" data-testid="settings-form" onSubmit={(e) => e.preventDefault()}>
        <section className="settings-section">
          <h2>Appearance</h2>
          <div className="setting-group">
            <label htmlFor="theme-selector" className="setting-label">
              Theme
            </label>
            <ThemeSelector value={themeMode} onChange={handleThemeChange} />
          </div>
        </section>

        <section className="settings-section">
          <h2>Language</h2>
          <div className="setting-group">
            <label htmlFor="language-selector" className="setting-label">
              Interface Language
            </label>
            <LanguageSelector value={language} onChange={handleLanguageChange} />
          </div>
        </section>

        <section className="settings-section">
          <h2>Data Export</h2>
          <div className="setting-group">
            <label htmlFor="export-settings" className="setting-label">
              Default Export Format
            </label>
            <ExportSettings value={exportFormat} onChange={handleExportFormatChange} />
          </div>
        </section>

        <div className="settings-actions">
          <button
            type="button"
            onClick={handleSave}
            disabled={!isDirty || saving}
            className="save-button"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>

      {blocker.state === 'blocked' && (
        <div className="navigation-warning-overlay">
          <div className="navigation-warning">
            <h3>Unsaved Changes</h3>
            <p>You have unsaved changes. Are you sure you want to leave?</p>
            <div className="warning-actions">
              <button type="button" onClick={() => blocker.proceed()}>
                Leave
              </button>
              <button type="button" onClick={() => blocker.reset()}>
                Stay
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// export default SettingsPage;
