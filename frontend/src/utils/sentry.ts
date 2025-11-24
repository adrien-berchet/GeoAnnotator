/**
 * Sentry initialization for frontend error tracking and performance monitoring.
 *
 * Configure Sentry DSN and environment via environment variables:
 * - VITE_SENTRY_DSN: Your Sentry DSN (required for Sentry to work)
 * - VITE_SENTRY_ENVIRONMENT: Environment name (development, staging, production)
 * - VITE_SENTRY_TRACES_SAMPLE_RATE: Percentage of transactions to capture (0.0-1.0)
 */

import * as Sentry from "@sentry/react";

/**
 * Initialize Sentry for error tracking.
 *
 * This should be called once at application startup, before React renders.
 */
export function initSentry() {
  const sentryDsn = import.meta.env.VITE_SENTRY_DSN;
  const environment = import.meta.env.VITE_SENTRY_ENVIRONMENT || import.meta.env.MODE || "development";
  const tracesSampleRate = parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || "0.1");

  // Only initialize Sentry if DSN is configured
  if (!sentryDsn) {
    console.info("Sentry DSN not configured - error tracking disabled");
    return;
  }

  Sentry.init({
    dsn: sentryDsn,
    environment,
    integrations: [
      // Capture browser performance metrics
      Sentry.browserTracingIntegration(),
      // Capture user interactions (clicks, navigation)
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],

    // Set tracesSampleRate to 1.0 to capture 100% of transactions for performance monitoring.
    // We recommend adjusting this value in production (e.g., 0.1 = 10%)
    tracesSampleRate,

    // Capture Replay for 10% of all sessions,
    // plus 100% of sessions with an error
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,

    // Don't send personally identifiable information
    beforeSend(event) {
      // Filter out sensitive data
      if (event.request) {
        // Remove authorization headers
        if (event.request.headers) {
          delete event.request.headers.Authorization;
          delete event.request.headers.authorization;
        }
      }

      return event;
    },
  });

  console.info(`Sentry initialized for environment: ${environment}`);
}
