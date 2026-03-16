import React from 'react'
import { Link } from 'react-router-dom'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error) {
    // Keep simple console logging for local debugging.
    console.error('UI error:', error)
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children
    }

    return (
      <div className="min-h-screen flex items-center justify-center px-6" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
        <div className="max-w-md text-center glass-card p-6">
          <h1 className="text-xl font-semibold mb-2">Da co loi giao dien</h1>
          <p className="text-sm mb-5" style={{ color: 'var(--text-muted)' }}>
            Trang hien tai gap su co. Vui long thu tai lai hoac quay ve trang chu.
          </p>
          <Link to="/" className="inline-flex px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-sm">
            Ve trang chu
          </Link>
        </div>
      </div>
    )
  }
}
