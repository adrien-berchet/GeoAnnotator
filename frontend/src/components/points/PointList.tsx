/**
 * Point list component.
 *
 * Displays list of GPS points with pagination, filters, and search.
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getPoints } from "../../api/points";
import { getErrorMessage } from "../../api/client";
import { LoadingSpinner } from "../common/LoadingSpinner";
import type { GPSPoint, PointsFilter } from "../../types/point";

interface PointListProps {
  filter?: PointsFilter;
  onPointSelect?: (point: GPSPoint) => void;
}

/**
 * Point list component.
 */
export function PointList({ filter, onPointSelect }: PointListProps) {
  const navigate = useNavigate();
  const [points, setPoints] = useState<GPSPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  /**
   * Load points on mount or filter change.
   */
  useEffect(() => {
    loadPoints();
  }, [filter]);

  /**
   * Load points from API.
   */
  const loadPoints = async () => {
    setIsLoading(true);
    setError("");

    try {
      const data = await getPoints(filter);
      setPoints(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle point click.
   */
  const handlePointClick = (point: GPSPoint) => {
    if (onPointSelect) {
      onPointSelect(point);
    } else {
      navigate(`/points/${point.id}`);
    }
  };

  /**
   * Format date.
   */
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading points..." />;
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">{error}</p>
        <button onClick={loadPoints} className="btn-secondary">
          Retry
        </button>
      </div>
    );
  }

  if (points.length === 0) {
    return (
      <div className="empty-state">
        <p>No points found</p>
        <p className="text-muted">
          {filter
            ? "Try adjusting your filters"
            : "Create your first point by clicking on the map"}
        </p>
      </div>
    );
  }

  return (
    <div className="point-list">
      {points.map((point) => (
        <div
          key={point.id}
          className="point-list-item"
          onClick={() => handlePointClick(point)}
        >
          <div className="point-list-header">
            <h3 className="point-list-title">
              {point.type && point.type.icon && (
                <img
                  src={point.type.icon}
                  alt=""
                  style={{
                    width: "16px",
                    height: "16px",
                    marginRight: "6px",
                    verticalAlign: "middle",
                  }}
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              )}
              {point.title}
            </h3>
            {point.is_public && (
              <span className="badge badge-public">Public</span>
            )}
          </div>

          {point.description && (
            <div
              className="point-list-description"
              dangerouslySetInnerHTML={{
                __html:
                  point.description.substring(0, 150) +
                  (point.description.length > 150 ? "..." : ""),
              }}
            />
          )}

          <div className="point-list-meta">
            <div className="point-list-tags">
              {point.tags.slice(0, 3).map((tag) => (
                <span key={tag.id} className="tag tag-small">
                  {tag.name}
                </span>
              ))}
              {point.tags.length > 3 && (
                <span className="tag tag-small">+{point.tags.length - 3}</span>
              )}
            </div>

            <div className="point-list-info">
              <span className="point-list-annotations">
                {point.annotation_count} annotation
                {point.annotation_count !== 1 ? "s" : ""}
              </span>
              <span className="point-list-date">
                {formatDate(point.created_at)}
              </span>
            </div>
          </div>

          <div className="point-list-location">
            <span>
              📍 {point.latitude.toFixed(6)}, {point.longitude.toFixed(6)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
