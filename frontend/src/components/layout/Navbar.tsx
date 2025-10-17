/**
 * Navigation bar component.
 *
 * Displays app navigation with user menu and main actions.
 */

import { useState, useEffect, useRef } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import './Navbar.css';

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
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

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo and Brand */}
        <div className="navbar-brand">
          <Link to="/" className="navbar-logo">
            📍 GeoAnnotator
          </Link>
        </div>

        {/* Mobile menu toggle */}
        {user && (
          <button
            className="mobile-menu-toggle"
            onClick={() => setShowMobileMenu(!showMobileMenu)}
            aria-label="Toggle menu"
          >
            {showMobileMenu ? '✕' : '☰'}
          </button>
        )}

        {/* Navigation Links */}
        <div className={`navbar-links ${showMobileMenu ? 'mobile-open' : ''}`}>
          {user ? (
            <>

              <NavLink to="/" className="nav-link" onClick={() => setShowMobileMenu(false)} end>
                🗺️ <span>Map</span>
              </NavLink>
              <NavLink to="/points" className="nav-link" onClick={() => setShowMobileMenu(false)}>
                📌 <span>Points</span>
              </NavLink>
              <NavLink to="/tags" className="nav-link" onClick={() => setShowMobileMenu(false)}>
                🏷️ <span>Tags</span>
              </NavLink>
              <NavLink to="/types" className="nav-link" onClick={() => setShowMobileMenu(false)}>
                📋 <span>Types</span>
              </NavLink>
              <NavLink to="/trash" className="nav-link" onClick={() => setShowMobileMenu(false)}>
                🗑️ <span>Trash</span>
              </NavLink>

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
                      onClick={() => {
                        setShowUserMenu(false);
                        setShowMobileMenu(false);
                      }}
                    >
                      👤 Profile
                    </Link>
                    <Link
                      to="/settings"
                      className="user-menu-item"
                      onClick={() => {
                        setShowUserMenu(false);
                        setShowMobileMenu(false);
                      }}
                    >
                      ⚙️ Settings
                    </Link>
                    <div className="user-menu-divider"></div>
                    <button
                      className="user-menu-item logout-button"
                      onClick={() => {
                        setShowUserMenu(false);
                        setShowMobileMenu(false);
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
              <Link to="/login" className="btn btn-secondary">
                Login
              </Link>
              <Link to="/register" className="btn btn-primary">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
