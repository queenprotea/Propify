import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { authApi } from '../../api/auth'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

export default function VerifyEmail() {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [estado, setEstado] = useState('verificando')
  const [mensaje, setMensaje] = useState('')

  useEffect(() => {
    if (!token) {
      setEstado('error')
      setMensaje('Falta el token de verificación en el enlace.')
      return
    }
    let activo = true
    authApi.verifyEmail(token)
      .then((r) => { if (activo) { setEstado('ok'); setMensaje(r.message) } })
      .catch((err) => {
        if (activo) {
          setEstado('error')
          setMensaje(err.response?.data?.detail || 'No se pudo verificar el correo.')
        }
      })
    return () => { activo = false }
  }, [token])

  return (
    <div style={{ maxWidth: 480, margin: '0 auto' }}>
      <h1>Verificación de correo</h1>
      <div className="card stack">
        {estado === 'verificando' && <Spinner label="Verificando tu correo…" />}
        {estado === 'ok' && <Alert type="success">{mensaje}</Alert>}
        {estado === 'error' && <Alert type="error">{mensaje}</Alert>}
        {estado !== 'verificando' && (
          <Link className="btn" to="/login">Ir a iniciar sesión</Link>
        )}
      </div>
    </div>
  )
}
