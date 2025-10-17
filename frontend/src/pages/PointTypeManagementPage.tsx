import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPointTypes, createPointType, updatePointType, deletePointType, reorderPointTypes } from '../api/types';
import type { PointType, CreatePointTypeData, UpdatePointTypeData } from '../types/point';
import { getErrorMessage } from '../api/client';
import './PointTypeManagementPage.css';

export default function PointTypeManagementPage() {
  const navigate = useNavigate();
  const [types, setTypes] = useState<PointType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create form
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTypeName, setNewTypeName] = useState('');
  const [newTypeIcon, setNewTypeIcon] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Edit state
  const [editingTypeId, setEditingTypeId] = useState<string | null>(null);
  const [editingTypeName, setEditingTypeName] = useState('');
  const [editingTypeIcon, setEditingTypeIcon] = useState('');
  const [updating, setUpdating] = useState(false);

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

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newTypeName.trim()) {
      setCreateError('Type name cannot be empty');
      return;
    }

    try {
      setCreating(true);
      setCreateError(null);

      const data: CreatePointTypeData = {
        name: newTypeName.trim(),
      };

      if (newTypeIcon.trim()) {
        data.icon = newTypeIcon.trim();
      }

      const newType = await createPointType(data);
      setTypes([...types, newType]);
      setNewTypeName('');
      setNewTypeIcon('');
      setShowCreateForm(false);
    } catch (err) {
      setCreateError(getErrorMessage(err));
    } finally {
      setCreating(false);
    }
  };

  const handleStartEdit = (type: PointType) => {
    // Don't allow editing base types
    if (!type.user) {
      return;
    }
    setEditingTypeId(type.id);
    setEditingTypeName(type.name);
    setEditingTypeIcon(type.icon);
  };

  const handleCancelEdit = () => {
    setEditingTypeId(null);
    setEditingTypeName('');
    setEditingTypeIcon('');
  };

  const handleUpdate = async (typeId: string) => {
    if (!editingTypeName.trim()) {
      return;
    }

    try {
      setUpdating(true);

      const data: UpdatePointTypeData = {
        name: editingTypeName.trim(),
        icon: editingTypeIcon.trim() || undefined,
      };

      const updatedType = await updatePointType(typeId, data);
      setTypes(types.map(t => t.id === typeId ? updatedType : t));
      setEditingTypeId(null);
      setEditingTypeName('');
      setEditingTypeIcon('');
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
      setTypes(types.filter(t => t.id !== typeId));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDeleting(null);
    }
  };

  const moveType = (index: number, direction: 'up' | 'down') => {
    const newTypes = [...types];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;

    if (targetIndex < 0 || targetIndex >= newTypes.length) {
      return;
    }

    [newTypes[index], newTypes[targetIndex]] = [newTypes[targetIndex], newTypes[index]];
    setTypes(newTypes);

    // Update order on server - send ALL types (including base types)
    // Backend will store user-specific custom order
    const reorderData = newTypes.map((type, idx) => ({
      id: type.id,
      order: idx,
    }));

    reorderPointTypes(reorderData).catch(err => {
      setError(getErrorMessage(err));
      loadTypes(); // Reload on error
    });
  };

  if (loading) {
    return (
      <div className="type-management-page">
        <div className="loading">Loading point types...</div>
      </div>
    );
  }

  return (
    <div className="type-management-page">
      <header className="page-header">
        <h1>Point Type Management</h1>
        <button onClick={() => navigate(-1)} className="btn-secondary">
          Back
        </button>
      </header>

      {error && (
        <div className="error-banner" role="alert">
          {error}
          <button onClick={() => setError(null)} aria-label="Dismiss error">×</button>
        </div>
      )}

      <div className="type-management-content">
        <div className="create-type-section">
          {!showCreateForm ? (
            <button
              onClick={() => setShowCreateForm(true)}
              className="btn-primary"
              aria-label="Add new point type"
            >
              + Add New Type
            </button>
          ) : (
            <form onSubmit={handleCreate} className="create-type-form">
              <h2>Create New Point Type</h2>

              {createError && (
                <div className="error-message" role="alert">
                  {createError}
                </div>
              )}

              <div className="form-group">
                <label htmlFor="type-name">
                  Type Name <span className="required">*</span>
                </label>
                <input
                  id="type-name"
                  type="text"
                  value={newTypeName}
                  onChange={(e) => setNewTypeName(e.target.value)}
                  placeholder="e.g., Restaurant, Museum, Park"
                  required
                  maxLength={100}
                  aria-required="true"
                  disabled={creating}
                />
              </div>

              <div className="form-group">
                <label htmlFor="type-icon">
                  Icon URL <span className="optional">(optional)</span>
                </label>
                <input
                  id="type-icon"
                  type="text"
                  value={newTypeIcon}
                  onChange={(e) => setNewTypeIcon(e.target.value)}
                  placeholder="/icons/restaurant.svg or leave empty for default"
                  maxLength={500}
                  disabled={creating}
                />
                <small className="form-help">
                  Leave empty to use the default icon. You can update this later.
                </small>
              </div>

              <div className="form-actions">
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={creating}
                >
                  {creating ? 'Creating...' : 'Create Type'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewTypeName('');
                    setNewTypeIcon('');
                    setCreateError(null);
                  }}
                  className="btn-secondary"
                  disabled={creating}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>

        <div className="types-list">
          <h2>Your Point Types ({types.filter(t => t.user !== null).length})</h2>

          {types.length === 0 ? (
            <p className="empty-state">
              No point types yet. Create your first type to get started!
            </p>
          ) : (
            <table className="types-table">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Icon</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {types.map((type, index) => (
                  <tr key={type.id} className={!type.user ? 'base-type' : ''}>
                    <td>
                      <div className="order-controls">
                        <button
                          onClick={() => moveType(index, 'up')}
                          disabled={index === 0}
                          aria-label="Move up"
                          className="btn-icon"
                        >
                          ▲
                        </button>
                        <button
                          onClick={() => moveType(index, 'down')}
                          disabled={index === types.length - 1}
                          aria-label="Move down"
                          className="btn-icon"
                        >
                          ▼
                        </button>
                      </div>
                    </td>
                    <td>
                      {type.icon && type.icon !== '/icons/default.svg' ? (
                        <img
                          src={type.icon}
                          alt=""
                          className="type-icon"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                      ) : (
                        <span className="type-icon-placeholder">📍</span>
                      )}
                    </td>
                    <td>
                      {editingTypeId === type.id ? (
                        <input
                          type="text"
                          value={editingTypeName}
                          onChange={(e) => setEditingTypeName(e.target.value)}
                          className="edit-input"
                          autoFocus
                        />
                      ) : (
                        <span className="type-name">{type.name}</span>
                      )}
                    </td>
                    <td>
                      {type.user ? (
                        <span className="badge badge-user">Custom</span>
                      ) : (
                        <span className="badge badge-base">Base Type</span>
                      )}
                    </td>
                    <td>
                      {type.user && (
                        <div className="action-buttons">
                          {editingTypeId === type.id ? (
                            <>
                              <button
                                onClick={() => handleUpdate(type.id)}
                                disabled={updating}
                                className="btn-success"
                              >
                                Save
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                disabled={updating}
                                className="btn-secondary"
                              >
                                Cancel
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => handleStartEdit(type)}
                                className="btn-edit"
                                aria-label={`Edit ${type.name}`}
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleDelete(type.id, type.name)}
                                disabled={deleting === type.id}
                                className="btn-delete"
                                aria-label={`Delete ${type.name}`}
                              >
                                {deleting === type.id ? 'Deleting...' : 'Delete'}
                              </button>
                            </>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="info-box">
          <h3>About Point Types</h3>
          <ul>
            <li>Point types help you categorize your GPS points with custom icons</li>
            <li>Base types (like "Point") are available to all users and cannot be edited</li>
            <li>You can create up to 1,000 custom types</li>
            <li>Deleting a type will switch all associated points to the default "Point" type</li>
            <li>Reorder types using the ▲▼ buttons to customize how they appear in dropdowns</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
