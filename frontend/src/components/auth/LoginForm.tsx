/**
 * Login form component.
 *
 * Provides email/password authentication with validation and error display.
 */

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { login } from '../../api/auth';
import { getErrorMessage } from '../../api/client';

/**
 * Login form component.
 */
export function LoginForm() {
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

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

    setIsLoading(true);

    try {
      // Call login API
      const response = await login({ email, password });

      // Store tokens and user in auth context
      authLogin(response.access, response.refresh, response.user);

      // Redirect to map
      navigate('/map');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-form-container">
      <div className="login-form-card">
        <h1>Login to GeoAnnotator</h1>

        <form onSubmit={handleSubmit} className="login-form">
          {/* Error display */}
          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}

          {/* Email field */}
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
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
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              disabled={isLoading}
              autoComplete="current-password"
              required
            />
          </div>

          {/* Submit button */}
          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading}
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        {/* Register link */}
        <div className="form-footer">
          <p>
            Don't have an account?{' '}
            <a href="/register">Register here</a>
          </p>
        </div>
      </div>
    </div>
  );
}
