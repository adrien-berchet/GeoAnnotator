import { Outlet } from 'react-router-dom'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import './App.css'

/**
 * Main application component.
 * Provides layout and navigation for all routes.
 */
function App() {
  return (
    <ErrorBoundary>
      <div className="app">
        {/* TODO: Add navigation header */}
        <main>
          <Outlet />
        </main>
      </div>
    </ErrorBoundary>
  )
}

export default App
