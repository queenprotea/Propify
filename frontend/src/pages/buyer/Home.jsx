import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { propertiesApi } from '../../api/properties'
import { capitalizar, estadoDe, tipoDe, usoDe, operacionDe, ESTADOS_PUBLICOS } from '../../utils/constants'
import { useCategorias } from '../../hooks/useCategorias'
import Field from '../../components/Field'
import Spinner from '../../components/Spinner'
import Alert from '../../components/Alert'
import PropertyCard from '../../components/PropertyCard'

const filtrosInit = {
  texto: '', tipo: '', operacion: '', uso: '',
  precioMin: '', precioMax: '', recamaras: '', estado: '',
}

export default function Home() {
  const cat = useCategorias()
  const [inmuebles, setInmuebles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filtros, setFiltros] = useState(filtrosInit)

  useEffect(() => {
    let activo = true
    async function cargar() {
      setLoading(true); setError('')
      try {
        const lista = await propertiesApi.disponibles()
        if (!activo) return
        setInmuebles(lista)
      } catch (err) {
        if (activo) setError(err.response?.data?.detail || 'No se pudieron cargar los inmuebles.')
      } finally {
        if (activo) setLoading(false)
      }
    }
    cargar()
    return () => { activo = false }
  }, [])

  const set = (field) => (e) => setFiltros((f) => ({ ...f, [field]: e.target.value }))

  const resultados = useMemo(() => {
    return inmuebles.filter((inm) => {
      const ubi = inm.ubicacion
      if (filtros.texto) {
        const t = filtros.texto.toLowerCase()
        const ok = inm.titulo?.toLowerCase().includes(t) || inm.descripcion?.toLowerCase().includes(t) ||
          ubi?.ciudad?.toLowerCase().includes(t) || ubi?.colonia?.toLowerCase().includes(t) ||
          ubi?.estado_republica?.valor?.toLowerCase().includes(t)
        if (!ok) return false
      }
      if (filtros.tipo && tipoDe(inm) !== filtros.tipo) return false
      if (filtros.operacion && operacionDe(inm) !== filtros.operacion) return false
      if (filtros.uso && usoDe(inm) !== filtros.uso) return false
      if (filtros.estado && estadoDe(inm) !== filtros.estado) return false
      if (filtros.precioMin && Number(inm.precio) < Number(filtros.precioMin)) return false
      if (filtros.precioMax && Number(inm.precio) > Number(filtros.precioMax)) return false
      if (filtros.recamaras && Number(inm.num_recamaras || 0) < Number(filtros.recamaras)) return false
      return true
    })
  }, [inmuebles, filtros])

  const hayFiltros = Object.values(filtros).some(Boolean)

  return (
    <>
      {/* ---- HERO ---- */}
      <section className="hero" aria-labelledby="hero-title">
        <div className="inner">
          <div className="hero-eyebrow">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9,22 9,12 15,12 15,22"/>
            </svg>
            Plataforma inmobiliaria en México
          </div>

          <h1 id="hero-title">Encuentra el hogar perfecto para ti</h1>
          <p className="lead">Casas, departamentos y locales en venta y renta. Busca, compara y agenda visitas en un solo lugar.</p>

          <div className="op-tabs" role="group" aria-label="Tipo de operación">
            {[
              { val: '', label: 'Todas' },
              { val: 'venta', label: 'Comprar' },
              { val: 'renta', label: 'Rentar' },
            ].map(({ val, label }) => (
              <button
                key={val || 'todas'} type="button"
                aria-pressed={filtros.operacion === val}
                onClick={() => setFiltros((f) => ({ ...f, operacion: val }))}
              >
                {label}
              </button>
            ))}
          </div>

          <form className="hero-search" aria-label="Búsqueda rápida" onSubmit={(e) => e.preventDefault()}>
            <Field
              label="Ciudad, zona o título"
              value={filtros.texto}
              onChange={set('texto')}
              placeholder="Ej. Cancún, Polanco, Casa con jardín…"
            />
            <Field
              label="Tipo de inmueble"
              as="select"
              options={cat.tipos.map((t) => ({ value: t.valor, label: capitalizar(t.valor) }))}
              value={filtros.tipo}
              onChange={set('tipo')}
            />
            <Field
              label="Uso"
              as="select"
              options={['residencial', 'comercial'].map((t) => ({ value: t, label: capitalizar(t) }))}
              value={filtros.uso}
              onChange={set('uso')}
            />
            <a className="btn" href="#resultados">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
              </svg>
              Buscar
            </a>
          </form>

          {!loading && inmuebles.length > 0 && (
            <div className="hero-stats" aria-label="Estadísticas">
              <div className="hero-stat">
                <div className="hero-stat-num">{inmuebles.length}+</div>
                <div className="hero-stat-label">Propiedades activas</div>
              </div>
              <div className="hero-stat">
                <div className="hero-stat-num">{inmuebles.filter(i => operacionDe(i) === 'venta').length}+</div>
                <div className="hero-stat-label">En venta</div>
              </div>
              <div className="hero-stat">
                <div className="hero-stat-num">{inmuebles.filter(i => operacionDe(i) === 'renta').length}+</div>
                <div className="hero-stat-label">En renta</div>
              </div>
            </div>
          )}
        </div>
      </section>

      {error && (
        <div className="section first">
          <Alert type="error">{error}</Alert>
        </div>
      )}

      {loading ? (
        <div className="section first"><Spinner label="Cargando propiedades…" /></div>
      ) : (
        <>
          {/* ---- FILTROS AVANZADOS ---- */}
          <div className="section first">
            <details className="filtros">
              <summary>Filtros avanzados</summary>
              <div className="grid form-2" style={{ marginTop: '1rem' }}>
                <Field label="Precio mínimo" type="number" min="0" value={filtros.precioMin} onChange={set('precioMin')} />
                <Field label="Precio máximo" type="number" min="0" value={filtros.precioMax} onChange={set('precioMax')} />
                <Field label="Recámaras (mínimo)" type="number" min="0" value={filtros.recamaras} onChange={set('recamaras')} />
                <Field
                  label="Estado"
                  as="select"
                  options={ESTADOS_PUBLICOS.map((e) => ({ value: e, label: capitalizar(e) }))}
                  value={filtros.estado}
                  onChange={set('estado')}
                />
              </div>
              {hayFiltros && (
                <button type="button" className="btn secondary small" onClick={() => setFiltros(filtrosInit)}>
                  Limpiar filtros
                </button>
              )}
            </details>
          </div>

          {/* ---- RESULTADOS ---- */}
          <div className="section" id="resultados">
            <div className="section-head">
              <div>
                <div className="section-tag">
                  {filtros.operacion ? capitalizar(filtros.operacion) : 'Todas las propiedades'}
                </div>
                <h2 aria-live="polite" style={{ margin: 0 }}>
                  {resultados.length === 0
                    ? 'Sin resultados'
                    : `${resultados.length} propiedad${resultados.length !== 1 ? 'es' : ''} encontrada${resultados.length !== 1 ? 's' : ''}`}
                </h2>
              </div>
              {hayFiltros && (
                <button type="button" className="btn secondary small" onClick={() => setFiltros(filtrosInit)}>
                  Limpiar filtros
                </button>
              )}
            </div>

            {resultados.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 1rem', color: 'var(--n-300)' }} aria-hidden="true">
                  <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
                </svg>
                <p className="muted" style={{ margin: 0 }}>No hay inmuebles que coincidan con tu búsqueda.</p>
              </div>
            ) : (
              <div className="grid cards">
                {resultados.map((inm) => (
                  <PropertyCard key={inm.id} inmueble={inm} />
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* ---- CONTACTO ---- */}
      <section className="contact-section" aria-labelledby="contacto-title">
        <div className="contact-grid">
          <div>
            <div className="section-tag" style={{ marginBottom: '0.75rem' }}>¿Necesitas ayuda?</div>
            <h2 id="contacto-title" style={{ marginBottom: '0.5rem' }}>Estamos aquí para acompañarte</h2>
            <p className="muted">Nuestro equipo te guía en cada paso del proceso de compra o renta.</p>
          </div>
          <div>
            <h3>Contáctanos</h3>
            <p className="muted" style={{ lineHeight: 2 }}>
              +52 55 1234 5678<br />
              contacto@propify.com<br />
              Ciudad de México
            </p>
          </div>
          <div>
            <h3>¿Eres propietario?</h3>
            <p className="muted" style={{ marginBottom: '1rem' }}>Publica y gestiona tus inmuebles desde nuestro panel de administración.</p>
            <Link className="btn" to="/login">Acceder al panel</Link>
          </div>
        </div>
      </section>
    </>
  )
}
