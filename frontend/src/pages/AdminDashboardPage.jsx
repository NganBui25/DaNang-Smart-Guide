import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminApi } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { Check, X, Shield, Users, MapPin, Clock } from 'lucide-react'

export default function AdminDashboardPage() {
  const [activeTab, setActiveTab] = useState('places')
  const [places, setPlaces] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { replace: true })
      return
    }
    fetchData()
  }, [isAuthenticated, navigate, activeTab])

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      if (activeTab === 'places') {
        const res = await adminApi.getPlaces('PENDING')
        setPlaces(res.data.results || [])
      } else {
        const res = await adminApi.getUsers()
        setUsers(res.data.results || [])
      }
    } catch (err) {
      if (err.message.includes('403')) {
        setError('Bạn không có quyền truy cập trang này.')
      } else {
        setError(err.message || 'Không thể tải dữ liệu.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (id) => {
    try {
      await adminApi.approvePlace(id)
      setPlaces(places.filter(p => p.id !== id))
    } catch (err) {
      alert(err.message || 'Lỗi khi duyệt.')
    }
  }

  const handleReject = async (id) => {
    const reason = prompt('Lý do từ chối:')
    if (reason === null) return
    try {
      await adminApi.rejectPlace(id, reason)
      setPlaces(places.filter(p => p.id !== id))
    } catch (err) {
      alert(err.message || 'Lỗi khi từ chối.')
    }
  }

  const toggleUser = async (id, currentStatus) => {
    try {
      await adminApi.toggleUserStatus(id, !currentStatus)
      setUsers(users.map(u => u.id === id ? { ...u, is_active: !currentStatus } : u))
    } catch (err) {
      alert(err.message || 'Lỗi khi cập nhật user.')
    }
  }

  if (error && error.includes('quyền')) {
    return (
      <div className="min-h-screen pt-20 flex flex-col items-center justify-center p-6 text-center" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
        <Shield size={48} className="text-red-500 mb-4" />
        <h1 className="text-2xl font-bold mb-2">Truy cập bị từ chối</h1>
        <p className="text-gray-400">{error}</p>
        <button onClick={() => navigate('/')} className="mt-6 px-4 py-2 bg-sky-600 rounded-lg text-white text-sm">Về trang chủ</button>
      </div>
    )
  }

  return (
    <div className="min-h-screen pt-20 px-6 pb-16" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Shield className="text-sky-400" /> Quản trị hệ thống
        </h1>

        <div className="flex gap-2 mb-6 border-b" style={{ borderColor: 'var(--border)' }}>
          <button
            onClick={() => setActiveTab('places')}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'places' ? 'border-sky-400 text-sky-400' : 'border-transparent text-gray-400 hover:text-white'}`}
          >
            <MapPin size={16} /> Duyệt địa điểm
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'users' ? 'border-sky-400 text-sky-400' : 'border-transparent text-gray-400 hover:text-white'}`}
          >
            <Users size={16} /> Quản lý Users
          </button>
        </div>

        {error && <div role="alert" className="mb-4 p-3 rounded bg-red-500/10 text-red-400 border border-red-500/20 text-sm">{error}</div>}

        {loading ? (
          <div className="py-12 text-center text-gray-400 text-sm flex items-center justify-center gap-2">
            <Clock className="animate-spin" size={16} /> Đang tải dữ liệu...
          </div>
        ) : (
          <div>
            {activeTab === 'places' && (
              <div className="space-y-4">
                {places.length === 0 ? (
                  <p className="text-gray-400 text-sm text-center py-8">Không có địa điểm nào đang chờ duyệt.</p>
                ) : (
                  places.map(place => (
                    <div key={place.id} className="glass-card p-4 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-lg">{place.name}</h3>
                        <p className="text-sm text-gray-400 mt-1"><MapPin size={12} className="inline mr-1" />{place.address}</p>
                        {place.description && <p className="text-xs text-gray-500 mt-2 line-clamp-2">{place.description}</p>}
                        <div className="flex gap-2 mt-2">
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400">PENDING</span>
                          {place.category && <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-400">{place.category.name}</span>}
                        </div>
                      </div>
                      <div className="flex md:flex-col gap-2 w-full md:w-32 flex-shrink-0">
                        <button onClick={() => handleApprove(place.id)} className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition-colors">
                          <Check size={14} /> Duyệt
                        </button>
                        <button onClick={() => handleReject(place.id)} className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-semibold rounded-lg transition-colors">
                          <X size={14} /> Từ chối
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {activeTab === 'users' && (
              <div className="glass-card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-black/20 text-gray-400 uppercase text-xs">
                      <tr>
                        <th className="px-4 py-3">Username</th>
                        <th className="px-4 py-3">Vai trò</th>
                        <th className="px-4 py-3">Ngày tham gia</th>
                        <th className="px-4 py-3 text-right">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.length === 0 ? (
                        <tr><td colSpan="4" className="text-center py-8 text-gray-400">Không có người dùng.</td></tr>
                      ) : (
                        users.map(user => (
                          <tr key={user.id} className="border-b last:border-0 border-white/5 hover:bg-white/5 transition-colors">
                            <td className="px-4 py-3 font-medium flex items-center gap-2">
                              <span className={`w-2 h-2 rounded-full ${user.is_active ? 'bg-emerald-400' : 'bg-red-400'}`}></span>
                              {user.username}
                            </td>
                            <td className="px-4 py-3">
                              {user.role === 'admin' ? <span className="text-sky-400 font-semibold text-xs">Admin</span> : <span className="text-gray-400 text-xs">User</span>}
                            </td>
                            <td className="px-4 py-3 text-gray-400 text-xs">
                              {new Date(user.date_joined).toLocaleDateString('vi-VN')}
                            </td>
                            <td className="px-4 py-3 text-right">
                              {user.role !== 'admin' && (
                                <button
                                  onClick={() => toggleUser(user.id, user.is_active)}
                                  className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${user.is_active ? 'bg-red-500/20 text-red-400 hover:bg-red-500/40' : 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/40'}`}
                                >
                                  {user.is_active ? 'Khóa' : 'Mở khóa'}
                                </button>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
