/**
 * Logger utility for frontend application.
 *
 * Provides environment-aware logging that:
 * - Suppresses debug/info logs in production
 * - Always shows warnings and errors
 * - Sends errors to Sentry in production
 */

import * as Sentry from "@sentry/react";

const isDevelopment = import.meta.env.MODE === "development";

/**
 * Logger interface with environment-aware methods.
 *
 * Usage:
 *   logger.debug('Debug info', data);  // Only in development
 *   logger.info('Something happened'); // Only in development
 *   logger.warn('Warning message');    // Always shown
 *   logger.error('Error occurred', error); // Always shown + can send to monitoring
 */
export const logger = {
  /**
   * Debug logging - only in development.
   * Use for detailed debugging information.
   */
  debug: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.debug("[DEBUG]", ...args);
    }
  },

  /**
   * Info logging - only in development.
   * Use for general informational messages.
   */
  info: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.log("[INFO]", ...args);
    }
  },

  /**
   * Warning logging - always shown.
   * Use for recoverable issues that should be investigated.
   */
  warn: (...args: unknown[]): void => {
    console.warn("[WARN]", ...args);
  },

  /**
   * Error logging - always shown.
   * Use for errors that impact functionality.
   *
   * In production, errors are sent to Sentry for tracking and analysis.
   */
  error: (...args: unknown[]): void => {
    console.error("[ERROR]", ...args);

    // Send to Sentry in production
    if (!isDevelopment) {
      const [firstArg, ...rest] = args;

      // If first argument is an Error object, capture it
      if (firstArg instanceof Error) {
        Sentry.captureException(firstArg, {
          extra: rest.length > 0 ? { additional: rest } : undefined,
        });
      } else {
        // Otherwise, capture as a message with context
        Sentry.captureMessage(String(firstArg), {
          level: "error",
          extra: { args: rest },
        });
      }
    }
  },

  /**
   * Log an API request (development only).
   */
  apiRequest: (method: string, url: string, data?: unknown): void => {
    if (isDevelopment) {
      console.log(`[API ${method}]`, url, data || "");
    }
  },

  /**
   * Log an API response (development only).
   */
  apiResponse: (method: string, url: string, status: number, data?: unknown): void => {
    if (isDevelopment) {
      console.log(`[API ${method}] ${status}`, url, data || "");
    }
  },
};

/**
 * Create a namespaced logger for a specific component or module.
 *
 * Usage:
 *   const log = createLogger('MapPage');
 *   log.info('Map initialized'); // Output: [INFO] [MapPage] Map initialized
 */
export function createLogger(namespace: string) {
  return {
    debug: (...args: unknown[]) => logger.debug(`[${namespace}]`, ...args),
    info: (...args: unknown[]) => logger.info(`[${namespace}]`, ...args),
    warn: (...args: unknown[]) => logger.warn(`[${namespace}]`, ...args),
    error: (...args: unknown[]) => logger.error(`[${namespace}]`, ...args),
  };
}
