import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { placesApi } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

const INITIAL_FORM = {
  name: '',
  description: '',
  address: '',
  lat: '',
  lng: '',
}

export default function SubmitPlacePage() {
  const [form, setForm] = useState(INITIAL_FORM)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { replace: true, state: { from: location.pathname } })
    }
  }, [isAuthenticated, navigate, location.pathname])

  const update = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const validate = () => {
    if (!form.name.trim() || !form.address.trim()) {
      return 'Ten dia diem va dia chi la bat buoc.'
    }

    if (form.lat && Number.isNaN(Number(form.lat))) {
      return 'Toa do lat khong hop le.'
    }

    if (form.lng && Number.isNaN(Number(form.lng))) {
      return 'Toa do lng khong hop le.'
    }

    return ''
  }

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }

    setLoading(true)
    try {
      await placesApi.submit({
        name: form.name.trim(),
        address: form.address.trim(),
        description: form.description.trim(),
        lat: form.lat === '' ? null : Number(form.lat),
        lng: form.lng === '' ? null : Number(form.lng),
      })
      setSuccess('Gui thanh cong. Dia diem cua ban se o trang thai PENDING cho den khi duoc duyet.')
      setForm(INITIAL_FORM)
    } catch (err) {
      setError(err.message || 'Khong the gui dia diem luc nay.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen pt-20 px-6 pb-16" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-2">Dong gop dia diem moi</h1>
        <p className="text-sm mb-6" style={{ color: 'var(--text-muted)' }}>
          Cung cap thong tin co ban. Sau khi gui, dia diem se duoc danh dau PENDING va can duoc duyet.
        </p>

        <div className="glass-card p-5">
          {error && <div role="alert" className="mb-4 text-sm text-red-400">{error}</div>}
          {success && <div role="status" className="mb-4 text-sm text-emerald-400">{success}</div>}

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-xs mb-1">Ten dia diem *</label>
              <input id="name" value={form.name} onChange={(e) => update('name', e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bg-transparent"
                style={{ borderColor: 'var(--border)' }} />
            </div>

            <div>
              <label htmlFor="address" className="block text-xs mb-1">Dia chi *</label>
              <input id="address" value={form.address} onChange={(e) => update('address', e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bg-transparent"
                style={{ borderColor: 'var(--border)' }} />
            </div>

            <div>
              <label htmlFor="description" className="block text-xs mb-1">Mo ta</label>
              <textarea id="description" rows={4} value={form.description} onChange={(e) => update('description', e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bg-transparent"
                style={{ borderColor: 'var(--border)' }} />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label htmlFor="lat" className="block text-xs mb-1">Lat</label>
                <input id="lat" value={form.lat} onChange={(e) => update('lat', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border bg-transparent"
                  style={{ borderColor: 'var(--border)' }} />
              </div>
              <div>
                <label htmlFor="lng" className="block text-xs mb-1">Lng</label>
                <input id="lng" value={form.lng} onChange={(e) => update('lng', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border bg-transparent"
                  style={{ borderColor: 'var(--border)' }} />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={loading}
                className="px-4 py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-60 text-white text-sm font-medium">
                {loading ? 'Dang gui...' : 'Gui dia diem'}
              </button>
              <button type="button" onClick={() => navigate(-1)}
                className="px-4 py-2.5 rounded-lg border text-sm"
                style={{ borderColor: 'var(--border)' }}>
                Quay lai
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
