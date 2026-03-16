import { createContext, useContext, useMemo, useState } from 'react'
import { authApi } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem('access_token') || '')
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem('refresh_token') || '')

  const isAuthenticated = Boolean(accessToken)

  const login = async ({ username, password }) => {
    const resp = await authApi.login({ username, password })
    const access = resp?.data?.access || ''
    const refresh = resp?.data?.refresh || ''
    if (!access || !refresh) {
      throw new Error('Dang nhap that bai.')
    }
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    setAccessToken(access)
    setRefreshToken(refresh)
    return true
  }

  const register = async ({ username, email, password }) => {
    await authApi.register({ username, email, password })
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setAccessToken('')
    setRefreshToken('')
  }

  const value = useMemo(() => ({
    isAuthenticated,
    accessToken,
    refreshToken,
    login,
    register,
    logout,
  }), [isAuthenticated, accessToken, refreshToken])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
