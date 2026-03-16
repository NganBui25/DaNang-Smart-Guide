import { Link, useLocation } from 'react-router-dom'
import { MapPin, Search, Compass, Sun, Moon } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'

function navLinkClass(active) {
  return [
    'flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg transition-all duration-200',
    active ? 'text-sky-300 bg-sky-500/15' : 'hover:text-sky-300 hover:bg-white/5',
  ].join(' ')
}

export default function Navbar() {
  const location = useLocation()
  const isHome = location.pathname === '/'
  const { theme, toggle } = useTheme()
  const { isAuthenticated, logout } = useAuth()

  const isSearch = location.pathname === '/search'
  const isPlaces = location.pathname === '/places'

  const shellStyle = isHome
    ? {
        background: 'color-mix(in srgb, var(--glass-bg) 62%, transparent)',
        borderColor: 'color-mix(in srgb, var(--glass-border) 72%, transparent)',
      }
    : {
        background: 'color-mix(in srgb, var(--glass-bg) 88%, transparent)',
        borderColor: 'var(--glass-border)',
      }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-3 md:px-6 pt-3">
      <div
        className="mx-auto max-w-6xl rounded-2xl border backdrop-blur-xl px-4 md:px-6 py-2.5 flex items-center justify-between shadow-[0_14px_40px_rgba(2,6,23,0.25)]"
        style={shellStyle}
      >
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-9 h-9 bg-gradient-to-br from-cyan-400 to-sky-600 rounded-xl flex items-center justify-center shadow-lg shadow-sky-900/40 group-hover:scale-105 transition-transform">
            <Compass size={17} className="text-white" />
          </div>
          <span className="font-extrabold text-sm md:text-base tracking-tight" style={{ color: 'var(--text)' }}>
            Da Nang <span className="text-sky-400">Smart Guide</span>
          </span>
        </Link>

        <div className="flex items-center gap-1 md:gap-2">
          <Link to="/search" className={navLinkClass(isSearch)} style={{ color: isSearch ? '#7dd3fc' : 'var(--text-muted)' }}>
            <Search size={15} /> <span className="hidden sm:inline">Kham pha</span>
          </Link>
          <Link to="/places" className={navLinkClass(isPlaces)} style={{ color: isPlaces ? '#7dd3fc' : 'var(--text-muted)' }}>
            <MapPin size={15} /> <span className="hidden sm:inline">Dia diem</span>
          </Link>

          <Link
            to="/submit"
            className="px-3.5 md:px-4 py-1.5 text-sm rounded-lg font-semibold text-white transition-all hover:-translate-y-0.5"
            style={{
              background: 'linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%)',
              boxShadow: '0 10px 20px rgba(2, 132, 199, 0.32)',
            }}
          >
            + Dong gop
          </Link>

          {isAuthenticated ? (
            <button
              onClick={logout}
              aria-label="Dang xuat"
              className="text-xs px-3 py-1.5 rounded-lg border transition-colors hover:text-sky-300"
              style={{ color: 'var(--text-muted)', borderColor: 'var(--border)' }}
            >
              Dang xuat
            </button>
          ) : (
            <Link
              to="/login"
              className="text-xs px-3 py-1.5 rounded-lg border transition-colors hover:text-sky-300"
              style={{ color: 'var(--text-muted)', borderColor: 'var(--border)' }}
            >
              Dang nhap
            </Link>
          )}

          <button
            onClick={toggle}
            aria-label={theme === 'dark' ? 'Chuyen sang giao dien sang' : 'Chuyen sang giao dien toi'}
            title={theme === 'dark' ? 'Chuyen sang giao dien sang' : 'Chuyen sang giao dien toi'}
            className="w-9 h-9 rounded-full flex items-center justify-center transition-all hover:scale-110"
            style={{ background: 'var(--surface-2)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}
          >
            {theme === 'dark' ? <Sun size={16} className="text-amber-400" /> : <Moon size={16} className="text-sky-600" />}
          </button>
        </div>
      </div>
    </nav>
  )
}
