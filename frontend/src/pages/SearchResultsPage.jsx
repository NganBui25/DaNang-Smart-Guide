import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { Map, List, Loader2, SearchX, X, ArrowRight, MapPin, ExternalLink } from 'lucide-react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

import { searchApi, placesApi } from '../services/api'
import PlaceCard from '../components/PlaceCard'
import SearchBar from '../components/SearchBar'
import { useTheme } from '../contexts/ThemeContext'
import { resolvePlaceImage } from '../utils/media'

// Fix leaflet icons
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

const selectedIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
})

function FlyToPlace({ place }) {
    const map = useMap()
    useEffect(() => {
        if (place?.lat && place?.lng) map.flyTo([place.lat, place.lng], 16, { duration: 1 })
    }, [place, map])
    return null
}

// ===== Compact Card for list panel =====
function CompactCard({ place, isSelected, onClick }) {
    const imageSrc = resolvePlaceImage(place)

    return (
        <div
            onClick={onClick}
            className={`cursor-pointer rounded-xl p-3 flex gap-3 transition-all duration-200 border
        ${isSelected ? 'border-sky-500 shadow-lg shadow-sky-900/20' : 'hover:border-sky-500/30'}
      `}
            style={{
                background: 'var(--glass-bg)',
                borderColor: isSelected ? '#0ea5e9' : 'var(--glass-border)',
                backdropFilter: 'blur(12px)',
            }}
        >
            <div className="w-16 h-16 rounded-lg overflow-hidden flex-shrink-0" style={{ background: 'var(--surface-2)' }}>
                {imageSrc
                    ? <img src={imageSrc} loading="lazy" alt={place.name} className="w-full h-full object-cover" onError={e => e.target.style.display = 'none'} />
                    : <div className="w-full h-full" style={{ background: 'var(--surface-2)' }} />
                }
            </div>
            <div className="flex-1 min-w-0">
                <p className="text-sm font-medium line-clamp-1" style={{ color: 'var(--text)' }}>{place.name}</p>
                <p className="text-xs line-clamp-1 mt-0.5" style={{ color: 'var(--text-muted)' }}>{place.address || 'Đà Nẵng'}</p>
                {place.category && <span className="text-xs text-sky-400">{place.category.name}</span>}
            </div>
        </div>
    )
}

