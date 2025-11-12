/**
 * Application routes configuration.
 *
 * Defines all routes with authentication protection.
 */

import { createBrowserRouter, Navigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import App from "./App";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { MapPage } from "./pages/MapPage";
import { PointsListPage } from "./pages/PointsListPage";
import { PointDetailPage } from "./pages/PointDetailPage";
import { EditPointPage } from "./pages/EditPointPage";
import TagManagementPage from "./pages/TagManagementPage";
import PointTypeManagementPage from "./pages/PointTypeManagementPage";
import { TrashPage } from "./pages/TrashPage";
import { SettingsPage } from "./pages/SettingsPage";
import { ImportExportPage } from "./pages/ImportExportPage";

// Placeholder components - to be implemented
const ProfilePage = () => <div>Profile Page</div>;
const SharedPointsPage = () => <div>Shared Points Page</div>;

/**
 * Protected route wrapper.
 * Redirects to login if user is not authenticated.
 */
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

/**
 * Public route wrapper.
 * Redirects to map if user is already authenticated.
 */
const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (isAuthenticated) {
    return <Navigate to="/map" replace />;
  }

  return <>{children}</>;
};

/**
 * Router configuration.
 */
export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      // Redirect root to map or login
      {
        index: true,
        element: <Navigate to="/map" replace />,
      },

      // Public routes
      {
        path: "login",
        element: (
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        ),
      },
      {
        path: "register",
        element: (
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        ),
      },

      // Protected routes
      {
        path: "map",
        element: (
          <ProtectedRoute>
            <MapPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "points",
        element: (
          <ProtectedRoute>
            <PointsListPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "points/:id",
        element: (
          <ProtectedRoute>
            <PointDetailPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "points/:id/edit",
        element: (
          <ProtectedRoute>
            <EditPointPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "tags",
        element: (
          <ProtectedRoute>
            <TagManagementPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "types",
        element: (
          <ProtectedRoute>
            <PointTypeManagementPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "profile",
        element: (
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        ),
      },
      {
        path: "settings",
        element: (
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "shared",
        element: (
          <ProtectedRoute>
            <SharedPointsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "import-export",
        element: (
          <ProtectedRoute>
            <ImportExportPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "trash",
        element: (
          <ProtectedRoute>
            <TrashPage />
          </ProtectedRoute>
        ),
      },

      // Share acceptance route (public)
      {
        path: "shares/accept/:token",
        element: <div>Accept Share Page</div>,
      },

      // 404 page
      {
        path: "*",
        element: <div>404 - Page Not Found</div>,
      },
    ],
  },
]);
