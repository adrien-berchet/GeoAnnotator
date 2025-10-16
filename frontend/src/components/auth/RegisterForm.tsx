/**
 * Register form component.
 *
 * Provides user registration with password strength indicator.
 */

import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { register } from '../../api/auth';
import { getErrorMessage } from '../../api/client';
import './RegisterForm.css';

/**
 * Password strength levels.
 */
type PasswordStrength = 'weak' | 'medium' | 'strong' | 'very-strong';

/**
 * Calculate password strength.
 */
function getPasswordStrength(password: string): PasswordStrength {
  if (password.length < 6) return 'weak';

  let score = 0;

  // Length check
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;

  // Character variety checks
  if (/[a-z]/.test(password)) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  if (score <= 2) return 'weak';
  if (score <= 4) return 'medium';
  if (score <= 5) return 'strong';
  return 'very-strong';
}

/**
 * Register form component.
 */
export function RegisterForm() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const passwordStrength = password ? getPasswordStrength(password) : null;

  // Apply system theme for register page (no user is authenticated yet)
  useEffect(() => {
    const applySystemTheme = () => {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    };

    applySystemTheme();

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = applySystemTheme;
    mediaQuery.addEventListener('change', handler);

    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  /**
   * Validate email format.
   */
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate email
    if (!email) {
      setError('Email is required');
      return;
    }

    if (!validateEmail(email)) {
      setError('Invalid email format');
      return;
    }

    // Validate password
    if (!password) {
      setError('Password is required');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    if (passwordStrength === 'weak') {
      setError('Please use a stronger password (add uppercase, numbers, or special characters)');
      return;
    }

    // Validate password confirmation
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      // Call register API
      const response = await register({ email, password });

      // Store tokens and user in auth context
      login(response.access, response.refresh, response.user);

      // Redirect to map
      navigate('/map');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Get password strength color.
   */
  const getStrengthColor = (strength: PasswordStrength): string => {
    const colors = {
      'weak': '#dc3545',
      'medium': '#ffc107',
      'strong': '#28a745',
      'very-strong': '#007bff',
    };
    return colors[strength];
  };

  /**
   * Get password strength label.
   */
  const getStrengthLabel = (strength: PasswordStrength): string => {
    const labels = {
      'weak': 'Weak',
      'medium': 'Medium',
      'strong': 'Strong',
      'very-strong': 'Very Strong',
    };
    return labels[strength];
  };

  return (
    <div className="register-form-container">
      <div className="register-form-card">
        <h1>Create Account</h1>

        <form onSubmit={handleSubmit} className="register-form">
          {/* Error display */}
          {error && (
            <div className="alert alert-error" role="alert">
              {error}
            </div>
          )}

          {/* Email field */}
          <div className="form-group">
            <label htmlFor="email" className="form-label">Email</label>
            <input
              id="email"
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your.email@example.com"
              disabled={isLoading}
              autoComplete="email"
              required
            />
          </div>

          {/* Password field */}
          <div className="form-group">
            <label htmlFor="password" className="form-label">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Create a strong password"
              disabled={isLoading}
              autoComplete="new-password"
              required
            />

            {/* Password strength indicator */}
            <div className="password-strength">
              <div className="strength-bar-container">
                <div
                  className="strength-bar"
                  style={{
                    width: passwordStrength ? `${(['weak', 'medium', 'strong', 'very-strong'].indexOf(passwordStrength) + 1) * 25}%` : '0%',
                    backgroundColor: passwordStrength ? getStrengthColor(passwordStrength) : 'transparent',
                  }}
                />
              </div>
              <span
                className="strength-label"
                style={{ color: passwordStrength ? getStrengthColor(passwordStrength) : 'var(--color-text-muted)' }}
              >
                {passwordStrength ? getStrengthLabel(passwordStrength) : 'No password'}
              </span>
            </div>

            <div className="form-hint">
              Use at least 8 characters with a mix of uppercase, lowercase, numbers, and symbols
            </div>
          </div>

          {/* Confirm password field */}
          <div className="form-group">
            <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              className="form-input"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              disabled={isLoading}
              autoComplete="new-password"
              required
            />
          </div>

          {/* Submit button */}
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isLoading}
          >
            {isLoading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        {/* Login link */}
        <div className="form-footer">
          <p>
            Already have an account?{' '}
            <a href="/login">Login here</a>
          </p>
        </div>
      </div>
    </div>
  );
}
