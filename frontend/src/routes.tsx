/**
 * Application routes configuration.
 *
 * Defines all routes with authentication protection.
 */

import { createBrowserRouter, Navigate } from "react-router-dom";
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
import { AccountPage } from "./pages/AccountPage";
import { EmailConfirmPage } from "./pages/EmailConfirmPage";
import { RegistrationConfirmPage } from "./pages/RegistrationConfirmPage";
import { AccountDeleteConfirmPage } from "./pages/AccountDeleteConfirmPage";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import { PublicRoute } from "./routes/PublicRoute";
import { SharedPointsPage } from "./pages/PlaceholderPages";
import { FriendsPage } from "./pages/FriendsPage";
import { FriendDetailPage } from "./pages/FriendDetailPage";
import { PointSharingPage } from "./pages/PointSharingPage";

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
      {
        path: "confirm-email",
        element: (
          <PublicRoute>
            <RegistrationConfirmPage />
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
        path: "points/:id/sharing",
        element: (
          <ProtectedRoute>
            <PointSharingPage />
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
        element: <Navigate to="/account" replace />,
      },
      {
        path: "account",
        element: (
          <ProtectedRoute>
            <AccountPage />
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
        path: "friends",
        element: (
          <ProtectedRoute>
            <FriendsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "friends/:friendId",
        element: (
          <ProtectedRoute>
            <FriendDetailPage />
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

      // Account management confirmation routes (require login)
      {
        path: "account/confirm-email",
        element: (
          <ProtectedRoute>
            <EmailConfirmPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "account/confirm-delete",
        element: (
          <ProtectedRoute>
            <AccountDeleteConfirmPage />
          </ProtectedRoute>
        ),
      },

      // 404 page
      {
        path: "*",
        element: <div>404 - Page Not Found</div>,
      },
    ],
  },
]);
