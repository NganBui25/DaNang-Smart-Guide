import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { ArrowLeft, MapPin, Star, Bookmark, ExternalLink, Loader2 } from 'lucide-react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { placesApi } from '../services/api'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'
import { resolvePlaceImage } from '../utils/media'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

export default function PlaceDetailPage() {
    const { id } = useParams()
    const navigate = useNavigate()
    const location = useLocation()
    const { theme } = useTheme()
    const { isAuthenticated } = useAuth()
    const [place, setPlace] = useState(null)
    const [reviews, setReviews] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [bookmarkState, setBookmarkState] = useState(false)
    const [bookmarkLoading, setBookmarkLoading] = useState(false)
    const [bookmarkMessage, setBookmarkMessage] = useState('')
    const [reviewMessage, setReviewMessage] = useState('')
    const [reviewForm, setReviewForm] = useState({ rating: 5, comment: '' })

    const tileUrl = theme === 'dark'
        ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'

    useEffect(() => {
        setLoading(true)
        Promise.all([
            placesApi.detail(id),
            placesApi.reviews(id)
        ])
            .then(([placeRes, reviewsRes]) => {
                setPlace(placeRes.data)
                setReviews(reviewsRes.data || [])
                setError('')
            })
            .catch((err) => {
                setError(err.message || 'Khong the tai thong tin dia diem.')
            })
            .finally(() => setLoading(false))
    }, [id])

    const handleBookmark = async () => {
        if (!isAuthenticated) {
            navigate('/login', { state: { from: location.pathname } })
            return
        }

        setBookmarkLoading(true)
        setBookmarkMessage('')
        try {
            const resp = await placesApi.bookmark(id)
            const nextState = Boolean(resp?.data?.bookmarked)
            setBookmarkState(nextState)
            setBookmarkMessage(nextState ? 'Da luu vao danh sach yeu thich.' : 'Da bo luu dia diem.')
        } catch (err) {
            setBookmarkMessage(err.message || 'Khong the cap nhat bookmark.')
        } finally {
            setBookmarkLoading(false)
        }
    }

    const submitReview = async (e) => {
        e.preventDefault()
        setReviewMessage('')
        if (!isAuthenticated) {
            navigate('/login', { state: { from: location.pathname } })
            return
        }

        if (!reviewForm.comment.trim()) {
            setReviewMessage('Vui long nhap noi dung danh gia.')
            return
        }

        try {
            await placesApi.submitReview({
                place: id,
                rating: Number(reviewForm.rating),
                comment: reviewForm.comment.trim(),
            })
            const reviewsRes = await placesApi.reviews(id)
            setReviews(reviewsRes.data || [])
            setReviewForm({ rating: 5, comment: '' })
            setReviewMessage('Danh gia da duoc gui thanh cong.')
        } catch (err) {
            setReviewMessage(err.message || 'Khong the gui danh gia.')
        }
    }

    const imageSrc = resolvePlaceImage(place)

    if (loading) return (
        <div className="min-h-screen pt-20 flex items-center justify-center" style={{ background: 'var(--bg)' }}>
            <Loader2 size={32} className="animate-spin text-sky-400" />
        </div>
    )

    if (!place) return (
        <div className="min-h-screen pt-20 flex flex-col items-center justify-center gap-4" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
            <p className="text-lg">Không tìm thấy địa điểm này.</p>
            {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
            <Link to="/" className="text-sky-400 hover:underline text-sm">← Về trang chủ</Link>
        </div>
    )

    return (
        <div className="min-h-screen pt-14" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
            {/* Back button */}
            <div className="px-6 py-3 border-b" style={{ borderColor: 'var(--border)', background: 'var(--glass-bg)', backdropFilter: 'blur(12px)' }}>
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-2 text-sm hover:text-sky-400 transition-colors"
                    style={{ color: 'var(--text-muted)' }}
                >
                    <ArrowLeft size={16} /> Quay lại
                </button>
            </div>

            <div className="max-w-5xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* === Left Column: Info === */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Hero image */}
                    <div className="rounded-2xl overflow-hidden h-64 relative" style={{ background: 'var(--surface-2)' }}>
                        {imageSrc ? (
                            <img src={imageSrc} alt={place.name} loading="lazy" className="w-full h-full object-cover"
                                onError={e => e.target.style.display = 'none'} />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center">
                                <MapPin size={48} style={{ color: 'var(--text-muted)' }} />
                            </div>
                        )}
                        {place.is_hidden_gem && (
                            <span className="absolute top-3 left-3 px-3 py-1 bg-amber-500 text-black text-xs font-bold rounded-full">
                                ✦ Hidden Gem
                            </span>
                        )}
                    </div>

                    {/* Name + Category */}
                    <div>
                        <div className="flex items-start justify-between gap-4">
                            <h1 className="text-2xl font-bold">{place.name}</h1>
                            {place.category && (
                                <span className="px-3 py-1 text-xs font-medium rounded-full bg-sky-600/20 text-sky-400 flex-shrink-0">
                                    {place.category.name}
                                </span>
                            )}
                        </div>
                        {place.address && (
                            <div className="flex items-center gap-2 mt-2" style={{ color: 'var(--text-muted)' }}>
                                <MapPin size={14} />
                                <span className="text-sm">{place.address}</span>
                            </div>
                        )}
                    </div>

                    {/* Tags */}
                    {place.tags?.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                            {place.tags.map(tag => (
                                <span key={tag.id} className="px-3 py-1 text-sm rounded-full"
                                    style={{ background: 'var(--surface-2)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                                    #{tag.name}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Description */}
                    {place.description && (
                        <div className="glass-card p-4">
                            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>{place.description}</p>
                        </div>
                    )}

                    {/* Reviews */}
                    <div>
                        <h2 className="text-lg font-semibold mb-4">Đánh giá ({reviews.length})</h2>
                        {error && <p role="alert" className="text-sm mb-2 text-red-400">{error}</p>}
                        {reviews.length === 0
                            ? <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Chưa có đánh giá nào.</p>
                            : (
                                <div className="space-y-3">
                                    {reviews.map(r => (
                                        <div key={r.id} className="glass-card p-4">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-medium">{r.reviewer_name}</span>
                                                {r.rating && (
                                                    <span className="flex items-center gap-1 text-xs text-amber-400">
                                                        <Star size={12} fill="currentColor" /> {r.rating}
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{r.comment}</p>
                                        </div>
                                    ))}
                                </div>
                            )
                        }

                        <form onSubmit={submitReview} className="glass-card p-4 mt-4 space-y-3">
                            <p className="text-sm font-medium">Gui danh gia</p>
                            <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
                                <div className="sm:col-span-1">
                                    <label htmlFor="rating" className="text-xs block mb-1" style={{ color: 'var(--text-muted)' }}>Rating</label>
                                    <input
                                        id="rating"
                                        type="number"
                                        min="1"
                                        max="5"
                                        value={reviewForm.rating}
                                        onChange={(e) => setReviewForm((prev) => ({ ...prev, rating: e.target.value }))}
                                        className="w-full px-3 py-2 rounded-lg border bg-transparent"
                                        style={{ borderColor: 'var(--border)' }}
                                    />
                                </div>
                                <div className="sm:col-span-3">
                                    <label htmlFor="comment" className="text-xs block mb-1" style={{ color: 'var(--text-muted)' }}>Noi dung</label>
                                    <textarea
                                        id="comment"
                                        rows={3}
                                        value={reviewForm.comment}
                                        onChange={(e) => setReviewForm((prev) => ({ ...prev, comment: e.target.value }))}
                                        className="w-full px-3 py-2 rounded-lg border bg-transparent"
                                        style={{ borderColor: 'var(--border)' }}
                                    />
                                </div>
                            </div>
                            {reviewMessage && (
                                <p role="status" className="text-xs" style={{ color: reviewMessage.includes('thanh cong') ? '#34d399' : '#f87171' }}>
                                    {reviewMessage}
                                </p>
                            )}
                            <button type="submit" className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-sm">
                                Gui review
                            </button>
                        </form>
                    </div>
                </div>

                {/* === Right Column: Map + Actions === */}
                <div className="space-y-4">
                    {/* Map */}
                    {place.lat && place.lng && (
                        <div className="glass-card overflow-hidden" style={{ height: '260px' }}>
                            <MapContainer center={[place.lat, place.lng]} zoom={16} className="w-full h-full" zoomControl={false}>
                                <TileLayer url={tileUrl} />
                                <Marker position={[place.lat, place.lng]}>
                                    <Popup>{place.name}</Popup>
                                </Marker>
                            </MapContainer>
                        </div>
                    )}

                    {/* Action buttons */}
                    <div className="glass-card p-4 space-y-3">
                        {place.lat && place.lng && (
                            <a
                                href={`https://www.google.com/maps/dir/?api=1&destination=${place.lat},${place.lng}`}
                                target="_blank" rel="noopener noreferrer"
                                className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium transition-colors"
                            >
                                <ExternalLink size={15} /> Chỉ đường Google Maps
                            </a>
                        )}
                        <button
                            onClick={handleBookmark}
                            disabled={bookmarkLoading}
                            aria-label="Luu dia diem"
                            className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl text-sm font-medium transition-all disabled:opacity-60"
                            style={{ background: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border)' }}>
                            <Bookmark size={15} /> {bookmarkLoading ? 'Dang cap nhat...' : (bookmarkState ? 'Da luu dia diem' : 'Luu dia diem')}
                        </button>
                        {bookmarkMessage && (
                            <p role="status" className="text-xs" style={{ color: bookmarkMessage.includes('Da') ? '#34d399' : '#f87171' }}>
                                {bookmarkMessage}
                            </p>
                        )}
                    </div>

                    {/* Coords */}
                    {place.lat && place.lng && (
                        <div className="text-xs text-center" style={{ color: 'var(--text-muted)' }}>
                            {Number(place.lat).toFixed(5)}, {Number(place.lng).toFixed(5)}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
