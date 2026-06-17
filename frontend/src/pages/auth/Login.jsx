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
    <div style={{ maxWidth: 420, margin: '0 auto' }}>
      <h1>Iniciar sesión</h1>
      <div className="card">
        <Alert type="error">{error}</Alert>
        <Alert type="success">{info}</Alert>
        {sinVerificar && (
          <p>
            <button className="btn secondary" type="button" onClick={reenviar}>
              Reenviar enlace de verificación
            </button>
          </p>
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
          <button className="btn" type="submit" disabled={loading}>
            {loading ? 'Entrando…' : 'Entrar'}
          </button>
        </form>
      </div>
      <p style={{ marginTop: '1rem' }}>
        ¿No tienes cuenta? <Link to="/registro">Crear cuenta</Link>
      </p>
    </div>
  )
}
