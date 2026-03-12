import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Sparkles, X } from 'lucide-react'

export default function SearchBar({ initialValue = '', autoFocus = false }) {
    const [query, setQuery] = useState(initialValue)
    const [focused, setFocused] = useState(false)
    const navigate = useNavigate()
    const inputRef = useRef(null)

    useEffect(() => {
        if (autoFocus) inputRef.current?.focus()
    }, [autoFocus])

    const handleSubmit = (e) => {
        e.preventDefault()
        const q = query.trim()
        if (!q) return
        navigate(`/search?q=${encodeURIComponent(q)}`)
    }

    const suggestions = [
        'quán cà phê chill gần biển',
        'quán ăn vỉa hè ngon rẻ',
        'điểm vui chơi cho gia đình',
        'quán cafe yên tĩnh học bài',
    ]

    return (
        <div className="w-full max-w-2xl mx-auto">
            <form onSubmit={handleSubmit}>
                <div className={`
          flex items-center gap-3 px-5 py-4 rounded-2xl border transition-all duration-300
          ${focused
                        ? 'bg-gray-800/80 border-sky-500/60 shadow-lg shadow-sky-900/20'
                        : 'bg-gray-800/40 border-white/10'}
        `}>
                    <Sparkles size={20} className="text-sky-400 flex-shrink-0" />
                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onFocus={() => setFocused(true)}
                        onBlur={() => setFocused(false)}
                        placeholder="Tìm kiếm bằng ngôn ngữ tự nhiên... VD: quán cà phê chill gần biển"
                        className="flex-1 bg-transparent outline-none text-sm placeholder-gray-500 text-white"
                    />
                    {query && (
                        <button type="button" onClick={() => setQuery('')} className="text-gray-500 hover:text-white transition-colors">
                            <X size={16} />
                        </button>
                    )}
                    <button
                        type="submit"
                        className="flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 rounded-xl text-sm font-medium transition-all duration-200 hover:shadow-lg hover:shadow-sky-700/30"
                    >
                        <Search size={15} />
                        Tìm
                    </button>
                </div>
            </form>

            {/* Gợi ý nhanh */}
            {!query && (
                <div className="flex flex-wrap gap-2 mt-3 justify-center">
                    {suggestions.map((s) => (
                        <button
                            key={s}
                            onClick={() => { setQuery(s); navigate(`/search?q=${encodeURIComponent(s)}`) }}
                            className="px-3 py-1.5 text-xs bg-gray-800/60 border border-white/8 rounded-full text-gray-400 hover:text-sky-400 hover:border-sky-500/30 transition-all duration-200"
                        >
                            {s}
                        </button>
                    ))}
                </div>
            )}
        </div>
    )
}
