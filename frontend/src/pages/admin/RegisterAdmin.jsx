import { useState } from 'react'
import { authApi } from '../../api/auth'
import { validarNombre } from '../../utils/constants'
import Field from '../../components/Field'
import Alert from '../../components/Alert'

const empty = { nombre: '', correo: '', telefono: '', password: '', password2: '' }

export default function RegisterAdmin() {
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [busy, setBusy] = useState(false)

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }))
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError(''); setOk('')
    const errNombre = validarNombre(form.nombre)
    if (errNombre) { setError(errNombre); return }
    if (form.password !== form.password2) { setError('Las contraseñas no coinciden.'); return }
    setBusy(true)
    try {
      await authApi.registerAdmin({
        nombre: form.nombre.trim(),
        correo: form.correo.trim(),
        telefono: form.telefono.trim() || null,
        password: form.password,
        is_active: true,
        is_admin: true,
      })
      setOk(`Administrador "${form.nombre}" registrado correctamente.`)
      setForm(empty)
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo registrar el administrador.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ maxWidth: 520 }}>
      <h1>Registrar administrador</h1>
      <div className="card">
        <Alert type="error">{error}</Alert>
        <Alert type="success">{ok}</Alert>
        <form onSubmit={onSubmit} noValidate>
          <Field label="Nombre completo" value={form.nombre} onChange={set('nombre')} required minLength={2} maxLength={100} />
          <Field label="Correo electrónico" type="email" value={form.correo} onChange={set('correo')} required maxLength={100} />
          <Field label="Teléfono" type="tel" inputMode="numeric" maxLength={10} value={form.telefono}
                 onChange={(e) => set('telefono')({ target: { value: e.target.value.replace(/\D/g, '') } })}
                 hint="10 dígitos (opcional)." />
          <Field
            label="Contraseña" type="password" value={form.password} onChange={set('password')} required maxLength={30}
            hint="Mínimo 8 caracteres, con mayúscula, minúscula y número."
          />
          <Field
            label="Confirmar contraseña" type="password" value={form.password2} onChange={set('password2')} required maxLength={30}
            error={form.password2 && form.password !== form.password2 ? 'Las contraseñas no coinciden.' : ''}
          />
          <button className="btn" type="submit" disabled={busy}>{busy ? 'Registrando…' : 'Registrar administrador'}</button>
        </form>
      </div>
    </div>
  )
}
