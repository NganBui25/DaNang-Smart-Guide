import { Link, useLocation } from 'react-router-dom'
import { MapPin, Search, Compass } from 'lucide-react'

export default function Navbar() {
    const location = useLocation()
    const isHome = location.pathname === '/'

    return (
        <nav className={`
      fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-3
      transition-all duration-300
      ${isHome ? 'bg-transparent' : 'bg-gray-900/80 backdrop-blur-xl border-b border-white/8'}
    `}>
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 group">
                <div className="w-8 h-8 bg-gradient-to-br from-sky-500 to-blue-700 rounded-lg flex items-center justify-center shadow-lg shadow-sky-900/40">
                    <Compass size={16} className="text-white" />
                </div>
                <span className="font-bold text-sm">
                    <span className="text-white">Da Nang</span>
                    <span className="text-sky-400"> Smart Guide</span>
                </span>
            </Link>

            {/* Nav Links */}
            <div className="flex items-center gap-6">
                <Link
                    to="/search"
                    className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white transition-colors"
                >
                    <Search size={15} />
                    Khám phá
                </Link>
                <Link
                    to="/places"
                    className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white transition-colors"
                >
                    <MapPin size={15} />
                    Địa điểm
                </Link>
                <Link
                    to="/submit"
                    className="px-4 py-1.5 text-sm bg-sky-600 hover:bg-sky-500 rounded-lg font-medium transition-colors"
                >
                    + Đóng góp
                </Link>
            </div>
        </nav>
    )
}
