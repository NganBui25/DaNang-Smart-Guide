import { Link } from 'react-router-dom'
import { MapPin, Gem } from 'lucide-react'
import { resolvePlaceImage } from '../utils/media'

export default function PlaceCard({ place, score }) {
    const imageSrc = resolvePlaceImage(place)

    return (
        <Link
            to={`/places/${place.id}`}
            aria-label={`Xem chi tiet ${place.name}`}
            className="glass-card group block overflow-hidden transition-all duration-300 hover:-translate-y-1"
        >
            {/* Image */}
            <div className="relative h-44 overflow-hidden" style={{ background: 'var(--surface-2)' }}>
                {imageSrc ? (
                    <img
                        src={imageSrc}
                        alt={place.name}
                        loading="lazy"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        onError={(e) => { e.target.style.display = 'none' }}
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center">
                        <MapPin size={40} style={{ color: 'var(--text-muted)' }} />
                    </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/45 via-transparent to-transparent pointer-events-none" />
                {/* Badges */}
                <div className="absolute top-2 left-2 flex gap-1.5">
                    {place.is_hidden_gem && (
                        <span className="flex items-center gap-1 px-2 py-0.5 bg-amber-500/90 backdrop-blur text-xs font-semibold rounded-full text-black">
                            <Gem size={10} /> Hidden Gem
                        </span>
                    )}
                    {place.category && (
                        <span className="px-2 py-0.5 bg-sky-600/90 backdrop-blur text-xs font-medium rounded-full text-white">
                            {place.category.name}
                        </span>
                    )}
                </div>
                {/* AI Score */}
                {score !== undefined && (
                    <div className="absolute top-2 right-2 px-2 py-0.5 bg-black/60 backdrop-blur rounded-full text-xs text-sky-400 font-mono">
                        AI ✦
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="p-4">
                <h3 className="font-semibold text-sm leading-tight line-clamp-2 group-hover:text-sky-400 transition-colors" style={{ color: 'var(--text)' }}>
                    {place.name}
                </h3>
                <div className="flex items-center gap-1 mt-2" style={{ color: 'var(--text-muted)' }}>
                    <MapPin size={12} className="flex-shrink-0" />
                    <span className="text-xs line-clamp-1">{place.address || 'Đà Nẵng'}</span>
                </div>
                {/* Tags */}
                {place.tags?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                        {place.tags.slice(0, 3).map(tag => (
                            <span key={tag.id} className="px-2 py-0.5 text-xs rounded-full" style={{ background: 'var(--surface-2)', color: 'var(--text-muted)' }}>
                                #{tag.name}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </Link>
    )
}
