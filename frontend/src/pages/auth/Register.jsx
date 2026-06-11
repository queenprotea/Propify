import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authApi } from '../../api/auth'
import Field from '../../components/Field'
import Alert from '../../components/Alert'

const empty = { nombre: '', correo: '', telefono: '', password: '' }

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
    if (form.nombre.trim().length < 2) return 'El nombre es obligatorio.'
    if (!/^\S+@\S+\.\S+$/.test(form.correo)) return 'Introduce un correo válido.'
    const p = form.password
    if (p.length < 8 || !/[A-Z]/.test(p) || !/[a-z]/.test(p) || !/\d/.test(p)) {
      return 'La contraseña debe tener 8+ caracteres, con mayúscula, minúscula y número.'
    }
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
    <div style={{ maxWidth: 520, margin: '0 auto' }}>
      <h1>Crear cuenta</h1>
      <div className="card">
        <Alert type="error">{error}</Alert>
        <Alert type="success">{ok}</Alert>
        <form onSubmit={onSubmit} noValidate>
          <Field label="Nombre completo" value={form.nombre} onChange={set('nombre')} required autoComplete="name" />
          <Field label="Correo electrónico" type="email" value={form.correo} onChange={set('correo')} required autoComplete="email" />
          <Field label="Teléfono" type="tel" inputMode="numeric" maxLength={10}
                 value={form.telefono}
                 onChange={(e) => setForm((f) => ({ ...f, telefono: e.target.value.replace(/\D/g, '') }))}
                 autoComplete="tel" hint="10 dígitos (opcional)." />
          <Field
            label="Contraseña" type="password" value={form.password} onChange={set('password')}
            required autoComplete="new-password"
            hint="Mínimo 8 caracteres, con mayúscula, minúscula y número."
          />
          <button className="btn" type="submit" disabled={busy}>{busy ? 'Creando…' : 'Crear cuenta'}</button>
        </form>
      </div>
      <p style={{ marginTop: '1rem' }}>¿Ya tienes cuenta? <Link to="/login">Iniciar sesión</Link></p>
    </div>
  )
}
