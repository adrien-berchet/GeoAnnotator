/**
 * TrashAnnotationCard component.
 *
 * Displays a trashed annotation with its associated point (which remains active).
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { TrashAnnotation } from "../../types/trash";
import {
  restoreAnnotation,
  permanentlyDeleteAnnotation,
} from "../../api/trash";
import { useLanguage } from "../../contexts/LanguageContext";
import { SanitizedHTML } from "../common/SanitizedHTML";
import "./TrashCard.css";

interface TrashAnnotationCardProps {
  item: TrashAnnotation;
  onRestore: () => void;
  onDelete: () => void;
}

export function TrashAnnotationCard({
  item,
  onRestore,
  onDelete,
}: TrashAnnotationCardProps) {
  const { t } = useLanguage();
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleRestore = async () => {
    if (
      !confirm(
        t(
          "trash.confirmRestoreAnnotation",
          "Restore this annotation from trash?",
        ),
      )
    )
      return;

    setIsLoading(true);
    try {
      await restoreAnnotation(item.annotation.id);
      onRestore();
    } catch (error) {
      console.error("Failed to restore annotation:", error);
      alert(t("trash.restoreAnnotationFailed", "Failed to restore annotation"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (
      !confirm(
        t(
          "trash.confirmDeleteAnnotation",
          "Permanently delete this annotation? This action is irreversible.",
        ),
      )
    ) {
      return;
    }

    setIsLoading(true);
    try {
      await permanentlyDeleteAnnotation(item.annotation.id);
      onDelete();
    } catch (error) {
      console.error("Failed to delete annotation:", error);
      alert(t("trash.deleteAnnotationFailed", "Failed to delete annotation"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewPoint = () => {
    navigate(`/points/${item.gps_point.id}`);
  };

  const getDaysRemainingClass = () => {
    if (item.days_remaining <= 7) return "critical";
    if (item.days_remaining <= 14) return "warning";
    return "normal";
  };

  const formatDate = (dateString: string) => {
    const locale = t("common.locale", "en-US");
    return new Date(dateString).toLocaleDateString(locale);
  };

  const getDaysRemainingText = (days: number) => {
    if (days === 1) {
      return t("trash.oneDayRemaining", "1 day remaining");
    }
    return t("trash.daysRemaining", "{count} days remaining").replace(
      "{count}",
      String(days),
    );
  };

  const translateAnnotationType = (type: string) => {
    const typeKey = `annotations.${type.toLowerCase()}`;
    return t(typeKey, type);
  };

  const formatFileSize = (bytes: number) => {
    const kb = bytes / 1024;
    if (kb < 1024) {
      return `${kb.toFixed(2)} ${t("common.fileSizeKB", "KB")}`;
    }
    const mb = kb / 1024;
    if (mb < 1024) {
      return `${mb.toFixed(2)} ${t("common.fileSizeMB", "MB")}`;
    }
    const gb = mb / 1024;
    return `${gb.toFixed(2)} ${t("common.fileSizeGB", "GB")}`;
  };

  const renderAnnotationPreview = () => {
    const { annotation } = item;

    if (annotation.type === "text") {
      return (
        <div className="annotation-preview-content text">
          <span className="icon">📝</span>
          <SanitizedHTML
            html={annotation.text_content?.substring(0, 150) + "..." || ""}
            className="text-preview"
          />
        </div>
      );
    }

    return (
      <div className="annotation-preview-content file">
        <span className="icon">
          {annotation.type === "image"
            ? "🖼️"
            : annotation.type === "document"
              ? "📄"
              : "📎"}
        </span>
        <div className="file-info">
          <div className="file-name">{annotation.file?.file_name}</div>
          <div className="file-meta">
            <span className="file-type">
              {translateAnnotationType(annotation.type)}
            </span>
            {annotation.file?.file_size && (
              <span className="file-size">
                {formatFileSize(annotation.file.file_size)}
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div
      className="trash-card trash-annotation-card"
      id={`annotation-${item.annotation.id}`}
    >
      <div className="trash-card-header">
        <div className="trash-card-info">
          <h3 className="trash-card-title">
            {t("trash.deletedAnnotation", "Deleted annotation")}
          </h3>
          <div className="trash-card-meta">
            <span className="deleted-by">
              {t("trash.deletedBy", "Deleted by {email}").replace(
                "{email}",
                item.deleted_by.email,
              )}
            </span>
            <span className="deleted-at">
              {t("trash.on", "on")} {formatDate(item.deleted_at)}
            </span>
          </div>
        </div>
        <div className={`days-remaining ${getDaysRemainingClass()}`}>
          {getDaysRemainingText(item.days_remaining)}
        </div>
      </div>

      <div className="annotation-preview">{renderAnnotationPreview()}</div>

      <div className="associated-point">
        <div className="associated-point-header">
          <h4>
            {t("trash.associatedPointActive", "Associated point (active)")}
          </h4>
          <button className="btn-link" onClick={handleViewPoint}>
            {t("trash.viewPoint", "View point")} →
          </button>
        </div>
        <div className="point-info">
          <span className="icon">📍</span>
          <span className="point-title">{item.gps_point.title}</span>
        </div>
      </div>

      <div className="trash-card-actions">
        <button
          className="btn btn-restore"
          onClick={handleRestore}
          disabled={isLoading || item.is_expired}
        >
          ↺ {t("trash.restore", "Restore")}
        </button>
        <button
          className="btn btn-delete"
          onClick={handleDelete}
          disabled={isLoading}
        >
          🗑️ {t("trash.deletePermanently", "Delete permanently")}
        </button>
      </div>

      {item.is_expired && (
        <div className="expired-notice">
          ⚠️{" "}
          {t(
            "trash.annotationExpiredNotice",
            "This annotation has expired and will be automatically deleted.",
          )}
        </div>
      )}
    </div>
  );
}
