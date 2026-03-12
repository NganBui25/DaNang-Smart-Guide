import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, MapPin, Compass, ArrowRight, Coffee, Utensils, Gamepad2 } from 'lucide-react'
import SearchBar from '../components/SearchBar'
import PlaceCard from '../components/PlaceCard'
import { placesApi } from '../services/api'

const CATEGORIES = [
    { name: 'Cafe', icon: Coffee, color: 'from-amber-600 to-orange-700', query: 'Cafe' },
    { name: 'Quán ăn', icon: Utensils, color: 'from-green-600 to-teal-700', query: 'Quán ăn' },
    { name: 'Vui chơi', icon: Gamepad2, color: 'from-purple-600 to-violet-700', query: 'Vui chơi' },
]

export default function HomePage() {
    const [featured, setFeatured] = useState([])
    const navigate = useNavigate()

    useEffect(() => {
        placesApi.list({ page_size: 8 })
            .then(res => setFeatured(res.data.results || []))
            .catch(() => { })
    }, [])

    return (
        <div className="min-h-screen bg-gray-950">
            {/* ===== Hero Section ===== */}
            <section className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
                {/* Background gradient blobs */}
                <div className="absolute inset-0 pointer-events-none overflow-hidden">
                    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-600/10 rounded-full blur-3xl animate-pulse" />
                    <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-blue-700/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
                    <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-indigo-600/8 rounded-full blur-3xl" />
                </div>

                {/* Content */}
                <div className="relative z-10 text-center max-w-3xl mx-auto">
                    {/* Badge */}
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-sky-900/40 border border-sky-700/40 text-sky-400 text-xs font-medium mb-8">
                        <Sparkles size={12} className="animate-pulse" />
                        AI Semantic Search — PhoBERT × FAISS
                    </div>

                    {/* Headline */}
                    <h1 className="text-4xl md:text-6xl font-extrabold leading-tight mb-4">
                        Khám phá{' '}
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-500">
                            Đà Nẵng
                        </span>
                        {' '}theo cách của bạn
                    </h1>
                    <p className="text-gray-400 text-lg mb-10 max-w-xl mx-auto">
                        Tìm kiếm địa điểm bản địa bằng ngôn ngữ tự nhiên. AI hiểu ý bạn và gợi ý những góc khuất thú vị nhất thành phố.
                    </p>

                    {/* Search Bar */}
                    <SearchBar autoFocus />

                    {/* Stats */}
                    <div className="flex justify-center gap-8 mt-12">
                        {[
                            { value: '144+', label: 'Địa điểm' },
                            { value: '3', label: 'Danh mục' },
                            { value: 'AI', label: 'Semantic Search' },
                        ].map(({ value, label }) => (
                            <div key={label} className="text-center">
                                <div className="text-2xl font-bold text-sky-400">{value}</div>
                                <div className="text-xs text-gray-500 mt-0.5">{label}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Scroll hint */}
                <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray-600">
                    <div className="w-5 h-8 border border-gray-600 rounded-full flex items-start justify-center pt-1.5">
                        <div className="w-1 h-2 bg-gray-500 rounded-full animate-bounce" />
                    </div>
                </div>
            </section>

            {/* ===== Categories ===== */}
            <section className="px-6 py-16 max-w-5xl mx-auto">
                <h2 className="text-2xl font-bold mb-2">Khám phá theo danh mục</h2>
                <p className="text-gray-400 text-sm mb-8">Tìm nhanh theo loại hình</p>
                <div className="grid grid-cols-3 gap-4">
                    {CATEGORIES.map(({ name, icon: Icon, color, query }) => (
                        <button
                            key={name}
                            onClick={() => navigate(`/search?q=${encodeURIComponent(query)}`)}
                            className="glass-card p-6 flex flex-col items-center gap-3 hover:scale-105 transition-all duration-300 hover:border-white/20 group"
                        >
                            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center shadow-lg`}>
                                <Icon size={22} className="text-white" />
                            </div>
                            <span className="font-semibold text-sm group-hover:text-white">{name}</span>
                            <ArrowRight size={14} className="text-gray-500 group-hover:text-sky-400 group-hover:translate-x-1 transition-all" />
                        </button>
                    ))}
                </div>
            </section>

            {/* ===== Featured Places ===== */}
            <section className="px-6 py-8 pb-20 max-w-5xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-2xl font-bold mb-1">Địa điểm nổi bật</h2>
                        <p className="text-gray-400 text-sm">Được chọn lọc từ dữ liệu thực tế</p>
                    </div>
                    <button
                        onClick={() => navigate('/search?q=địa điểm nổi bật')}
                        className="flex items-center gap-2 text-sm text-sky-400 hover:text-sky-300 transition-colors"
                    >
                        Xem tất cả <ArrowRight size={14} />
                    </button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {featured.map((place, i) => (
                        <div key={place.id} className="animate-fade-up" style={{ animationDelay: `${i * 60}ms` }}>
                            <PlaceCard place={place} />
                        </div>
                    ))}
                    {featured.length === 0 && (
                        Array.from({ length: 8 }).map((_, i) => (
                            <div key={i} className="rounded-2xl overflow-hidden">
                                <div className="skeleton h-44 rounded-t-2xl" />
                                <div className="p-4 glass-card rounded-t-none">
                                    <div className="skeleton h-4 w-3/4 mb-2" />
                                    <div className="skeleton h-3 w-1/2" />
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </section>
        </div>
    )
}
