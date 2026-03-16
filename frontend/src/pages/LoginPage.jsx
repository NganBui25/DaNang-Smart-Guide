import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const location = useLocation()

  const from = location.state?.from || '/'

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')

    if (!username.trim() || !password.trim()) {
      setError('Vui long nhap username va password.')
      return
    }

    setLoading(true)
    try {
      if (mode === 'register') {
        await register({ username: username.trim(), email: email.trim(), password })
        setMessage('Dang ky thanh cong. Ban co the dang nhap ngay bay gio.')
        setMode('login')
      } else {
        await login({ username: username.trim(), password })
        navigate(from, { replace: true })
      }
    } catch (err) {
      setError(err.message || 'Khong the xu ly yeu cau.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen pt-20 px-6" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
      <div className="max-w-md mx-auto glass-card p-6">
        <h1 className="text-xl font-semibold mb-1">{mode === 'login' ? 'Dang nhap' : 'Dang ky'}</h1>
        <p className="text-sm mb-5" style={{ color: 'var(--text-muted)' }}>
          {mode === 'login' ? 'Dang nhap de su dung bookmark va danh gia.' : 'Tao tai khoan de luu dia diem yeu thich.'}
        </p>

        {error && <div role="alert" className="mb-3 text-sm text-red-400">{error}</div>}
        {message && <div role="status" className="mb-3 text-sm text-emerald-400">{message}</div>}

        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="block text-xs mb-1" htmlFor="username">Username</label>
            <input id="username" value={username} onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border bg-transparent"
              style={{ borderColor: 'var(--border)' }} />
          </div>

          {mode === 'register' && (
            <div>
              <label className="block text-xs mb-1" htmlFor="email">Email (optional)</label>
              <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bg-transparent"
                style={{ borderColor: 'var(--border)' }} />
            </div>
          )}

          <div>
            <label className="block text-xs mb-1" htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border bg-transparent"
              style={{ borderColor: 'var(--border)' }} />
          </div>

          <button type="submit" disabled={loading}
            className="w-full py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-60 text-white text-sm font-medium">
            {loading ? 'Dang xu ly...' : mode === 'login' ? 'Dang nhap' : 'Dang ky'}
          </button>
        </form>

        <div className="mt-4 text-sm" style={{ color: 'var(--text-muted)' }}>
          {mode === 'login' ? 'Chua co tai khoan?' : 'Da co tai khoan?'}{' '}
          <button onClick={() => setMode(mode === 'login' ? 'register' : 'login')} className="text-sky-400 hover:underline">
            {mode === 'login' ? 'Dang ky ngay' : 'Dang nhap'}
          </button>
        </div>

        <Link to="/" className="inline-block mt-3 text-xs text-sky-400 hover:underline">Ve trang chu</Link>
      </div>
    </div>
  )
}
