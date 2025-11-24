import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth";
import { ThemeProvider } from "./contexts/ThemeContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import { initSentry } from "./utils/sentry";
import "./index.css";
import "./styles/markdown-editor.css";
import { router } from "./routes";

// Initialize Sentry before rendering the app
initSentry();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AuthProvider>
      <LanguageProvider>
        <ThemeProvider>
          <RouterProvider router={router} />
        </ThemeProvider>
      </LanguageProvider>
    </AuthProvider>
  </StrictMode>,
);
