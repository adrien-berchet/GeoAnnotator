/**
 * Utility functions for point types.
 */

import type { PointType } from '../types/point';

/**
 * Get the name of a point type in the specified language with fallback logic.
 *
 * Fallback order:
 * 1. Requested language
 * 2. English ('en')
 * 3. Creation language
 * 4. First available language
 *
 * @param pointType - The point type object
 * @param languageCode - The preferred language code (default: 'en')
 * @returns The name in the best available language
 */
export function getPointTypeName(pointType: PointType, languageCode: string = 'en'): string {
  if (!pointType.names || Object.keys(pointType.names).length === 0) {
    return 'Unnamed';
  }

  // Try requested language
  if (pointType.names[languageCode]) {
    return pointType.names[languageCode];
  }

  // Fallback to English
  if (pointType.names['en']) {
    return pointType.names['en'];
  }

  // Fallback to creation language
  if (pointType.creation_language && pointType.names[pointType.creation_language]) {
    return pointType.names[pointType.creation_language];
  }

  // Fallback to first available name
  const firstLanguage = Object.keys(pointType.names)[0];
  return pointType.names[firstLanguage] || 'Unnamed';
}

/**
 * Get available language codes for a point type.
 *
 * @param pointType - The point type object
 * @returns Array of language codes
 */
export function getAvailableLanguages(pointType: PointType): string[] {
  if (!pointType.names) {
    return [];
  }
  return Object.keys(pointType.names);
}

/**
 * Check if a point type has a translation in a specific language.
 *
 * @param pointType - The point type object
 * @param languageCode - The language code to check
 * @returns True if translation exists
 */
export function hasTranslation(pointType: PointType, languageCode: string): boolean {
  return !!(pointType.names && pointType.names[languageCode]);
}

/**
 * Validate that names object has at least one entry.
 *
 * @param names - The names object to validate
 * @returns Validation error message or null if valid
 */
export function validateNames(names: Record<string, string>): string | null {
  if (!names || Object.keys(names).length === 0) {
    return 'At least one translation is required';
  }

  // Check that all values are non-empty strings
  // for (const [lang, name] of Object.entries(names)) {
  //   if (!name || name.trim() === '') {
  //     return `Translation for language '${lang}' cannot be empty`;
  //   }
  // }

  return null;
}

/**
 * Validate language code format (ISO 639-1).
 *
 * @param languageCode - The language code to validate
 * @returns True if valid
 */
export function isValidLanguageCode(languageCode: string): boolean {
  // ISO 639-1 codes are 2 lowercase letters
  return /^[a-z]{2}$/.test(languageCode);
}
