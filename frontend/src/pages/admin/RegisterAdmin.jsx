import { useState } from 'react'
import { authApi } from '../../api/auth'
import Field from '../../components/Field'
import Alert from '../../components/Alert'

const empty = { nombre: '', correo: '', telefono: '', password: '' }

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
          <Field label="Nombre completo" value={form.nombre} onChange={set('nombre')} required />
          <Field label="Correo electrónico" type="email" value={form.correo} onChange={set('correo')} required />
          <Field label="Teléfono" type="tel" value={form.telefono} onChange={set('telefono')} hint="Opcional." />
          <Field
            label="Contraseña" type="password" value={form.password} onChange={set('password')} required
            hint="Mínimo 8 caracteres, con mayúscula, minúscula y número."
          />
          <button className="btn" type="submit" disabled={busy}>{busy ? 'Registrando…' : 'Registrar administrador'}</button>
        </form>
      </div>
    </div>
  )
}
