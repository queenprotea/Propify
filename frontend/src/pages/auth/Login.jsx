import { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import Field from '../../components/Field'
import Alert from '../../components/Alert'

export default function Login() {
  const { login, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      const user = await login(identifier.trim(), password)
      const dest = location.state?.from || (user?.isAdmin ? '/admin' : '/')
      navigate(dest, { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo iniciar sesión. Verifica tus datos.')
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: '0 auto' }}>
      <h1>Iniciar sesión</h1>
      <div className="card">
        <Alert type="error">{error}</Alert>
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
