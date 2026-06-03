import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { propertiesApi, contactsApi } from '../../api/properties'
import { usersApi, visitsApi } from '../../api/users'

function Tarjeta({ titulo, valor, to }) {
  return (
    <Link to={to} className="card" style={{ textDecoration: 'none', color: 'inherit' }}>
      <h2 style={{ margin: 0 }}>{valor}</h2>
      <p className="muted" style={{ margin: 0 }}>{titulo}</p>
    </Link>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState({ inmuebles: '—', usuarios: '—', visitas: '—', contactos: '—' })

  useEffect(() => {
    async function cargar() {
      const [inm, usr, vis, con] = await Promise.allSettled([
        propertiesApi.list(100, 0),
        usersApi.all(100, 0),
        visitsApi.all(),
        contactsApi.all(100, 0),
      ])
      setStats({
        inmuebles: inm.status === 'fulfilled' ? inm.value.length : '—',
        usuarios: usr.status === 'fulfilled' ? usr.value.length : '—',
        visitas: vis.status === 'fulfilled' ? vis.value.length : '—',
        contactos: con.status === 'fulfilled' ? con.value.length : '—',
      })
    }
    cargar()
  }, [])

  return (
    <div className="stack">
      <h1>Panel de administración</h1>
      <div className="grid cards">
        <Tarjeta titulo="Inmuebles" valor={stats.inmuebles} to="/admin/inmuebles" />
        <Tarjeta titulo="Usuarios" valor={stats.usuarios} to="/admin/usuarios" />
        <Tarjeta titulo="Visitas" valor={stats.visitas} to="/admin/visitas" />
        <Tarjeta titulo="Contactos" valor={stats.contactos} to="/admin/contactos" />
      </div>
      <div className="row">
        <Link className="btn" to="/admin/inmuebles/nuevo">Publicar inmueble</Link>
        <Link className="btn secondary" to="/admin/usuarios/nuevo-admin">Registrar administrador</Link>
        <Link className="btn secondary" to="/admin/contratos">Contratos</Link>
        <Link className="btn secondary" to="/admin/pagos">Pagos</Link>
      </div>
    </div>
  )
}
