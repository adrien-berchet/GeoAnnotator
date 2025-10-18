/**
 * Unit tests for BlueDot component.
 *
 * Tests rendering, positioning, and click behavior of the device position marker.
 */

import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { BlueDot } from '../BlueDot';
import type { DevicePosition } from '../../../hooks/useDevicePosition';

// Mock react-leaflet components
vi.mock('react-leaflet', () => ({
  Marker: ({ children, eventHandlers, position }: any) => (
    <div
      data-testid="marker"
      data-position={JSON.stringify(position)}
      onClick={() => eventHandlers?.click && eventHandlers.click()}
    >
      {children}
    </div>
  ),
  Circle: ({ center, radius }: any) => (
    <div
      data-testid="circle"
      data-center={JSON.stringify(center)}
      data-radius={radius}
    />
  ),
}));

describe('BlueDot', () => {
  const mockPosition: DevicePosition = {
    latitude: 48.8566,
    longitude: 2.3522,
    accuracy: 10,
    timestamp: Date.now(),
  };

  const mockOnClick = vi.fn();

  describe('Rendering', () => {
    it('should render marker and accuracy circle', () => {
      const { getByTestId } = render(
        <BlueDot position={mockPosition} onClick={mockOnClick} />
      );

      expect(getByTestId('marker')).toBeInTheDocument();
      expect(getByTestId('circle')).toBeInTheDocument();
    });

    it('should position marker at correct coordinates', () => {
      const { getByTestId } = render(
        <BlueDot position={mockPosition} onClick={mockOnClick} />
      );

      const marker = getByTestId('marker');
      const positionData = JSON.parse(marker.getAttribute('data-position') || '[]');

      expect(positionData[0]).toBe(48.8566);
      expect(positionData[1]).toBe(2.3522);
    });

    it('should render accuracy circle with correct radius', () => {
      const { getByTestId } = render(
        <BlueDot position={mockPosition} onClick={mockOnClick} />
      );

      const circle = getByTestId('circle');

      expect(circle.getAttribute('data-radius')).toBe('10');
    });

    it('should center accuracy circle at marker position', () => {
      const { getByTestId } = render(
        <BlueDot position={mockPosition} onClick={mockOnClick} />
      );

      const circle = getByTestId('circle');
      const centerData = JSON.parse(circle.getAttribute('data-center') || '[]');

      expect(centerData[0]).toBe(48.8566);
      expect(centerData[1]).toBe(2.3522);
    });
  });

  describe('Click Behavior', () => {
    it('should call onClick when marker is clicked', () => {
      const onClick = vi.fn();
      const { getByTestId } = render(
        <BlueDot position={mockPosition} onClick={onClick} />
      );

      const marker = getByTestId('marker');
      marker.click();

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('should not call onClick when circle is clicked', () => {
      const onClick = vi.fn();
      const { getByTestId } = render(
        <BlueDot position={mockPosition} onClick={onClick} />
      );

      const circle = getByTestId('circle');
      circle.click();

      // Circle doesn't have click handler, only marker does
      expect(onClick).not.toHaveBeenCalled();
    });
  });

  describe('Position Updates', () => {
    it('should update marker position when position prop changes', () => {
      const { getByTestId, rerender } = render(
        <BlueDot position={mockPosition} onClick={mockOnClick} />
      );

      const newPosition: DevicePosition = {
        latitude: 48.8584,
        longitude: 2.2945,
        accuracy: 15,
        timestamp: Date.now(),
      };

      rerender(<BlueDot position={newPosition} onClick={mockOnClick} />);

      const marker = getByTestId('marker');
      const positionData = JSON.parse(marker.getAttribute('data-position') || '[]');

      expect(positionData[0]).toBe(48.8584);
      expect(positionData[1]).toBe(2.2945);
    });

    it('should update accuracy circle when position changes', () => {
      const { getByTestId, rerender } = render(
        <BlueDot position={mockPosition} onClick={mockOnClick} />
      );

      const newPosition: DevicePosition = {
        ...mockPosition,
        accuracy: 25,
      };

      rerender(<BlueDot position={newPosition} onClick={mockOnClick} />);

      const circle = getByTestId('circle');

      expect(circle.getAttribute('data-radius')).toBe('25');
    });
  });

  describe('Edge Cases', () => {
    it('should handle very high accuracy values', () => {
      const highAccuracyPosition: DevicePosition = {
        latitude: 48.8566,
        longitude: 2.3522,
        accuracy: 1000,
        timestamp: Date.now(),
      };

      const { getByTestId } = render(
        <BlueDot position={highAccuracyPosition} onClick={mockOnClick} />
      );

      const circle = getByTestId('circle');

      expect(circle.getAttribute('data-radius')).toBe('1000');
    });

    it('should handle very low accuracy values', () => {
      const lowAccuracyPosition: DevicePosition = {
        latitude: 48.8566,
        longitude: 2.3522,
        accuracy: 1,
        timestamp: Date.now(),
      };

      const { getByTestId } = render(
        <BlueDot position={lowAccuracyPosition} onClick={mockOnClick} />
      );

      const circle = getByTestId('circle');

      expect(circle.getAttribute('data-radius')).toBe('1');
    });

    it('should handle extreme latitude/longitude values', () => {
      const extremePosition: DevicePosition = {
        latitude: 89.999,
        longitude: 179.999,
        accuracy: 10,
        timestamp: Date.now(),
      };

      const { getByTestId } = render(
        <BlueDot position={extremePosition} onClick={mockOnClick} />
      );

      const marker = getByTestId('marker');
      const positionData = JSON.parse(marker.getAttribute('data-position') || '[]');

      expect(positionData[0]).toBe(89.999);
      expect(positionData[1]).toBe(179.999);
    });
  });
});
