import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import HomePage from './pages/HomePage'
import SearchResultsPage from './pages/SearchResultsPage'
import PlaceDetailPage from './pages/PlaceDetailPage'
import SubmitPlacePage from './pages/SubmitPlacePage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <div className="app-shell">
              <div aria-hidden className="global-bg">
                <div className="global-orb global-orb-1" />
                <div className="global-orb global-orb-2" />
                <div className="global-orb global-orb-3" />
                <div className="global-grid" />
              </div>

              <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[60] focus:px-3 focus:py-2 focus:rounded focus:bg-sky-600 focus:text-white">
                Skip to content
              </a>
              <Navbar />
              <main id="main-content">
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/search" element={<SearchResultsPage />} />
                  <Route path="/places" element={<SearchResultsPage />} />
                  <Route path="/places/:id" element={<PlaceDetailPage />} />
                  <Route path="/submit" element={<SubmitPlacePage />} />
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="*" element={<NotFoundPage />} />
                </Routes>
              </main>
            </div>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  )
}
