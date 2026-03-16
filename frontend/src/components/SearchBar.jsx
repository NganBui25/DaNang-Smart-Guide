import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Sparkles, X } from 'lucide-react'

export default function SearchBar({ initialValue = '', autoFocus = false }) {
  const [query, setQuery] = useState(initialValue)
  const [focused, setFocused] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const inputRef = useRef(null)

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus()
  }, [autoFocus])

  const handleSubmit = (e) => {
    e.preventDefault()
    const q = query.trim()
    if (!q) {
      setError('Vui long nhap tu khoa de tim kiem.')
      return
    }
    setError('')
    navigate(`/search?q=${encodeURIComponent(q)}`)
  }

  const suggestions = [
    'quan ca phe chill gan bien',
    'quan an via he ngon re',
    'diem vui choi cho gia dinh',
    'quan cafe yen tinh hoc bai',
  ]

  const containerStyle = focused
    ? {
        background: 'var(--surface)',
        borderColor: '#38bdf8',
        boxShadow: '0 10px 30px rgba(14, 165, 233, 0.18)',
      }
    : {
        background: 'var(--glass-bg)',
        borderColor: 'var(--glass-border)',
      }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit}>
        <div
          className="flex items-center gap-3 px-5 py-4 rounded-2xl border transition-all duration-300"
          style={containerStyle}
        >
          <Sparkles size={20} className="text-sky-400 flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            aria-label="Tim kiem dia diem bang ngon ngu tu nhien"
            aria-invalid={Boolean(error)}
            placeholder="Tim kiem bang ngon ngu tu nhien... VD: quan ca phe chill gan bien"
            className="search-input flex-1 bg-transparent outline-none text-sm"
          />
          {query && (
            <button
              type="button"
              aria-label="Xoa tu khoa"
              onClick={() => {
                setQuery('')
                setError('')
              }}
              className="search-clear transition-colors"
            >
              <X size={16} />
            </button>
          )}
          <button
            type="submit"
            aria-label="Thuc hien tim kiem"
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 hover:shadow-lg hover:shadow-sky-700/30"
            style={{ background: '#0284c7', color: '#e0f2fe' }}
          >
            <Search size={15} />
            Tim
          </button>
        </div>
      </form>

      {error && (
        <p role="alert" aria-live="polite" className="text-xs mt-2 text-red-400 text-center">
          {error}
        </p>
      )}

      {!query && (
        <div className="flex flex-wrap gap-2 mt-3 justify-center">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => {
                setQuery(s)
                navigate(`/search?q=${encodeURIComponent(s)}`)
              }}
              aria-label={`Tim nhanh: ${s}`}
              className="search-chip px-3 py-1.5 text-xs rounded-full transition-all duration-200"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
