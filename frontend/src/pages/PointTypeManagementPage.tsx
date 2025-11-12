import { useState, useEffect, useRef, Fragment } from "react";
import { useNavigate } from "react-router-dom";
import {
  getPointTypes,
  createPointType,
  updatePointType,
  deletePointType,
  reorderPointTypes,
  uploadTypeIcon,
  downloadTypeIcon,
} from "../api/types";
import type {
  PointType,
  CreatePointTypeData,
  UpdatePointTypeData,
} from "../types/point";
import { getErrorMessage } from "../api/client";
import { useLanguage } from "../contexts/LanguageContext";
import { getPointTypeName } from "../utils/pointTypeUtils";
import TranslationManager from "../components/points/TranslationManager";
import "./PointTypeManagementPage.css";

export default function PointTypeManagementPage() {
  const { t, language } = useLanguage();
  const navigate = useNavigate();
  const [types, setTypes] = useState<PointType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create form
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTypeNames, setNewTypeNames] = useState<Record<string, string>>(
    () => ({
      [language || "en"]: "",
    }),
  );
  const [newTypeIcon, setNewTypeIcon] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [iconLoadError, setIconLoadError] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Edit state
  const [editingTypeId, setEditingTypeId] = useState<string | null>(null);
  const [editingTypeNames, setEditingTypeNames] = useState<
    Record<string, string>
  >({});
  const [editingTypeIcon, setEditingTypeIcon] = useState("");
  const [editingIconFile, setEditingIconFile] = useState<File | null>(null);
  const [editingIconLoadError, setEditingIconLoadError] = useState(false);
  const [updating, setUpdating] = useState(false);
  const editFileInputRef = useRef<HTMLInputElement>(null);

  // Delete state
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadTypes();
  }, []);

  const loadTypes = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getPointTypes();
      setTypes(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = [
      "image/svg+xml",
      "image/png",
      "image/jpeg",
      "image/jpg",
    ];
    if (!allowedTypes.includes(file.type)) {
      setCreateError(
        t(
          "types.invalidFileType",
          "Invalid file type. Please upload SVG, PNG, or JPG files.",
        ),
      );
      return;
    }

    // Validate file size (1MB)
    const maxSize = 1 * 1024 * 1024;
    if (file.size > maxSize) {
      setCreateError(
        t("types.fileTooLarge", "File too large. Maximum size is 1MB."),
      );
      return;
    }

    setSelectedFile(file);

    // Upload immediately
    try {
      setUploading(true);
      setCreateError(null);
      const result = await uploadTypeIcon(file);
      setNewTypeIcon(result.icon_url);
    } catch (err) {
      setCreateError(getErrorMessage(err));
      setSelectedFile(null);
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setNewTypeIcon("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleEditFileSelect = async (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = [
      "image/svg+xml",
      "image/png",
      "image/jpeg",
      "image/jpg",
    ];
    if (!allowedTypes.includes(file.type)) {
      setError(
        t(
          "types.invalidFileType",
          "Invalid file type. Please upload SVG, PNG, or JPG files.",
        ),
      );
      return;
    }

    // Validate file size (1MB)
    const maxSize = 1 * 1024 * 1024;
    if (file.size > maxSize) {
      setError(t("types.fileTooLarge", "File too large. Maximum size is 1MB."));
      return;
    }

    setEditingIconFile(file);

    // Upload immediately
    try {
      setUploading(true);
      setError(null);
      const result = await uploadTypeIcon(file);
      setEditingTypeIcon(result.icon_url);
      setEditingIconLoadError(false);
    } catch (err) {
      setError(getErrorMessage(err));
      setEditingIconFile(null);
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveEditFile = () => {
    setEditingIconFile(null);
    setEditingTypeIcon("");
    if (editFileInputRef.current) {
      editFileInputRef.current.value = "";
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate names
    if (!newTypeNames || Object.keys(newTypeNames).length === 0) {
      setCreateError(
        t(
          "types.atLeastOneTranslation",
          "At least one translation is required",
        ),
      );
      return;
    }

    // Check that all names are non-empty
    for (const [lang, name] of Object.entries(newTypeNames)) {
      if (!name.trim()) {
        setCreateError(
          t("types.nameCannotBeEmpty", `Name for '${lang}' cannot be empty`),
        );
        return;
      }
    }

    try {
      setCreating(true);
      setCreateError(null);

      const data: CreatePointTypeData = {
        names: newTypeNames,
        creation_language: language,
      };

      if (newTypeIcon.trim()) {
        data.icon = newTypeIcon.trim();
      }

      const newType = await createPointType(data);
      setTypes([...types, newType]);
      setNewTypeNames({ [language]: "" });
      setNewTypeIcon("");
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      setShowCreateForm(false);
    } catch (err) {
      setCreateError(getErrorMessage(err));
    } finally {
      setCreating(false);
    }
  };

  const handleStartEdit = (type: PointType) => {
    // Don't allow editing base types
    if (!type.owner) {
      return;
    }
    setEditingTypeId(type.id);
    setEditingTypeNames(type.names);
    setEditingTypeIcon(type.icon);
  };

  const handleCancelEdit = () => {
    setEditingTypeId(null);
    setEditingTypeNames({});
    setEditingTypeIcon("");
    setEditingIconFile(null);
    setEditingIconLoadError(false);
    if (editFileInputRef.current) {
      editFileInputRef.current.value = "";
    }
  };

  const handleUpdate = async (typeId: string) => {
    // Validate names
    if (!editingTypeNames || Object.keys(editingTypeNames).length === 0) {
      setError(
        t(
          "types.atLeastOneTranslation",
          "At least one translation is required",
        ),
      );
      return;
    }

    try {
      setUpdating(true);

      const data: UpdatePointTypeData = {
        names: editingTypeNames,
        icon: editingTypeIcon.trim() || undefined,
      };

      const updatedType = await updatePointType(typeId, data);
      setTypes(types.map((t) => (t.id === typeId ? updatedType : t)));
      setEditingTypeId(null);
      setEditingTypeNames({});
      setEditingTypeIcon("");
      setEditingIconFile(null);
      setEditingIconLoadError(false);
      if (editFileInputRef.current) {
        editFileInputRef.current.value = "";
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setUpdating(false);
    }
  };

  const handleDelete = async (typeId: string, typeName: string) => {
    const message = `Are you sure you want to delete "${typeName}"?\n\nAll points with this type will be switched to the default "Point" type.\n\nThis action cannot be undone.`;

    if (!confirm(message)) {
      return;
    }

    try {
      setDeleting(typeId);
      await deletePointType(typeId);
      setTypes(types.filter((t) => t.id !== typeId));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDeleting(null);
    }
  };

  const moveType = (index: number, direction: "up" | "down") => {
    const newTypes = [...types];
    const targetIndex = direction === "up" ? index - 1 : index + 1;

    if (targetIndex < 0 || targetIndex >= newTypes.length) {
      return;
    }

    [newTypes[index], newTypes[targetIndex]] = [
      newTypes[targetIndex],
      newTypes[index],
    ];
    // Met à jour le champ order localement
    const updatedTypes = newTypes.map((type, idx) => ({ ...type, order: idx }));
    setTypes(updatedTypes);

    // Update order on server - send ALL types (including base types)
    const reorderData = updatedTypes.map((type) => ({
      id: type.id,
      order: type.order,
    }));

    reorderPointTypes(reorderData).catch((err) => {
      setError(getErrorMessage(err));
    });
  };

  if (loading) {
    return (
      <div className="type-management-page">
        <div className="loading">
          {t("types.loadingTypes", "Loading point types...")}
        </div>
      </div>
    );
  }

  return (
    <div className="type-management-page">
      <header className="page-header">
        <h1>{t("types.manageTypes", "Point Type Management")}</h1>
      </header>

      {error && (
        <div className="error-banner" role="alert">
          {error}
          <button
            onClick={() => setError(null)}
            aria-label={t("common.close", "Dismiss error")}
          >
            ×
          </button>
        </div>
      )}

      <div className="type-management-content">
        <div className="create-type-section">
          {!showCreateForm ? (
            <button
              onClick={() => {
                setShowCreateForm(true);
                setNewTypeNames({ [language]: "" });
                setNewTypeIcon("");
                setCreateError(null);
              }}
              className="btn-primary"
              aria-label={t("types.addNewType", "Add new point type")}
            >
              + {t("types.addNewType", "Add New Type")}
            </button>
          ) : (
            <form onSubmit={handleCreate} className="create-type-form">
              <h2>{t("types.createNewType", "Create New Point Type")}</h2>

              {createError && (
                <div className="error-message" role="alert">
                  {createError}
                </div>
              )}

              <div className="form-group">
                <TranslationManager
                  names={newTypeNames}
                  onChange={setNewTypeNames}
                  disabled={creating}
                />
              </div>

              <div className="form-group">
                <label htmlFor="type-icon">
                  {t("types.icon", "Icon")}{" "}
                  <span className="optional">
                    ({t("types.optional", "optional")})
                  </span>
                </label>
                <div
                  style={{ display: "flex", alignItems: "center", gap: "1rem" }}
                >
                  {/* Bouton de sélection de fichier */}
                  <div
                    className="icon-upload-section"
                    style={{ flex: "0 0 auto" }}
                  >
                    <input
                      ref={fileInputRef}
                      id="icon-file"
                      type="file"
                      accept=".svg,.png,.jpg,.jpeg,image/svg+xml,image/png,image/jpeg"
                      onChange={handleFileSelect}
                      disabled={creating || uploading}
                      style={{ display: "none" }}
                    />
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="btn-secondary"
                      disabled={creating || uploading}
                    >
                      {uploading
                        ? t("types.uploading", "Uploading...")
                        : t("types.chooseIconFile", "Choose Icon File")}
                    </button>
                    {selectedFile && (
                      <div className="file-preview">
                        <span className="file-name">{selectedFile.name}</span>
                        <button
                          type="button"
                          onClick={handleRemoveFile}
                          className="btn-icon"
                          disabled={creating || uploading}
                          aria-label={t("types.removeFile", "Remove file")}
                        >
                          ✕
                        </button>
                      </div>
                    )}
                  </div>
                  {/* Séparateur OU */}
                  <div
                    className="form-divider"
                    style={{ flex: "0 0 auto", margin: 0 }}
                  >
                    <span>{t("types.or", "OR")}</span>
                  </div>
                  {/* Champ input pour URL/emoji et preview */}
                  <div
                    style={{
                      flex: 1,
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                    }}
                  >
                    <input
                      id="type-icon"
                      type="text"
                      value={newTypeIcon}
                      onChange={(e) => {
                        setNewTypeIcon(e.target.value);
                        setIconLoadError(false);
                      }}
                      placeholder={t(
                        "types.iconPlaceholder",
                        "Enter emoji (e.g., 🎨) or URL",
                      )}
                      maxLength={500}
                      disabled={creating || uploading}
                      style={{ flex: 1 }}
                    />
                    {/* Download button for external URLs with CORS issues */}
                    {newTypeIcon &&
                      newTypeIcon.startsWith("http") &&
                      iconLoadError && (
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              setUploading(true);
                              setCreateError(null);
                              const result =
                                await downloadTypeIcon(newTypeIcon);
                              setNewTypeIcon(result.icon_url);
                              setIconLoadError(false);
                            } catch (err) {
                              setCreateError(getErrorMessage(err));
                            } finally {
                              setUploading(false);
                            }
                          }}
                          className="btn-secondary"
                          disabled={uploading}
                          title={t(
                            "types.downloadIconTitle",
                            "Download and save this icon locally",
                          )}
                        >
                          {uploading
                            ? t("types.downloading", "Downloading...")
                            : t("types.downloadIcon", "Download Icon")}
                        </button>
                      )}
                    {/* Icon preview */}
                    {newTypeIcon && (
                      <div className="icon-preview">
                        {newTypeIcon.startsWith("http") ||
                        newTypeIcon.startsWith("/") ||
                        newTypeIcon.startsWith("data:") ? (
                          iconLoadError ? (
                            <span
                              className="icon-error"
                              title={t(
                                "types.corsIssue",
                                "Click 'Download Icon' to fix CORS issue",
                              )}
                            >
                              ❌
                            </span>
                          ) : (
                            <img
                              src={newTypeIcon}
                              alt={t("types.iconPreview", "Icon preview")}
                              className="type-icon"
                              onLoad={() => setIconLoadError(false)}
                              onError={() => setIconLoadError(true)}
                            />
                          )
                        ) : (
                          <span className="type-icon-emoji">{newTypeIcon}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <small className="form-help">
                  {t(
                    "types.uploadIconHelp",
                    'Upload an icon file (SVG, PNG, JPG - max 1MB) or enter an emoji/URL. If an external URL doesn\'t load due to CORS, click "Download Icon" to save it locally.',
                  )}
                </small>
              </div>

              <div className="form-actions">
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={creating}
                >
                  {creating
                    ? t("types.creating", "Creating...")
                    : t("types.createType", "Create Type")}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewTypeNames({ [language]: "" });
                    setNewTypeIcon("");
                    setCreateError(null);
                  }}
                  className="btn-secondary"
                  disabled={creating}
                >
                  {t("common.cancel", "Cancel")}
                </button>
              </div>
            </form>
          )}
        </div>

        <div className="types-list">
          <h2>
            {t("types.yourPointTypes", "Your Point Types")} (
            {types.filter((t) => t.owner !== null).length})
          </h2>

          {types.length === 0 ? (
            <p className="empty-state">
              {t(
                "types.noTypesYet",
                "No point types yet. Create your first type to get started!",
              )}
            </p>
          ) : (
            <table className="types-table">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Icon</th>
                  <th>Name</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {types.map((type, index) => (
                  <Fragment key={type.id}>
                    <tr className={!type.owner ? "base-type" : ""}>
                      <td>
                        <div className="order-controls">
                          <button
                            onClick={() => moveType(index, "up")}
                            disabled={index === 0}
                            aria-label="Move up"
                            className="btn-icon"
                          >
                            ▲
                          </button>
                          <button
                            onClick={() => moveType(index, "down")}
                            disabled={index === types.length - 1}
                            aria-label="Move down"
                            className="btn-icon"
                          >
                            ▼
                          </button>
                        </div>
                      </td>
                      <td>
                        {editingTypeId === type.id ? (
                          <div className="icon-edit-preview">
                            {editingTypeIcon &&
                            editingTypeIcon !== "/icons/default.svg" ? (
                              editingTypeIcon.startsWith("http") ||
                              editingTypeIcon.startsWith("/") ||
                              editingTypeIcon.startsWith("data:") ? (
                                editingIconLoadError ? (
                                  <span
                                    className="icon-error"
                                    title="Icon load error"
                                  >
                                    ❌
                                  </span>
                                ) : (
                                  <img
                                    src={editingTypeIcon}
                                    alt="Icon preview"
                                    className="type-icon"
                                    onLoad={() =>
                                      setEditingIconLoadError(false)
                                    }
                                    onError={() =>
                                      setEditingIconLoadError(true)
                                    }
                                  />
                                )
                              ) : (
                                <span className="type-icon-emoji">
                                  {editingTypeIcon}
                                </span>
                              )
                            ) : (
                              <span className="type-icon-placeholder">📍</span>
                            )}
                          </div>
                        ) : type.icon && type.icon !== "/icons/default.svg" ? (
                          type.icon.startsWith("http") ||
                          type.icon.startsWith("/") ||
                          type.icon.startsWith("data:") ? (
                            <img
                              src={type.icon}
                              alt=""
                              className="type-icon"
                              onError={(e) => {
                                e.currentTarget.style.display = "none";
                              }}
                            />
                          ) : (
                            <span className="type-icon-emoji">{type.icon}</span>
                          )
                        ) : (
                          <span className="type-icon-placeholder">📍</span>
                        )}
                      </td>
                      <td>
                        {editingTypeId === type.id ? (
                          <span className="type-name-editing">
                            {t(
                              "types.editingTranslations",
                              "Editing translations below",
                            )}
                          </span>
                        ) : (
                          <span className="type-name">
                            {getPointTypeName(type, language)}
                          </span>
                        )}
                      </td>
                      <td>
                        <div className="action-buttons">
                          {editingTypeId === type.id ? (
                            <>
                              <button
                                onClick={() => handleUpdate(type.id)}
                                disabled={updating}
                                className="btn-success"
                              >
                                {t("common.save", "Save")}
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                disabled={updating}
                                className="btn-secondary"
                              >
                                {t("common.cancel", "Cancel")}
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() =>
                                  navigate(`/map?types=${type.id}`)
                                }
                                className="btn-view"
                                aria-label={`${t("types.viewOnMap", "View")} ${getPointTypeName(type, language)} ${t("types.onMap", "on map")}`}
                                title={t("types.viewOnMap", "View on map")}
                              >
                                🗺️ {t("nav.map", "Map")}
                              </button>
                              <button
                                onClick={() =>
                                  navigate(`/points?types=${type.id}`)
                                }
                                className="btn-view"
                                aria-label={`${t("types.view", "View")} ${getPointTypeName(type, language)} ${t("types.list", "list")}`}
                                title={t(
                                  "types.viewPointsList",
                                  "View points list",
                                )}
                              >
                                📋 {t("tags.list", "List")}
                              </button>
                              {type.owner && (
                                <>
                                  <button
                                    onClick={() => handleStartEdit(type)}
                                    className="btn-edit"
                                    aria-label={`${t("common.edit", "Edit")} ${getPointTypeName(type, language)}`}
                                  >
                                    {t("common.edit", "Edit")}
                                  </button>
                                  <button
                                    onClick={() =>
                                      handleDelete(
                                        type.id,
                                        getPointTypeName(type, language),
                                      )
                                    }
                                    disabled={deleting === type.id}
                                    className="btn-delete"
                                    aria-label={`${t("common.delete", "Delete")} ${getPointTypeName(type, language)}`}
                                  >
                                    {deleting === type.id
                                      ? t("types.deleting", "Deleting...")
                                      : t("common.delete", "Delete")}
                                  </button>
                                </>
                              )}
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                    {editingTypeId === type.id && (
                      <tr className="edit-translation-row">
                        <td colSpan={4}>
                          <div className="edit-section">
                            <TranslationManager
                              names={editingTypeNames}
                              onChange={setEditingTypeNames}
                              disabled={updating}
                            />

                            <div className="icon-edit-section">
                              <label>Edit Icon:</label>

                              {/* File upload section */}
                              <div className="icon-upload-controls">
                                <input
                                  ref={editFileInputRef}
                                  id={`edit-icon-file-${type.id}`}
                                  type="file"
                                  accept=".svg,.png,.jpg,.jpeg,image/svg+xml,image/png,image/jpeg"
                                  onChange={handleEditFileSelect}
                                  disabled={updating || uploading}
                                  style={{ display: "none" }}
                                />
                                <button
                                  type="button"
                                  onClick={() =>
                                    editFileInputRef.current?.click()
                                  }
                                  className="btn-secondary btn-sm"
                                  disabled={updating || uploading}
                                >
                                  {uploading ? "Uploading..." : "Choose File"}
                                </button>

                                {editingIconFile && (
                                  <div className="file-preview">
                                    <span className="file-name">
                                      {editingIconFile.name}
                                    </span>
                                    <button
                                      type="button"
                                      onClick={handleRemoveEditFile}
                                      className="btn-icon"
                                      disabled={updating || uploading}
                                      aria-label="Remove file"
                                    >
                                      ✕
                                    </button>
                                  </div>
                                )}
                              </div>

                              <div className="form-divider">
                                <span>OR</span>
                              </div>

                              {/* Manual URL/emoji input */}
                              <div
                                style={{
                                  display: "flex",
                                  gap: "0.5rem",
                                  alignItems: "center",
                                  flex: 1,
                                }}
                              >
                                <input
                                  type="text"
                                  value={editingTypeIcon}
                                  onChange={(e) => {
                                    setEditingTypeIcon(e.target.value);
                                    setEditingIconLoadError(false);
                                  }}
                                  placeholder="Enter emoji (e.g., 🎨) or URL"
                                  maxLength={500}
                                  disabled={updating || uploading}
                                  style={{ flex: 1 }}
                                />
                                {/* Download button for external URLs with CORS issues */}
                                {editingTypeIcon &&
                                  editingTypeIcon.startsWith("http") &&
                                  editingIconLoadError && (
                                    <button
                                      type="button"
                                      onClick={async () => {
                                        try {
                                          setUploading(true);
                                          setError(null);
                                          const result =
                                            await downloadTypeIcon(
                                              editingTypeIcon,
                                            );
                                          setEditingTypeIcon(result.icon_url);
                                          setEditingIconLoadError(false);
                                        } catch (err) {
                                          setError(getErrorMessage(err));
                                        } finally {
                                          setUploading(false);
                                        }
                                      }}
                                      className="btn-secondary btn-sm"
                                      disabled={uploading}
                                      title="Download and save this icon locally"
                                    >
                                      {uploading
                                        ? "Downloading..."
                                        : "Download"}
                                    </button>
                                  )}
                              </div>

                              <small className="form-help">
                                Upload a file (SVG, PNG, JPG - max 1MB) or enter
                                an emoji/URL
                              </small>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="info-box">
          <h3>{t("types.aboutPointTypes", "About Point Types")}</h3>
          <ul>
            <li>
              {t(
                "types.helpCategorize",
                "Point types help you categorize your GPS points with custom icons",
              )}
            </li>
            <li>
              {t(
                "types.baseTypesInfo",
                'Base types (like "Point") are available to all users and cannot be edited',
              )}
            </li>
            <li>
              {t(
                "types.customTypesLimit",
                "You can create up to 1,000 custom types",
              )}
            </li>
            <li>
              {t(
                "types.deletingTypeInfo",
                'Deleting a type will switch all associated points to the default "Point" type',
              )}
            </li>
            <li>
              {t(
                "types.reorderInfo",
                "Reorder types using the ▲▼ buttons to customize how they appear in dropdowns",
              )}
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
