import { Outlet } from "react-router-dom";
import { ErrorBoundary } from "./components/common/ErrorBoundary";
import { Navbar } from "./components/layout/Navbar";
import "./App.css";

/**
 * Main application component.
 * Provides layout and navigation for all routes.
 */
function App() {
  return (
    <ErrorBoundary>
      <div className="app">
        <Navbar />
        <main>
          <Outlet />
        </main>
      </div>
    </ErrorBoundary>
  );
}

export default App;
