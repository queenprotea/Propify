import { useEffect, useState } from 'react'
import { usersApi } from '../../api/users'
import { useAuth } from '../../context/AuthContext'
import { validarNombre } from '../../utils/constants'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

export default function Profile() {
  const { user } = useAuth()
  const [form, setForm] = useState(null)
  const [password, setPassword] = useState('')
  const [password2, setPassword2] = useState('')
  const [msg, setMsg] = useState({ ok: '', err: '' })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let activo = true
    usersApi.get(user.id)
      .then((u) => { if (activo) setForm({ nombre: u.nombre, correo: u.correo, telefono: u.telefono || '' }) })
      .catch((err) => setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cargar el perfil.' }))
      .finally(() => { if (activo) setLoading(false) })
    return () => { activo = false }
  }, [user.id])

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }))
  }

  async function onSubmit(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    const errNombre = validarNombre(form.nombre)
    if (errNombre) { setMsg({ ok: '', err: errNombre }); return }
    if (password && password !== password2) { setMsg({ ok: '', err: 'Las contraseñas no coinciden.' }); return }
    try {
      const payload = { ...form, telefono: form.telefono || null }
      if (password) payload.password = password
      await usersApi.update(user.id, payload)
      setMsg({ ok: 'Perfil actualizado.', err: '' })
      setPassword(''); setPassword2('')
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo actualizar el perfil.' })
    }
  }

  if (loading) return <Spinner label="Cargando perfil…" />
  if (!form) return <Alert type="error">{msg.err}</Alert>

  return (
    <div style={{ maxWidth: 520 }}>
      <h1>Editar perfil</h1>
      <div className="card">
        <Alert type="error">{msg.err}</Alert>
        <Alert type="success">{msg.ok}</Alert>
        <form onSubmit={onSubmit} noValidate>
          <Field label="Nombre completo" value={form.nombre} onChange={set('nombre')} required minLength={2} maxLength={100} />
          <Field label="Correo electrónico" type="email" value={form.correo} onChange={set('correo')} required maxLength={100} />
          <Field label="Teléfono" type="tel" inputMode="numeric" maxLength={10} value={form.telefono}
                 onChange={(e) => set('telefono')({ target: { value: e.target.value.replace(/\D/g, '') } })}
                 hint="10 dígitos (opcional)." />
          <Field
            label="Nueva contraseña" type="password" value={password}
            onChange={(e) => setPassword(e.target.value)} maxLength={30}
            hint="Déjala vacía para no cambiarla."
          />
          {password && (
            <Field
              label="Confirmar nueva contraseña" type="password" value={password2}
              onChange={(e) => setPassword2(e.target.value)} maxLength={30}
              error={password2 && password !== password2 ? 'Las contraseñas no coinciden.' : ''}
            />
          )}
          <button className="btn" type="submit">Guardar cambios</button>
        </form>
      </div>
    </div>
  )
}
