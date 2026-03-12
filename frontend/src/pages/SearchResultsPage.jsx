import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { Map, List, Loader2, SearchX } from 'lucide-react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

import { searchApi, placesApi } from '../services/api'
import PlaceCard from '../components/PlaceCard'
import SearchBar from '../components/SearchBar'

// Fix leaflet default marker icon
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

// Custom blue marker cho selected place
const selectedIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
})

function FlyToPlace({ place }) {
    const map = useMap()
    useEffect(() => {
        if (place?.lat && place?.lng) {
            map.flyTo([place.lat, place.lng], 16, { duration: 1.2 })
        }
    }, [place, map])
    return null
}

export default function SearchResultsPage() {
    const [searchParams] = useSearchParams()
    const query = searchParams.get('q') || ''

    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [selectedPlace, setSelectedPlace] = useState(null)
    const [viewMode, setViewMode] = useState('split') // 'split' | 'list' | 'map'

    useEffect(() => {
        if (!query) return
        setLoading(true)
        setError(null)

        const fetchResults = query
            ? searchApi.semantic(query, 20)
            : placesApi.list({ page_size: 20 })

        fetchResults
            .then(res => {
                const data = res.data
                const items = data.results || []
                setResults(items)
                if (items.length > 0) setSelectedPlace(items[0])
            })
            .catch(() => setError('Không thể kết nối tới backend. Hãy đảm bảo server đang chạy.'))
            .finally(() => setLoading(false))
    }, [query])

    // Map center mặc định = Đà Nẵng
    const mapCenter = selectedPlace?.lat
        ? [selectedPlace.lat, selectedPlace.lng]
        : [16.0544, 108.2022]

    const placeMarkers = results.filter(p => p.lat && p.lng)

    return (
        <div className="flex flex-col h-screen pt-14 bg-gray-950">
            {/* Top Search Bar */}
            <div className="px-6 py-3 border-b border-white/8 bg-gray-900/60 backdrop-blur">
                <div className="max-w-5xl mx-auto flex items-center gap-4">
                    <div className="flex-1">
                        <SearchBar initialValue={query} />
                    </div>
                    {/* View Toggle */}
                    <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
                        {[
                            { key: 'list', icon: <List size={16} />, label: 'Danh sách' },
                            { key: 'split', icon: <><List size={14} /><Map size={14} /></>, label: 'Split' },
                            { key: 'map', icon: <Map size={16} />, label: 'Bản đồ' },
                        ].map(({ key, icon, label }) => (
                            <button
                                key={key}
                                onClick={() => setViewMode(key)}
                                title={label}
                                className={`p-2 rounded-md transition-all text-sm flex items-center gap-1
                  ${viewMode === key
                                        ? 'bg-sky-600 text-white'
                                        : 'text-gray-400 hover:text-white'
                                    }`}
                            >
                                {icon}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Result count */}
            {!loading && query && (
                <div className="px-6 py-2 text-xs text-gray-500 max-w-5xl mx-auto w-full">
                    {results.length > 0
                        ? <span>Tìm thấy <span className="text-sky-400 font-semibold">{results.length}</span> địa điểm phù hợp với "<span className="text-white">{query}</span>"</span>
                        : <span>Không tìm thấy kết quả nào.</span>
                    }
                </div>
            )}

            {/* Main Content: Split/List/Map */}
            <div className="flex flex-1 overflow-hidden">

                {/* === Place List === */}
                {(viewMode === 'list' || viewMode === 'split') && (
                    <div className={`
            ${viewMode === 'split' ? 'w-[420px] flex-shrink-0' : 'flex-1'}
            overflow-y-auto p-4 border-r border-white/8
          `}>
                        {loading && (
                            <div className="flex items-center justify-center py-20 gap-3 text-gray-400">
                                <Loader2 size={20} className="animate-spin" />
                                <span className="text-sm">Đang tìm kiếm...</span>
                            </div>
                        )}
                        {error && (
                            <div className="text-center py-20 text-red-400 text-sm">{error}</div>
                        )}
                        {!loading && results.length === 0 && !error && query && (
                            <div className="flex flex-col items-center py-20 text-gray-500 gap-3">
                                <SearchX size={40} />
                                <p className="text-sm">Thử từ khoá khác nhé!</p>
                            </div>
                        )}
                        <div className={viewMode === 'split' ? 'flex flex-col gap-3' : 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'}>
                            {results.map((place, i) => (
                                <div
                                    key={place.id}
                                    onClick={() => setSelectedPlace(place)}
                                    className={`cursor-pointer rounded-xl ring-2 transition-all duration-200
                    ${selectedPlace?.id === place.id && viewMode === 'split'
                                            ? 'ring-sky-500' : 'ring-transparent'}`}
                                    style={{ animationDelay: `${i * 40}ms` }}
                                >
                                    {viewMode === 'split' ? (
                                        // Compact card cho split view
                                        <div className="glass-card p-3 flex gap-3 hover:border-sky-500/40 transition-all">
                                            <div className="w-16 h-16 rounded-lg overflow-hidden bg-gray-800 flex-shrink-0">
                                                {place.image_path
                                                    ? <img src={place.image_path} alt={place.name} className="w-full h-full object-cover" onError={e => e.target.style.display = 'none'} />
                                                    : <div className="w-full h-full bg-gradient-to-br from-gray-700 to-gray-800" />
                                                }
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium line-clamp-1">{place.name}</p>
                                                <p className="text-xs text-gray-400 line-clamp-1 mt-0.5">{place.address || 'Đà Nẵng'}</p>
                                                {place.category && (
                                                    <span className="text-xs text-sky-400">{place.category.name}</span>
                                                )}
                                                {place.ai_score !== undefined && (
                                                    <span className="ml-2 text-xs text-gray-500">AI ✦</span>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <PlaceCard place={place} score={place.ai_score} />
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* === Map === */}
                {(viewMode === 'map' || viewMode === 'split') && (
                    <div className="flex-1 relative">
                        <MapContainer
                            center={mapCenter}
                            zoom={13}
                            className="w-full h-full"
                            zoomControl={false}
                        >
                            <TileLayer
                                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                                attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                            />
                            <FlyToPlace place={selectedPlace} />
                            {placeMarkers.map(place => (
                                <Marker
                                    key={place.id}
                                    position={[place.lat, place.lng]}
                                    icon={selectedPlace?.id === place.id ? selectedIcon : new L.Icon.Default()}
                                    eventHandlers={{ click: () => setSelectedPlace(place) }}
                                >
                                    <Popup>
                                        <div className="text-sm font-medium">{place.name}</div>
                                        <div className="text-xs text-gray-400 mt-1">{place.address}</div>
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
