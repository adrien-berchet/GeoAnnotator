/**
 * Security tests for AnnotationList component
 *
 * Tests verify that markdown rendering properly sanitizes malicious content
 * to prevent XSS attacks and other security vulnerabilities.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AnnotationList } from '../../../components/annotations/AnnotationList';
import type { Annotation } from '../../../types/annotation';
import * as annotationsApi from '../../../api/annotations';

// Mock the annotations API
vi.mock('../../../api/annotations', () => ({
  getAnnotations: vi.fn(),
  downloadAnnotation: vi.fn(),
  deleteAnnotation: vi.fn(),
}));

// Mock the useColorMode hook
vi.mock('../../../hooks/useColorMode', () => ({
  useColorMode: () => 'light',
}));

describe('AnnotationList - Security (XSS Prevention)', () => {
  const mockPointId = 'test-point-security';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * T009: Security tests for XSS prevention
   */
  describe('XSS Attack Prevention', () => {
    it('should sanitize script tags', async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: 'sec-1',
          gps_point_id: mockPointId,
          type: 'text',
          text_content: '<script>alert("XSS Attack!")</script>',
          file: null,
          order: 1,
          created_at: '2025-10-15T10:00:00Z',
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(mockAnnotations);

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // Script tag should NOT be present in the DOM
        const scriptTags = document.querySelectorAll('script');
        const maliciousScripts = Array.from(scriptTags).filter(
          script => script.textContent?.includes('XSS Attack')
        );
        expect(maliciousScripts).toHaveLength(0);
      });
    });

    it('should sanitize img tags with onerror handlers', async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: 'sec-2',
          gps_point_id: mockPointId,
          type: 'text',
          text_content: '<img src="invalid" onerror="alert(\'XSS via Image\')">',
          file: null,
          order: 1,
          created_at: '2025-10-15T10:00:00Z',
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(mockAnnotations);

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // Image tags with onerror should be sanitized
        const images = document.querySelectorAll('img');
        images.forEach(img => {
          expect(img.getAttribute('onerror')).toBeNull();
        });
      });
    });

    it('should sanitize javascript: protocol in links', async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: 'sec-3',
          gps_point_id: mockPointId,
          type: 'text',
          text_content: '[Click me](javascript:alert("XSS"))',
          file: null,
          order: 1,
          created_at: '2025-10-15T10:00:00Z',
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(mockAnnotations);

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // Link should not have javascript: protocol
        const links = screen.queryAllByRole('link');
        links.forEach(link => {
          const href = link.getAttribute('href');
          expect(href).not.toMatch(/javascript:/i);
        });
      });
    });

    it('should sanitize inline event handlers', async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: 'sec-4',
          gps_point_id: mockPointId,
          type: 'text',
          text_content: '<div onclick="alert(\'XSS\')">Click me</div>',
          file: null,
          order: 1,
          created_at: '2025-10-15T10:00:00Z',
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(mockAnnotations);

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // Should not have onclick handlers
        const elements = document.querySelectorAll('[onclick]');
        expect(elements).toHaveLength(0);
      });
    });

    it('should sanitize data URIs with scripts', async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: 'sec-5',
          gps_point_id: mockPointId,
          type: 'text',
          text_content: '<a href="data:text/html,<script>alert(\'XSS\')</script>">Click</a>',
          file: null,
          order: 1,
          created_at: '2025-10-15T10:00:00Z',
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(mockAnnotations);

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // Malicious data URIs should be sanitized
        const links = screen.queryAllByRole('link');
        links.forEach(link => {
          const href = link.getAttribute('href');
          if (href?.startsWith('data:')) {
            expect(href).not.toContain('script');
          }
        });
      });
    });

    it('should handle multiple XSS attempts in mixed content', async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: 'sec-6',
          gps_point_id: mockPointId,
          type: 'text',
          text_content: `
# Normal Heading
<script>alert('XSS 1')</script>

**Bold text** with <img src=x onerror="alert('XSS 2')">

[Safe link](https://example.com) and [Bad link](javascript:alert('XSS 3'))
          `,
          file: null,
          order: 1,
          created_at: '2025-10-15T10:00:00Z',
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(mockAnnotations);

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // No script execution in the annotation description
        const annotationDesc = document.querySelector('.annotation-description');
        expect(annotationDesc).toBeInTheDocument();

        const scriptTags = annotationDesc?.querySelectorAll('script');
        expect(scriptTags?.length || 0).toBe(0);

        // No inline event handlers
        expect(annotationDesc?.querySelectorAll('[onerror]').length || 0).toBe(0);
        expect(annotationDesc?.querySelectorAll('[onclick]').length || 0).toBe(0);

        // Safe content should still render
        expect(screen.getByRole('heading', { name: 'Normal Heading' })).toBeInTheDocument();
        expect(screen.getByText('Bold text', { selector: 'strong' })).toBeInTheDocument();
      });
    });

    it('should preserve safe HTML entities', async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: 'sec-7',
          gps_point_id: mockPointId,
          type: 'text',
          text_content: 'Use &lt;div&gt; tags in HTML',
          file: null,
          order: 1,
          created_at: '2025-10-15T10:00:00Z',
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(mockAnnotations);

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // HTML entities should be decoded and displayed correctly
        const text = screen.getByText(/<div>/);
        expect(text).toBeInTheDocument();
      });
    });
  });

  /**
   * Additional security edge cases
   */
  describe('Security Edge Cases', () => {
    it('should handle extremely long malicious input', async () => {
      const longMaliciousContent = '<script>' + 'alert("XSS");'.repeat(1000) + '</script>';

      const mockAnnotations: Annotation[] = [
        {
          id: 'sec-8',
          gps_point_id: mockPointId,
          type: 'text',
          text_content: longMaliciousContent,
          file: null,
          order: 1,
          created_at: '2025-10-15T10:00:00Z',
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(mockAnnotations);

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // Should render without crashing and without executing scripts
        const scriptTags = Array.from(document.querySelectorAll('script')).filter(
          s => s.textContent?.includes('XSS')
        );
        expect(scriptTags).toHaveLength(0);
      });
    });

    it('should sanitize nested malicious tags', async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: 'sec-9',
          gps_point_id: mockPointId,
          type: 'text',
          text_content: '<div><script><script>alert("Nested XSS")</script></script></div>',
          file: null,
          order: 1,
          created_at: '2025-10-15T10:00:00Z',
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(mockAnnotations);

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        const scriptTags = Array.from(document.querySelectorAll('script')).filter(
          s => s.textContent?.includes('Nested XSS')
        );
        expect(scriptTags).toHaveLength(0);
      });
    });
  });
});
