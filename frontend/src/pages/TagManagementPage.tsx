import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getTags, createTag, updateTag, deleteTag } from "../api/points";
import type { Tag } from "../types/point";
import { getErrorMessage } from "../api/client";
import { useLanguage } from "../contexts/LanguageContext";
import "./TagManagementPage.css";

export default function TagManagementPage() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create form
  const [newTagName, setNewTagName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Edit state
  const [editingTagId, setEditingTagId] = useState<string | null>(null);
  const [editingTagName, setEditingTagName] = useState("");
  const [updating, setUpdating] = useState(false);

  // Delete state
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadTags();
  }, []);

  const loadTags = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getTags();
      setTags(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newTagName.trim()) {
      setCreateError(t("tags.nameCannotBeEmpty", "Tag name cannot be empty"));
      return;
    }

    try {
      setCreating(true);
      setCreateError(null);
      const newTag = await createTag(newTagName.trim());
      setTags([...tags, newTag]);
      setNewTagName("");
    } catch (err) {
      setCreateError(getErrorMessage(err));
    } finally {
      setCreating(false);
    }
  };

  const handleStartEdit = (tag: Tag) => {
    setEditingTagId(tag.id);
    setEditingTagName(tag.name);
  };

  const handleCancelEdit = () => {
    setEditingTagId(null);
    setEditingTagName("");
  };

  const handleUpdate = async (tagId: string) => {
    if (!editingTagName.trim()) {
      return;
    }

    try {
      setUpdating(true);
      const updatedTag = await updateTag(tagId, editingTagName.trim());
      setTags(tags.map((t) => (t.id === tagId ? updatedTag : t)));
      setEditingTagId(null);
      setEditingTagName("");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setUpdating(false);
    }
  };

  const handleDelete = async (tagId: string) => {
    if (
      !confirm(
        t(
          "tags.confirmDelete",
          "Are you sure you want to delete this tag? This action cannot be undone.",
        ),
      )
    ) {
      return;
    }

    try {
      setDeleting(tagId);
      await deleteTag(tagId);
      setTags(tags.filter((t) => t.id !== tagId));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDeleting(null);
    }
  };

  if (loading) {
    return (
      <div className="tag-management-page">
        <div className="loading">
          {t("tags.loadingTags", "Loading tags...")}
        </div>
      </div>
    );
  }

  return (
    <div className="tag-management-page">
      <div className="tag-management-header">
        <h1>{t("tags.manageTags", "Tag Management")}</h1>
        <p className="description">
          {t(
            "tags.description",
            "Create, edit, and delete tags for organizing your GPS points.",
          )}
        </p>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-error">
            ×
          </button>
        </div>
      )}

      {/* Create Form */}
      <div className="create-tag-section">
        <form onSubmit={handleCreate} className="create-tag-form">
          <h2>{t("tags.createTag", "Create New Tag")}</h2>
          {createError && <div className="create-error">{createError}</div>}
          <div className="form-group">
            <input
              id="tag-name"
              type="text"
              value={newTagName}
              onChange={(e) => {
                setNewTagName(e.target.value);
                if (createError) setCreateError(null); // Clear error when user types
              }}
              placeholder={t("tags.enterTagName", "Enter tag name...")}
              disabled={creating}
              maxLength={50}
              className="tag-name-input"
              required
            />
          </div>
          <div className="form-actions">
            <button
              type="submit"
              disabled={creating || !newTagName.trim()}
              className="create-button"
            >
              {creating
                ? t("tags.creating", "Creating...")
                : t("tags.createTag", "Create Tag")}
            </button>
          </div>
        </form>
      </div>

      {/* Tags List */}
      <div className="tags-section">
        <h2>
          {t("tags.existingTags", "Existing Tags")} ({tags.length})
        </h2>

        {tags.length === 0 ? (
          <div className="empty-state">
            <p>
              {t("tags.noTagsYet", "No tags yet. Create your first tag above!")}
            </p>
          </div>
        ) : (
          <div className="tags-list">
            {tags.map((tag) => (
              <div key={tag.id} className="tag-item">
                {editingTagId === tag.id ? (
                  // Edit mode
                  <div className="tag-edit-mode">
                    <input
                      type="text"
                      value={editingTagName}
                      onChange={(e) => setEditingTagName(e.target.value)}
                      disabled={updating}
                      maxLength={50}
                      className="tag-edit-input"
                      autoFocus
                    />
                    <div className="tag-edit-actions">
                      <button
                        onClick={() => handleUpdate(tag.id)}
                        disabled={updating || !editingTagName.trim()}
                        className="btn btn-success btn-sm"
                      >
                        {updating
                          ? t("tags.saving", "Saving...")
                          : t("common.save", "Save")}
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        disabled={updating}
                        className="btn btn-secondary btn-sm"
                      >
                        {t("common.cancel", "Cancel")}
                      </button>
                    </div>
                  </div>
                ) : (
                  // View mode
                  <div className="tag-view-mode">
                    <span className="tag-name">{tag.name}</span>
                    <div className="tag-actions">
                      <button
                        onClick={() =>
                          navigate(`/map?tags=${encodeURIComponent(tag.name)}`)
                        }
                        className="btn btn-view btn-sm"
                        title={t("tags.viewOnMap", "View on map")}
                      >
                        🗺️ {t("nav.map", "Map")}
                      </button>
                      <button
                        onClick={() =>
                          navigate(
                            `/points?tags=${encodeURIComponent(tag.name)}`,
                          )
                        }
                        className="btn btn-view btn-sm"
                        title={t("tags.viewPointsList", "View points list")}
                      >
                        📋 {t("tags.list", "List")}
                      </button>
                      <button
                        onClick={() => handleStartEdit(tag)}
                        disabled={deleting === tag.id}
                        className="btn btn-info btn-sm"
                      >
                        {t("common.edit", "Edit")}
                      </button>
                      <button
                        onClick={() => handleDelete(tag.id)}
                        disabled={deleting === tag.id}
                        className="btn btn-danger btn-sm"
                      >
                        {deleting === tag.id
                          ? t("tags.deleting", "Deleting...")
                          : t("common.delete", "Delete")}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
