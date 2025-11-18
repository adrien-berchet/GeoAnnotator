/**
 * TrashPage component.
 *
 * Displays trashed points and annotations with 30-day retention.
 * Two separate sections to distinguish between:
 * - Points deleted (all annotations are deleted with it)
 * - Annotations deleted individually (point remains active)
 */

import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { TrashPointCard } from "../components/trash/TrashPointCard";
import { TrashAnnotationCard } from "../components/trash/TrashAnnotationCard";
import {
  getAllTrashData,
  emptyPointTrash,
  emptyAnnotationTrash,
} from "../api/trash";
import { useLanguage } from "../contexts/LanguageContext";
import type { TrashPoint, TrashAnnotation, TrashStats } from "../types/trash";
import "./TrashPage.css";

export function TrashPage() {
  const { t } = useLanguage();
  const location = useLocation();
  const [pointsTrash, setPointsTrash] = useState<TrashPoint[]>([]);
  const [annotationsTrash, setAnnotationsTrash] = useState<TrashAnnotation[]>(
    [],
  );
  const [pointsStats, setPointsStats] = useState<TrashStats>({
    total_items: 0,
    expiring_soon: 0,
    oldest_item_age_days: 0,
  });
  const [annotationsStats, setAnnotationsStats] = useState<TrashStats>({
    total_items: 0,
    expiring_soon: 0,
    oldest_item_age_days: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"points" | "annotations">(
    "points",
  );

  const loadTrashData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getAllTrashData();
      setPointsTrash(data.points);
      setPointsStats(data.pointsStats);
      setAnnotationsTrash(data.annotations);
      setAnnotationsStats(data.annotationsStats);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : t("trash.loadError", "Failed to load trash"),
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTrashData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle hash navigation to specific annotation
  useEffect(() => {
    const hash = location.hash;
    if (hash.startsWith("#annotation-")) {
      // Switch to annotations tab
      setActiveTab("annotations");

      // Wait for the tab content to render, then scroll to the annotation
      setTimeout(() => {
        const annotationId = hash.substring(1); // Remove the '#'
        const element = document.getElementById(annotationId);
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "center" });
          // Add a highlight effect
          element.classList.add("highlight-annotation");
          setTimeout(() => {
            element.classList.remove("highlight-annotation");
          }, 2000);
        }
      }, 100);
    }
  }, [location.hash, annotationsTrash]);

  const handleEmptyPointsTrash = async () => {
    const message = t(
      "trash.confirmEmptyPointsTrash",
      "Permanently delete all {count} points in trash? This action is irreversible.",
    ).replace("{count}", String(pointsStats.total_items));

    if (!confirm(message)) {
      return;
    }

    try {
      await emptyPointTrash();
      await loadTrashData();
    } catch (err) {
      console.error("Failed to empty points trash:", err);
      alert(t("trash.deleteError", "Failed to delete items"));
    }
  };

  const handleEmptyAnnotationsTrash = async () => {
    const message = t(
      "trash.confirmEmptyAnnotationsTrash",
      "Permanently delete all {count} annotations in trash? This action is irreversible.",
    ).replace("{count}", String(annotationsStats.total_items));

    if (!confirm(message)) {
      return;
    }

    try {
      await emptyAnnotationTrash();
      await loadTrashData();
    } catch (err) {
      console.error("Failed to empty annotations trash:", err);
      alert(t("trash.deleteError", "Failed to delete items"));
    }
  };

  if (isLoading) {
    return (
      <div className="page">
        <div className="loading">{t("trash.loading", "Loading trash...")}</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="error">{error}</div>
        <button className="btn-retry" onClick={loadTrashData}>
          {t("common.retry", "Retry")}
        </button>
      </div>
    );
  }

  const currentStats = activeTab === "points" ? pointsStats : annotationsStats;
  const currentCount =
    activeTab === "points" ? pointsTrash.length : annotationsTrash.length;

  return (
    <div className="page">
      <header className="page-header">
        <h1>🗑️ {t("trash.title", "Trash")}</h1>
        <p className="page-subtitle">
          {t(
            "trash.subtitle",
            "Deleted items are kept for 30 days before permanent deletion.",
          )}
        </p>
      </header>

      <div className="trash-tabs">
        <button
          className={`tab-button ${activeTab === "points" ? "active" : ""}`}
          onClick={() => setActiveTab("points")}
        >
          📍 {t("trash.deletedPoints", "Deleted points")}
          {pointsTrash.length > 0 && (
            <span className="tab-badge">{pointsTrash.length}</span>
          )}
        </button>
        <button
          className={`tab-button ${activeTab === "annotations" ? "active" : ""}`}
          onClick={() => setActiveTab("annotations")}
        >
          📝 {t("trash.deletedAnnotations", "Deleted annotations")}
          {annotationsTrash.length > 0 && (
            <span className="tab-badge">{annotationsTrash.length}</span>
          )}
        </button>
      </div>

      {currentCount > 0 && (
        <div className="trash-stats">
          <div className="stat-item">
            <span className="stat-value">{currentStats.total_items}</span>
            <span className="stat-label">{t("trash.total", "Total")}</span>
          </div>
          <div className="stat-item warning">
            <span className="stat-value">{currentStats.expiring_soon}</span>
            <span className="stat-label">
              {t("trash.expiringSoon", "Expiring soon (< 7 days)")}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-value">
              {currentStats.oldest_item_age_days}
            </span>
            <span className="stat-label">
              {t("trash.oldestItemAge", "Age of oldest (days)")}
            </span>
          </div>
        </div>
      )}

      {activeTab === "points" && (
        <div className="trash-section">
          <div className="section-header">
            <h2>{t("trash.deletedPoints", "Deleted points")}</h2>
            {pointsTrash.length > 0 && (
              <button
                className="btn btn-empty"
                onClick={handleEmptyPointsTrash}
              >
                {t("trash.emptyPointsTrash", "Empty points trash")}
              </button>
            )}
          </div>

          {pointsTrash.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📍</div>
              <h3>{t("trash.noPointsInTrash", "No points in trash")}</h3>
              <p>
                {t(
                  "trash.noPointsInTrashDesc",
                  "Deleted points will appear here and be kept for 30 days.",
                )}
              </p>
            </div>
          ) : (
            <>
              <div className="info-box">
                <p>
                  <strong>⚠️ Important :</strong>{" "}
                  {t(
                    "trash.pointsWarning",
                    "When a point is deleted, all its annotations and shares are also deleted with it. After restoration, shares will be reactivated if possible.",
                  )}
                </p>
              </div>

              <div className="trash-list">
                {pointsTrash.map((item) => (
                  <TrashPointCard
                    key={item.id}
                    item={item}
                    onRestore={loadTrashData}
                    onDelete={loadTrashData}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === "annotations" && (
        <div className="trash-section">
          <div className="section-header">
            <h2>{t("trash.deletedAnnotations", "Deleted annotations")}</h2>
            {annotationsTrash.length > 0 && (
              <button
                className="btn btn-empty"
                onClick={handleEmptyAnnotationsTrash}
              >
                {t("trash.emptyAnnotationsTrash", "Empty annotations trash")}
              </button>
            )}
          </div>

          {annotationsTrash.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📝</div>
              <h3>
                {t("trash.noAnnotationsInTrash", "No annotations in trash")}
              </h3>
              <p>
                {t(
                  "trash.noAnnotationsInTrashDesc",
                  "Individually deleted annotations will appear here and be kept for 30 days.",
                )}
              </p>
            </div>
          ) : (
            <>
              <div className="info-box">
                <p>
                  <strong>ℹ️ {t("common.note", "Note")} :</strong>{" "}
                  {t(
                    "trash.annotationsInfo",
                    "These annotations have been deleted individually. The points they are associated with remain active. Only the annotations will be permanently deleted after 30 days.",
                  )}
                </p>
              </div>

              <div className="trash-list">
                {annotationsTrash.map((item) => (
                  <TrashAnnotationCard
                    key={item.id}
                    item={item}
                    onRestore={loadTrashData}
                    onDelete={loadTrashData}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
