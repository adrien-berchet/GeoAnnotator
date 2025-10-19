import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import { ThemeProvider } from './contexts/ThemeContext'
import { LanguageProvider } from './contexts/LanguageContext'
import './index.css'
import './styles/markdown-editor.css'
import './styles/themes.css'
import { router } from './routes'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <LanguageProvider>
        <ThemeProvider>
          <RouterProvider router={router} />
        </ThemeProvider>
      </LanguageProvider>
    </AuthProvider>
  </StrictMode>,
)
