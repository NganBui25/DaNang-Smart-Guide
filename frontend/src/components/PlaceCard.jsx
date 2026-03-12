import { Link } from 'react-router-dom'
import { MapPin, Star, Gem } from 'lucide-react'

export default function PlaceCard({ place, score }) {
    const stars = Math.round((place.rating || 4.0) * 10) / 10

    return (
        <Link
            to={`/places/${place.id}`}
            className="glass-card group block overflow-hidden hover:border-sky-500/40 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-sky-900/20"
        >
            {/* Image */}
            <div className="relative h-44 bg-gray-800 overflow-hidden">
                {place.image_path ? (
                    <img
                        src={place.image_path}
                        alt={place.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        onError={(e) => { e.target.style.display = 'none' }}
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900">
                        <MapPin size={40} className="text-gray-600" />
                    </div>
                )}
                {/* Badges */}
                <div className="absolute top-2 left-2 flex gap-1.5">
                    {place.is_hidden_gem && (
                        <span className="flex items-center gap-1 px-2 py-0.5 bg-amber-500/90 backdrop-blur text-xs font-semibold rounded-full text-black">
                            <Gem size={10} /> Hidden Gem
                        </span>
                    )}
                    {place.category && (
                        <span className="px-2 py-0.5 bg-sky-600/90 backdrop-blur text-xs font-medium rounded-full">
                            {place.category.name}
                        </span>
                    )}
                </div>
                {/* AI Score if present */}
                {score !== undefined && (
                    <div className="absolute top-2 right-2 px-2 py-0.5 bg-black/60 backdrop-blur rounded-full text-xs text-sky-400 font-mono">
                        AI ✦
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="p-4">
                <h3 className="font-semibold text-sm leading-tight line-clamp-2 group-hover:text-sky-400 transition-colors">
                    {place.name}
                </h3>
                <div className="flex items-center gap-1 mt-2 text-gray-400">
                    <MapPin size={12} className="flex-shrink-0" />
                    <span className="text-xs line-clamp-1">{place.address || 'Đà Nẵng'}</span>
                </div>
                {/* Tags */}
                {place.tags?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                        {place.tags.slice(0, 3).map(tag => (
                            <span key={tag.id} className="px-2 py-0.5 bg-gray-700/60 text-xs rounded-full text-gray-300">
                                #{tag.name}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </Link>
    )
}
