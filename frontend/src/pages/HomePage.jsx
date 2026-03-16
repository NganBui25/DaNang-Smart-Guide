import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, ArrowRight, Coffee, Utensils, Gamepad2, Star } from 'lucide-react'
import SearchBar from '../components/SearchBar'
import PlaceCard from '../components/PlaceCard'
import { placesApi } from '../services/api'

const CATEGORIES = [
  { name: 'Cafe', icon: Coffee, gradient: 'from-amber-500 to-orange-600', query: 'cafe' },
  { name: 'Quan an', icon: Utensils, gradient: 'from-emerald-500 to-teal-600', query: 'quan an' },
  { name: 'Vui choi', icon: Gamepad2, gradient: 'from-indigo-500 to-violet-600', query: 'vui choi' },
]

export default function HomePage() {
  const [featured, setFeatured] = useState([])
  const [loadingError, setLoadingError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    placesApi
      .list({ page_size: 8 })
      .then((res) => setFeatured(res.data.results || []))
      .catch(() => setLoadingError('Khong the tai danh sach noi bat.'))
  }, [])

  return (
    <div className="min-h-screen" style={{ color: 'var(--text)' }}>
      <section className="relative min-h-[92vh] px-6 pt-28 pb-14 overflow-hidden">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium mb-7 hero-ring">
              <Sparkles size={13} className="text-sky-300" />
              <span style={{ color: 'var(--text-muted)' }}>Semantic Search x AI Suggestions</span>
            </div>

            <h1 className="text-4xl md:text-6xl font-extrabold leading-[1.05] tracking-tight mb-5">
              Kham pha Da Nang
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-300 via-cyan-300 to-violet-300">
                theo phong cach hien dai
              </span>
            </h1>

            <p className="text-base md:text-lg max-w-2xl mb-8" style={{ color: 'var(--text-muted)' }}>
              Nhap nhu ban dang chat voi mot local guide. He thong se tim dia diem phu hop theo ngu canh, khong chi theo keyword.
            </p>

            <SearchBar autoFocus />

            <div className="mt-10 grid grid-cols-3 gap-3 max-w-xl">
              {[
                { value: '144+', label: 'Dia diem' },
                { value: '3', label: 'Danh muc' },
                { value: '<1s', label: 'Phan hoi' },
              ].map((item) => (
                <div key={item.label} className="glass-card py-3 text-center">
                  <div className="text-xl font-bold text-sky-300">{item.value}</div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {item.label}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-5">
            <div
              className="glass-card p-5 md:p-6 rounded-3xl"
              style={{ background: 'color-mix(in srgb, var(--glass-bg) 92%, transparent)' }}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-base">Goi y nhanh hom nay</h2>
                <span className="text-[11px] px-2 py-1 rounded-full bg-sky-500/20 text-sky-300">live</span>
              </div>
              <div className="space-y-3">
                {[
                  'quan cafe chup anh dep',
                  'quan an gan bien',
                  'choi toi o da nang',
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => navigate(`/search?q=${encodeURIComponent(q)}`)}
                    className="w-full text-left rounded-xl px-3.5 py-3 transition-all hover:-translate-y-0.5"
                    style={{
                      background: 'color-mix(in srgb, var(--surface-2) 88%, transparent)',
                      border: '1px solid var(--border)',
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm" style={{ color: 'var(--text)' }}>
                        {q}
                      </span>
                      <ArrowRight size={14} className="text-sky-300" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="px-6 py-6 max-w-6xl mx-auto">
        <div className="flex items-end justify-between mb-5">
          <div>
            <h2 className="text-2xl font-bold">Kham pha theo danh muc</h2>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Chon nhanh theo nhu cau
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {CATEGORIES.map(({ name, icon: Icon, gradient, query }) => (
            <button
              key={name}
              onClick={() => navigate(`/search?q=${encodeURIComponent(query)}`)}
              className="glass-card p-5 text-left group"
            >
              <div className="flex items-center justify-between">
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center shadow-lg`}>
                  <Icon size={20} className="text-white" />
                </div>
                <ArrowRight size={15} className="text-sky-300 transition-transform group-hover:translate-x-1" />
              </div>
              <p className="mt-4 font-semibold">{name}</p>
              <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                Tim de xuat thong minh cho {name.toLowerCase()}
              </p>
            </button>
          ))}
        </div>
      </section>

      <section className="px-6 py-10 pb-16 max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Star size={18} className="text-amber-300" />
              Dia diem noi bat
            </h2>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Danh sach de demo ngay
            </p>
          </div>
          <button
            onClick={() => navigate('/search?q=dia diem noi bat')}
            className="text-sm inline-flex items-center gap-2 text-sky-300 hover:text-sky-200"
          >
            Xem tat ca <ArrowRight size={14} />
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {featured.map((place, i) => (
            <div key={place.id} className="animate-fade-up" style={{ animationDelay: `${i * 60}ms` }}>
              <PlaceCard place={place} />
            </div>
          ))}

          {featured.length === 0 &&
            Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="rounded-2xl overflow-hidden">
                <div className="skeleton h-44 rounded-t-2xl" />
                <div className="p-4 glass-card rounded-t-none">
                  <div className="skeleton h-4 w-3/4 mb-2" />
                  <div className="skeleton h-3 w-1/2" />
                </div>
              </div>
            ))}
        </div>

        {loadingError && (
          <p role="alert" className="text-xs mt-4 text-red-400">
            {loadingError}
          </p>
        )}
      </section>
    </div>
  )
}
