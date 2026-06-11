import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { propertiesApi } from '../../api/properties'
import { capitalizar, estadoDe, tipoDe, usoDe, operacionDe, ESTADOS_PUBLICOS } from '../../utils/constants'
import { useCategorias } from '../../hooks/useCategorias'
import Field from '../../components/Field'
import Spinner from '../../components/Spinner'
import Alert from '../../components/Alert'
import PropertyCard from '../../components/PropertyCard'
import PropertyMap from '../../components/PropertyMap'

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
  const [verMapa, setVerMapa] = useState(false)

  useEffect(() => {
    let activo = true
    async function cargar() {
      setLoading(true); setError('')
      try {
        // Listado público: solo inmuebles visibles (en venta / en renta / reservado),
        // con ubicación e imágenes embebidas.
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

  const puntos = resultados.map((inm) => {
    const ubi = inm.ubicacion
    return { id: inm.id, titulo: inm.titulo, lat: ubi?.latitud, lng: ubi?.longitud, direccion: ubi?.direccion_completa || 'Dirección no disponible' }
  })

  return (
    <>
      {/* HERO con buscador principal */}
      <section className="hero" aria-labelledby="hero-title">
        <div className="inner">
          <h1 id="hero-title">Encuentra el inmueble perfecto para ti</h1>
          <p className="lead">Casas, departamentos y locales en venta y renta. Busca, compara y agenda visitas en un solo lugar.</p>

          <div className="op-tabs" role="group" aria-label="Tipo de operación">
            {['', 'venta', 'renta'].map((op) => (
              <button
                key={op || 'todas'} type="button"
                aria-pressed={filtros.operacion === op}
                onClick={() => setFiltros((f) => ({ ...f, operacion: op }))}
              >
                {op === '' ? 'Todas' : op === 'venta' ? 'Comprar' : 'Rentar'}
              </button>
            ))}
          </div>

          <form className="hero-search" aria-label="Búsqueda rápida" onSubmit={(e) => e.preventDefault()}>
            <Field label="¿Dónde? Ciudad, zona o título" value={filtros.texto} onChange={set('texto')} placeholder="Ej. Cancún, Polanco…" />
            <Field label="Tipo" as="select" options={cat.tipos.map((t) => ({ value: t.valor, label: capitalizar(t.valor) }))} value={filtros.tipo} onChange={set('tipo')} />
            <Field label="Uso" as="select" options={['residencial', 'comercial'].map((t) => ({ value: t, label: capitalizar(t) }))} value={filtros.uso} onChange={set('uso')} />
            <a className="btn" href="#resultados">Buscar</a>
          </form>
        </div>
      </section>

      {error && <div className="section"><Alert type="error">{error}</Alert></div>}

      {loading ? (
        <div className="section"><Spinner label="Cargando inmuebles…" /></div>
      ) : (
        <>
          {/* Filtros avanzados */}
          <div className="section">
            <details className="filtros">
              <summary>Filtros avanzados</summary>
              <div className="grid form-2" style={{ marginTop: '1rem' }}>
                <Field label="Precio mínimo" type="number" min="0" value={filtros.precioMin} onChange={set('precioMin')} />
                <Field label="Precio máximo" type="number" min="0" value={filtros.precioMax} onChange={set('precioMax')} />
                <Field label="Recámaras (mínimo)" type="number" min="0" value={filtros.recamaras} onChange={set('recamaras')} />
                <Field label="Estado" as="select" options={ESTADOS_PUBLICOS.map((e) => ({ value: e, label: capitalizar(e) }))} value={filtros.estado} onChange={set('estado')} />
              </div>
              <button type="button" className="btn secondary" onClick={() => setFiltros(filtrosInit)}>Limpiar filtros</button>
            </details>
          </div>

          {/* Resultados / destacados */}
          <div className="section" id="resultados">
            <div className="section-head">
              <h2 aria-live="polite">{resultados.length} propiedad(es) {filtros.operacion ? `en ${filtros.operacion}` : 'destacadas'}</h2>
              <button type="button" className="btn secondary" onClick={() => setVerMapa((v) => !v)} aria-pressed={verMapa}>
                {verMapa ? 'Ocultar mapa' : 'Ver en el mapa'}
              </button>
            </div>

            {verMapa && <div style={{ marginBottom: '1.5rem' }}><PropertyMap points={puntos} /></div>}

            {resultados.length === 0 ? (
              <p className="muted">No hay inmuebles que coincidan con tu búsqueda.</p>
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

      {/* Contacto */}
      <section className="contact-section" aria-labelledby="contacto-title">
        <div className="contact-grid">
          <div>
            <h2 id="contacto-title">¿Necesitas ayuda?</h2>
            <p className="muted">Nuestro equipo te acompaña en todo el proceso de compra o renta.</p>
          </div>
          <div>
            <h3>Contacto</h3>
            <p className="muted">📞 +52 55 1234 5678<br />✉️ contacto@propify.com<br />📍 Ciudad de México</p>
          </div>
          <div>
            <h3>¿Eres propietario?</h3>
            <p className="muted">Inicia sesión como administrador para publicar y gestionar inmuebles.</p>
            <Link className="btn" to="/login">Acceder</Link>
          </div>
        </div>
      </section>
    </>
  )
}
