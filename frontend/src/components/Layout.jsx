import { NavLink, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout({ children }) {
  const { isAuthenticated, isAdmin, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <>
      <a href="#main-content" className="skip-link">Saltar al contenido principal</a>

      <header className="site-header">
        <div className="bar">
          <Link to="/" className="brand">Propify</Link>
          <nav className="main-nav" aria-label="Navegación principal">
            <ul>
              <li><NavLink to="/">Inicio</NavLink></li>
              {isAdmin && (
                <>
                  <li><NavLink to="/admin">Panel</NavLink></li>
                  <li><NavLink to="/admin/inmuebles">Inmuebles</NavLink></li>
                  <li><NavLink to="/admin/solicitudes">Solicitudes</NavLink></li>
                  <li><NavLink to="/admin/usuarios">Usuarios</NavLink></li>
                  <li><NavLink to="/admin/contratos">Contratos</NavLink></li>
                  <li><NavLink to="/admin/rentas">Rentas</NavLink></li>
                  <li><NavLink to="/admin/ventas">Ventas</NavLink></li>
                  <li><NavLink to="/admin/pagos">Pagos</NavLink></li>
                  <li><NavLink to="/admin/auditoria">Auditoría</NavLink></li>
                  <li><NavLink to="/admin/visitas">Visitas</NavLink></li>
                  <li><NavLink to="/admin/contactos">Contactos</NavLink></li>
                </>
              )}
              {isAuthenticated && !isAdmin && (
                <>
                  <li><NavLink to="/mis-solicitudes">Mis solicitudes</NavLink></li>
                  <li><NavLink to="/mis-visitas">Mis visitas</NavLink></li>
                  <li><NavLink to="/mis-contratos">Mis contratos</NavLink></li>
                </>
              )}
              {isAuthenticated ? (
                <>
                  <li><NavLink to="/perfil">Perfil</NavLink></li>
                  <li><button type="button" className="nav-btn" onClick={handleLogout}>Cerrar sesión</button></li>
                </>
              ) : (
                <>
                  <li><NavLink to="/login">Iniciar sesión</NavLink></li>
                  <li><NavLink to="/registro">Crear cuenta</NavLink></li>
                </>
              )}
            </ul>
          </nav>
        </div>
      </header>

      <main id="main-content" tabIndex={-1}>
        <div className="container">{children}</div>
      </main>

      <footer className="site-footer">
        <p>© {new Date().getFullYear()} Propify — Gestión inmobiliaria.</p>
      </footer>
    </>
  )
}
