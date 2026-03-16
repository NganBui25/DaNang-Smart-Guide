import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen pt-20 px-6 flex items-center justify-center" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
      <div className="glass-card p-8 text-center max-w-md">
        <p className="text-xs uppercase tracking-wider text-sky-400 mb-2">404</p>
        <h1 className="text-2xl font-semibold mb-3">Khong tim thay trang</h1>
        <p className="text-sm mb-5" style={{ color: 'var(--text-muted)' }}>
          Duong dan ban truy cap khong ton tai hoac da duoc thay doi.
        </p>
        <Link to="/" className="inline-flex px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-sm">
          Ve trang chu
        </Link>
      </div>
    </div>
  )
}
