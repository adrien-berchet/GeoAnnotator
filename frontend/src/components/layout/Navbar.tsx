/**
 * Navigation bar component.
 *
 * Displays app navigation with user menu and main actions.
 */

import { useState, useEffect, useRef } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useLanguage } from '../../contexts/LanguageContext';
import './Navbar.css';

export function Navbar() {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
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

              <NavLink
                to="/"
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                onClick={() => setShowMobileMenu(false)}
                end
              >
                🗺️ <span>{t('nav.map', 'Map')}</span>
              </NavLink>
              <NavLink
                to="/points"
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                onClick={() => setShowMobileMenu(false)}
              >
                📌 <span>{t('nav.points', 'Points')}</span>
              </NavLink>
              <NavLink
                to="/tags"
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                onClick={() => setShowMobileMenu(false)}
              >
                🏷️ <span>{t('nav.tags', 'Tags')}</span>
              </NavLink>
              <NavLink
                to="/types"
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                onClick={() => setShowMobileMenu(false)}
              >
                📋 <span>{t('nav.types', 'Types')}</span>
              </NavLink>
              <NavLink
                to="/trash"
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                onClick={() => setShowMobileMenu(false)}
              >
                🗑️ <span>{t('nav.trash', 'Trash')}</span>
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
                      ⚙️ {t('nav.settings', 'Settings')}
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
                      🚪 {t('nav.logout', 'Logout')}
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-secondary">
                {t('nav.login', 'Login')}
              </Link>
              <Link to="/register" className="btn btn-primary">
                {t('nav.register', 'Register')}
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
