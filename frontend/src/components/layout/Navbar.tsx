/**
 * Navigation bar component.
 * 
 * Displays app navigation with user menu, search, and main actions.
 */

import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import './Navbar.css';

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/points?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo and Brand */}
        <div className="navbar-brand">
          <Link to="/" className="navbar-logo">
            📍 GeoAnnotator
          </Link>
        </div>

        {/* Search Bar */}
        {user && (
          <form className="navbar-search" onSubmit={handleSearch}>
            <input
              type="search"
              placeholder="Search points..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            <button type="submit" className="search-button">
              🔍
            </button>
          </form>
        )}

        {/* Navigation Links */}
        <div className="navbar-links">
          {user ? (
            <>
              <Link to="/" className="nav-link">
                🗺️ Map
              </Link>
              <Link to="/points" className="nav-link">
                📌 Points
              </Link>
              <Link to="/trash" className="nav-link">
                🗑️ Trash
              </Link>

              {/* User Menu */}
              <div className="user-menu" ref={userMenuRef}>
                <button
                  className="user-menu-button"
                  onClick={() => setShowUserMenu(!showUserMenu)}
                >
                  <span className="user-avatar">
                    {user.first_name?.[0]?.toUpperCase() || user.email[0].toUpperCase()}
                  </span>
                  <span className="user-name">
                    {user.first_name || user.email}
                  </span>
                  <span className="dropdown-arrow">▼</span>
                </button>

                {showUserMenu && (
                  <div className="user-menu-dropdown">
                    <div className="user-menu-header">
                      <div className="user-menu-email">{user.email}</div>
                    </div>
                    <div className="user-menu-divider"></div>
                    <Link
                      to="/profile"
                      className="user-menu-item"
                      onClick={() => setShowUserMenu(false)}
                    >
                      👤 Profile
                    </Link>
                    <Link
                      to="/settings"
                      className="user-menu-item"
                      onClick={() => setShowUserMenu(false)}
                    >
                      ⚙️ Settings
                    </Link>
                    <div className="user-menu-divider"></div>
                    <button
                      className="user-menu-item logout-button"
                      onClick={() => {
                        setShowUserMenu(false);
                        handleLogout();
                      }}
                    >
                      🚪 Logout
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link">
                Login
              </Link>
              <Link to="/register" className="nav-link nav-link-primary">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
