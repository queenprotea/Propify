import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { usersApi } from '../../api/users'
import { useAuth } from '../../context/AuthContext'
import DataTable from '../../components/DataTable'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

export default function UsersAdmin() {
  const { user } = useAuth()
  const [usuarios, setUsuarios] = useState([])
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ ok: '', err: '' })

  async function cargar() {
    setLoading(true)
    try {
      setUsuarios(await usersApi.all(100, 0))
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudieron cargar los usuarios.' })
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => { cargar() }, [])

  async function alternarActivo(u) {
    setMsg({ ok: '', err: '' })
    try {
      if (u.is_active) await usersApi.deactivate(u.id)
      else await usersApi.activate(u.id)
      cargar()
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cambiar el estado del usuario.' })
    }
  }

  const filtrados = usuarios.filter((u) =>
    !q || u.nombre?.toLowerCase().includes(q.toLowerCase()) || u.correo?.toLowerCase().includes(q.toLowerCase()),
  )

  const adminsActivos = usuarios.filter((u) => u.is_admin && u.is_active).length

  const columns = [
    { key: 'nombre', header: 'Nombre' },
    { key: 'correo', header: 'Correo' },
    { key: 'telefono', header: 'Teléfono', render: (r) => r.telefono || '—' },
    { key: 'is_admin', header: 'Rol', render: (r) => (r.is_admin ? 'Administrador' : 'Comprador') },
    { key: 'is_active', header: 'Estado', render: (r) => (r.is_active ? 'Activo' : 'Inactivo') },
    {
      key: 'acciones', header: 'Acciones',
      render: (r) => {
        if (r.id === user.id) return <span className="muted">Tu cuenta</span>
        const ultimoAdmin = r.is_admin && r.is_active && adminsActivos <= 1
        if (r.is_active && ultimoAdmin) {
          return <span className="muted" title="Debe existir al menos un administrador activo">Último admin</span>
        }
        return (
          <button className="btn small secondary" type="button" onClick={() => alternarActivo(r)}>
            {r.is_active ? 'Desactivar' : 'Activar'}<span className="sr-only"> a {r.nombre}</span>
          </button>
        )
      },
    },
  ]

  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h1>Gestión de usuarios</h1>
        <Link className="btn" to="/admin/usuarios/nuevo-admin">Registrar administrador</Link>
      </div>
      <Alert type="error">{msg.err}</Alert>
      <div style={{ maxWidth: 360 }}>
        <Field label="Buscar usuarios" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {loading ? <Spinner /> : (
        <DataTable caption="Usuarios del sistema" columns={columns} rows={filtrados} empty="No hay usuarios." />
      )}
    </div>
  )
}
