import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authApi } from '../../api/auth'
import { validarNombre } from '../../utils/constants'
import Field from '../../components/Field'
import Alert from '../../components/Alert'

const empty = { nombre: '', correo: '', telefono: '', password: '', password2: '' }

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [busy, setBusy] = useState(false)

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }))
  }

  function validar() {
    const errNombre = validarNombre(form.nombre)
    if (errNombre) return errNombre
    if (!/^\S+@\S+\.\S+$/.test(form.correo)) return 'Introduce un correo válido.'
    const p = form.password
    if (p.length < 8 || !/[A-Z]/.test(p) || !/[a-z]/.test(p) || !/\d/.test(p)) {
      return 'La contraseña debe tener 8+ caracteres, con mayúscula, minúscula y número.'
    }
    if (form.password !== form.password2) return 'Las contraseñas no coinciden.'
    return ''
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError(''); setOk('')
    const v = validar()
    if (v) { setError(v); return }
    setBusy(true)
    try {
      await authApi.register({
        nombre: form.nombre.trim(),
        correo: form.correo.trim(),
        telefono: form.telefono.trim() || null,
        password: form.password,
        is_active: true,
        is_admin: false,
      })
      setOk('Cuenta creada. Te enviamos un enlace de verificación a tu correo; confírmalo para poder iniciar sesión.')
      setTimeout(() => navigate('/login'), 4000)
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo crear la cuenta.')
    } finally {
      setBusy(false)
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

        <h1 className="auth-title">Crea tu cuenta</h1>
        <p className="auth-subtitle">Únete a Propify y encuentra tu próximo hogar</p>

        <Alert type="error">{error}</Alert>
        <Alert type="success">{ok}</Alert>

        <form onSubmit={onSubmit} noValidate>
          <Field
            label="Nombre completo"
            value={form.nombre}
            onChange={set('nombre')}
            required autoComplete="name" maxLength={100}
          />
          <Field
            label="Correo electrónico"
            type="email"
            value={form.correo}
            onChange={set('correo')}
            required autoComplete="email" maxLength={100}
          />
          <Field
            label="Teléfono"
            type="tel" inputMode="numeric" maxLength={10}
            value={form.telefono}
            onChange={(e) => setForm((f) => ({ ...f, telefono: e.target.value.replace(/\D/g, '') }))}
            autoComplete="tel"
            hint="10 dígitos (opcional)."
          />
          <Field
            label="Contraseña"
            type="password"
            value={form.password}
            onChange={set('password')}
            required autoComplete="new-password" maxLength={30}
            hint="Mínimo 8 caracteres, con mayúscula, minúscula y número."
          />
          <Field
            label="Confirmar contraseña"
            type="password"
            value={form.password2}
            onChange={set('password2')}
            required autoComplete="new-password" maxLength={30}
            error={form.password2 && form.password !== form.password2 ? 'Las contraseñas no coinciden.' : ''}
          />
          <button className="btn full large" type="submit" disabled={busy}>
            {busy ? 'Creando cuenta…' : 'Crear cuenta'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: 'var(--text-sm)', color: 'var(--n-500)' }}>
          ¿Ya tienes cuenta?{' '}
          <Link to="/login" style={{ color: 'var(--p-600)', fontWeight: 600 }}>Iniciar sesión</Link>
        </p>
      </div>
    </div>
  )
}
