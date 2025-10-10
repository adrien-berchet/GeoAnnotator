import { Outlet } from 'react-router-dom'
import './App.css'

/**
 * Main application component.
 * Provides layout and navigation for all routes.
 */
function App() {
  return (
    <div className="app">
      {/* TODO: Add navigation header */}
      <main>
        <Outlet />
      </main>
    </div>
  )
}

export default App