// ===== Inline Detail Panel =====
function DetailPanel({ place, onClose }) {
    if (!place) return null
    const imageSrc = resolvePlaceImage(place)

    return (
        <div className="animate-slide-right h-full overflow-y-auto flex flex-col" style={{ background: 'var(--surface)', borderLeft: '1px solid var(--border)' }}>
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b sticky top-0 z-10" style={{ borderColor: 'var(--border)', background: 'var(--glass-bg)', backdropFilter: 'blur(12px)' }}>
                <span className="font-semibold text-sm line-clamp-1" style={{ color: 'var(--text)' }}>{place.name}</span>
                <button aria-label="Dong panel chi tiet" onClick={onClose} className="p-1.5 rounded-lg hover:bg-red-500/20 text-red-400 transition-colors">
                    <X size={16} />
                </button>
            </div>

            {/* Image */}
            <div className="h-44 relative overflow-hidden flex-shrink-0" style={{ background: 'var(--surface-2)' }}>
                {imageSrc
                    ? <img src={imageSrc} loading="lazy" alt={place.name} className="w-full h-full object-cover" onError={e => e.target.style.display = 'none'} />
                    : <div className="w-full h-full flex items-center justify-center"><MapPin size={32} style={{ color: 'var(--text-muted)' }} /></div>
                }
                {place.is_hidden_gem && (
                    <span className="absolute top-2 left-2 px-2 py-0.5 bg-amber-500 text-black text-xs font-bold rounded-full">✦ Hidden Gem</span>
                )}
            </div>

            {/* Content */}
            <div className="p-4 space-y-4 flex-1">
                {place.category && (
                    <span className="inline-block px-3 py-0.5 text-xs rounded-full bg-sky-600/20 text-sky-400">{place.category.name}</span>
                )}

                {place.address && (
                    <div className="flex items-start gap-2">
                        <MapPin size={14} className="mt-0.5 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
                        <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{place.address}</span>
                    </div>
                )}

                {place.tags?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                        {place.tags.map(t => (
                            <span key={t.id} className="px-2 py-0.5 text-xs rounded-full" style={{ background: 'var(--surface-2)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                                #{t.name}
                            </span>
                        ))}
                    </div>
                )}

                {/* Actions */}
                <div className="space-y-2 pt-2">
                    <Link
                        to={`/places/${place.id}`}
                        className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium transition-colors"
                    >
                        Xem chi tiết đầy đủ <ArrowRight size={14} />
                    </Link>

                    {place.lat && place.lng && (
                        <a
                            href={`https://www.google.com/maps/dir/?api=1&destination=${place.lat},${place.lng}`}
                            target="_blank" rel="noopener noreferrer"
                            className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl text-sm font-medium transition-all"
                            style={{ background: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border)' }}
                        >
                            <ExternalLink size={14} /> Chỉ đường
                        </a>
                    )}
                </div>
            </div>
        </div>
    )
}

// ===== Main Component =====
export default function SearchResultsPage() {
    const [searchParams] = useSearchParams()
    const query = searchParams.get('q') || ''
    //Nbui bổ sung lấy thêm tọa độ User hiện tại
    const lat = searchParams.get('lat');
    const lng = searchParams.get('lng');

    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [selectedPlace, setSelectedPlace] = useState(null)
    const [showDetail, setShowDetail] = useState(false)
    const [viewMode, setViewMode] = useState(() => (window.innerWidth < 768 ? 'list' : 'split'))
    const [isMobile, setIsMobile] = useState(() => window.innerWidth < 768)
    const { theme } = useTheme()

    useEffect(() => {
        const onResize = () => {
            const mobile = window.innerWidth < 768
            setIsMobile(mobile)
            if (mobile && viewMode === 'split') {
                setViewMode('list')
            }
        }
        window.addEventListener('resize', onResize)
        return () => window.removeEventListener('resize', onResize)
    }, [viewMode])

    useEffect(() => {
        if (!query) {
            placesApi.list({ page_size: 30 })
                .then(r => setResults(r.data.results || []))
                .catch((err) => setError(err.message || 'Khong the ket noi den backend.'))
            return
        }
        setLoading(true)
        setError(null)
        setShowDetail(false)
        //Nbui có sửa xí ở đây thêm lat,lng (tọa độ user) để gửi về BE
        const userLat = lat ? parseFloat(lat) : null;
        const userLng = lng ? parseFloat(lng) : null;
        searchApi.semantic(query, 20,userLat, userLng)
            .then(res => {
                const items = res.data.results || []
                setResults(items)
                if (items.length > 0) setSelectedPlace(items[0])
            })
            .catch((err) => setError(err.message || 'Khong the ket noi den backend.'))
            .finally(() => setLoading(false))
    }, [query,lat, lng])

    const handleSelectPlace = (place) => {
        setSelectedPlace(place)
        setShowDetail(true)
    }

    const mapCenter = selectedPlace?.lat ? [selectedPlace.lat, selectedPlace.lng] : [16.0544, 108.2022]
    const placeMarkers = results.filter(p => p.lat && p.lng)

    const tileUrl = theme === 'dark'
        ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'

    return (
        <div className="flex flex-col h-screen pt-14" style={{ background: 'var(--bg)' }}>
            {/* Top Bar */}
            <div className="px-4 py-2.5 border-b backdrop-blur" style={{ borderColor: 'var(--border)', background: 'var(--glass-bg)' }}>
                <div className="max-w-6xl mx-auto flex items-center gap-4">
                    <div className="flex-1"><SearchBar initialValue={query} /></div>
                    {/* View toggle */}
                    <div className="flex items-center gap-1 rounded-lg p-1" style={{ background: 'var(--surface-2)' }}>
                        {[
                            { key: 'list', icon: <List size={15} />, label: 'Danh sách' },
                            { key: 'split', icon: <span className="flex gap-0.5"><List size={13} /><Map size={13} /></span>, label: 'Split', hidden: isMobile },
                            { key: 'map', icon: <Map size={15} />, label: 'Bản đồ' },
                        ].filter((item) => !item.hidden).map(({ key, icon, label }) => (
                            <button key={key} onClick={() => setViewMode(key)} title={label}
                                aria-label={`Che do ${label}`}
                                className={`px-2.5 py-1.5 rounded-md transition-all text-xs flex items-center gap-1
                  ${viewMode === key ? 'bg-sky-600 text-white' : 'text-gray-400 hover:text-white'}`}>
                                {icon}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Count bar */}
            {!loading && query && (
                <div className="px-6 py-1.5 text-xs" style={{ color: 'var(--text-muted)', background: 'var(--surface)', borderBottom: '1px solid var(--border)' }}>
                    {results.length > 0
                        ? <>Tìm thấy <span className="text-sky-400 font-semibold">{results.length}</span> địa điểm cho "<span style={{ color: 'var(--text)' }}>{query}</span>"</>
                        : 'Không tìm thấy kết quả nào.'}
                </div>
            )}

            {/* Content */}
            <div className="flex flex-1 overflow-hidden">

                {/* List Panel */}
                {(viewMode === 'list' || viewMode === 'split') && (
                    <div className={`${viewMode === 'split' ? (showDetail ? 'w-56' : 'w-80') : 'flex-1'} ${isMobile ? 'w-full' : ''} overflow-y-auto border-r flex-shrink-0 transition-all duration-300`}
                        style={{ borderColor: 'var(--border)' }}>

                        {loading && <div role="status" aria-live="polite" className="flex items-center justify-center py-20 gap-3" style={{ color: 'var(--text-muted)' }}><Loader2 size={20} className="animate-spin" /><span className="text-sm">Dang tim...</span></div>}
                        {error && <div role="alert" className="text-center py-20 text-red-400 text-sm px-4">{error}</div>}
                        {!loading && results.length === 0 && !error && query && (
                            <div className="flex flex-col items-center py-20 gap-3" style={{ color: 'var(--text-muted)' }}>
                                <SearchX size={36} /><p className="text-sm">Thu tu khoa khac hoac bo dau tieng Viet.</p>
                            </div>
                        )}

                        <div className={viewMode === 'list' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4' : 'flex flex-col gap-2 p-3'}>
                            {results.map((place) => (
                                viewMode === 'list'
                                    ? <PlaceCard key={place.id} place={place} score={place.ai_score} />
                                    : <CompactCard key={place.id} place={place} isSelected={selectedPlace?.id === place.id} onClick={() => handleSelectPlace(place)} />
                            ))}
                        </div>
                    </div>
                )}

                {/* Detail Panel (slide-in) */}
                {viewMode === 'split' && showDetail && (
                    <div className="w-80 flex-shrink-0 flex flex-col overflow-hidden transition-all duration-300">
                        <DetailPanel place={selectedPlace} onClose={() => setShowDetail(false)} />
                    </div>
                )}

                {/* Map */}
                {(viewMode === 'map' || (viewMode === 'split' && !isMobile)) && (
                    <div className="flex-1 relative">
                        <MapContainer center={mapCenter} zoom={13} className="w-full h-full" zoomControl={true}>
                            <TileLayer url={tileUrl} attribution='&copy; CARTO' />
                            <FlyToPlace place={selectedPlace} />
                            {placeMarkers.map(place => (
                                <Marker
                                    key={place.id}
                                    position={[place.lat, place.lng]}
                                    icon={selectedPlace?.id === place.id ? selectedIcon : new L.Icon.Default()}
                                    eventHandlers={{ click: () => handleSelectPlace(place) }}
                                >
                                    <Popup>
                                        <div>
                                            <p className="font-semibold text-sm">{place.name}</p>
                                            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{place.address}</p>
                                            <Link to={`/places/${place.id}`} className="text-xs text-sky-400 hover:underline mt-1 inline-block">
                                                Xem chi tiết →
                                            </Link>
                                        </div>
                                    </Popup>
                                </Marker>
                            ))}
                        </MapContainer>
                    </div>
                )}
            </div>
        </div>
    )
}
