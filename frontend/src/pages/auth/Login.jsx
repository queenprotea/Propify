import { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { authApi } from '../../api/auth'
import Field from '../../components/Field'
import Alert from '../../components/Alert'

export default function Login() {
  const { login, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [sinVerificar, setSinVerificar] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setError(''); setInfo(''); setSinVerificar(false)
    try {
      const user = await login(identifier.trim(), password)
      const dest = location.state?.from || (user?.isAdmin ? '/admin/inmuebles' : '/')
      navigate(dest, { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail || 'No se pudo iniciar sesión. Verifica tus datos.'
      setError(detail)
      if (typeof detail === 'string' && detail.includes('no está verificado')) setSinVerificar(true)
    }
  }

  async function reenviar() {
    setInfo(''); setError('')
    try {
      const r = await authApi.resendVerification(identifier.trim())
      setInfo(r.message || 'Enlace reenviado.')
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo reenviar el enlace.')
    }
  }

  return (
    <div className="auth-outer">
      <div className="auth-card">
        <div className="auth-logo">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="brand-icon">P</span>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)', fontWeight: 700, color: 'var(--p-700)' }}>Propify</span>
          </div>
        </div>

        <h1 className="auth-title">Bienvenido de vuelta</h1>
        <p className="auth-subtitle">Inicia sesión para acceder a tu cuenta</p>

        <Alert type="error">{error}</Alert>
        <Alert type="success">{info}</Alert>

        {sinVerificar && (
          <div style={{ marginBottom: '1rem' }}>
            <button className="btn secondary full" type="button" onClick={reenviar}>
              Reenviar enlace de verificación
            </button>
          </div>
        )}

        <form onSubmit={onSubmit} noValidate>
          <Field
            label="Correo electrónico o teléfono"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            autoComplete="username"
            required
          />
          <Field
            label="Contraseña"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
          <button className="btn full large" type="submit" disabled={loading}>
            {loading ? 'Ingresando…' : 'Iniciar sesión'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: 'var(--text-sm)', color: 'var(--n-500)' }}>
          ¿No tienes cuenta?{' '}
          <Link to="/registro" style={{ color: 'var(--p-600)', fontWeight: 600 }}>Crear cuenta</Link>
        </p>
      </div>
    </div>
  )
}
