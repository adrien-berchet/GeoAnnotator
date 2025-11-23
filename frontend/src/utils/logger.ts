/**
 * Logger utility for frontend application.
 *
 * Provides environment-aware logging that:
 * - Suppresses debug/info logs in production
 * - Always shows warnings and errors
 * - Can be extended to send errors to monitoring services (e.g., Sentry)
 */

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
   * In production, this could send to error tracking service:
   * - Sentry
   * - DataDog
   * - LogRocket
   */
  error: (...args: unknown[]): void => {
    console.error("[ERROR]", ...args);

    // TODO: Send to error tracking service in production
    // if (!isDevelopment && window.Sentry) {
    //   window.Sentry.captureException(args[0]);
    // }
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
