import { useState, useEffect, useRef } from 'react'
import { NavLink, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const ADMIN_LINKS = [
  { to: '/admin/inmuebles',   label: 'Inmuebles' },
  { to: '/admin/solicitudes', label: 'Solicitudes' },
  { to: '/admin/contratos',   label: 'Contratos' },
  { to: '/admin/usuarios',    label: 'Usuarios' },
  { to: '/admin/rentas',      label: 'Rentas' },
  { to: '/admin/ventas',      label: 'Ventas' },
  { to: '/admin/clausulas',   label: 'Cláusulas' },
  { to: '/admin/visitas',     label: 'Visitas' },
  { to: '/admin/contactos',   label: 'Contactos' },
]

export default function Layout({ children }) {
  const { isAuthenticated, isAdmin, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const [adminOpen, setAdminOpen] = useState(false)
  const dropdownRef = useRef(null)

  useEffect(() => { setMenuOpen(false); setAdminOpen(false) }, [location.pathname])

  useEffect(() => {
    if (!adminOpen) return
    function onOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setAdminOpen(false)
    }
    document.addEventListener('mousedown', onOutside)
    return () => document.removeEventListener('mousedown', onOutside)
  }, [adminOpen])

  function handleLogout() { logout(); navigate('/login') }

  const isAdminPath = location.pathname.startsWith('/admin')

  return (
    <>
      <a href="#main-content" className="skip-link">Saltar al contenido principal</a>

      <header className="site-header">
        <div className="bar">
          <Link to="/" className="brand">
            <span className="brand-icon" aria-hidden="true">P</span>
            Propify
          </Link>

          <nav className={`main-nav${menuOpen ? ' open' : ''}`} aria-label="Navegación principal">
            <ul>
              <li><NavLink to="/" end>Inicio</NavLink></li>

              {isAdmin && (
                <li ref={dropdownRef} className="nav-dropdown">
                  <button
                    type="button"
                    className={`nav-dropdown-btn${isAdminPath ? ' active' : ''}`}
                    aria-expanded={adminOpen}
                    aria-haspopup="menu"
                    onClick={() => setAdminOpen((v) => !v)}
                  >
                    Panel Admin
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                      <path d="M6 9l6 6 6-6"/>
                    </svg>
                  </button>
                  {adminOpen && (
                    <div className="nav-dropdown-menu" role="menu">
                      {ADMIN_LINKS.map((l) => (
                        <NavLink key={l.to} to={l.to} role="menuitem">{l.label}</NavLink>
                      ))}
                    </div>
                  )}
                </li>
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
                <li><NavLink to="/login">Iniciar sesión</NavLink></li>
              )}
            </ul>
          </nav>

          <div className="nav-actions">
            {isAuthenticated ? (
              <span className="nav-avatar" aria-hidden="true" title="Mi cuenta">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </span>
            ) : (
              <NavLink to="/registro" className="nav-cta">Crear cuenta</NavLink>
            )}
            <button
              type="button"
              className={`nav-toggle${menuOpen ? ' open' : ''}`}
              aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((v) => !v)}
            >
              <span></span><span></span><span></span>
            </button>
          </div>
        </div>
      </header>

      <main id="main-content" tabIndex={-1}>
        <div className="container">{children}</div>
      </main>

      <footer className="site-footer" aria-label="Pie de página">
        <div className="footer-inner">
          <div className="footer-grid">
            <div>
              <div className="footer-brand-name">Propify</div>
              <p className="footer-desc">
                Plataforma inmobiliaria moderna para encontrar, comprar y rentar propiedades en México. Con tecnología, transparencia y acompañamiento profesional.
              </p>
            </div>
            <div className="footer-col">
              <h4>Explorar</h4>
              <ul>
                <li><Link to="/">Inicio</Link></li>
                <li><Link to="/">Propiedades en venta</Link></li>
                <li><Link to="/">Propiedades en renta</Link></li>
              </ul>
            </div>
            <div className="footer-col">
              <h4>Mi cuenta</h4>
              <ul>
                {isAuthenticated ? (
                  <>
                    <li><Link to="/perfil">Mi perfil</Link></li>
                    <li><Link to="/mis-contratos">Mis contratos</Link></li>
                    <li><Link to="/mis-visitas">Mis visitas</Link></li>
                    <li><Link to="/mis-solicitudes">Mis solicitudes</Link></li>
                  </>
                ) : (
                  <>
                    <li><Link to="/login">Iniciar sesión</Link></li>
                    <li><Link to="/registro">Crear cuenta</Link></li>
                  </>
                )}
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <span>© {new Date().getFullYear()} Propify — Gestión inmobiliaria moderna.</span>
            <span>Hecho con dedicación en México</span>
          </div>
        </div>
      </footer>
    </>
  )
}
