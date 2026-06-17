import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { propertiesApi, contactsApi, historyApi } from '../../api/properties'
import { visitsApi } from '../../api/users'
import { rentalsApi } from '../../api/contracts'
import { useAuth } from '../../context/AuthContext'
import { capitalizar, formatoMoneda, estadoDe, tipoDe, usoDe, operacionDe, claseEstado, validarTexto } from '../../utils/constants'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'
import PropertyMap from '../../components/PropertyMap'

const hoyISO = new Date().toISOString().slice(0, 10)
const minVisitaLocal = (() => {
  const d = new Date(); d.setDate(d.getDate() + 1); d.setHours(9, 0, 0, 0)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
})()

function DetailFeat({ label, value }) {
  if (!value && value !== 0) return null
  return (
    <div>
      <div className="detail-feat-label">{label}</div>
      <div className="detail-feat-value">{value}</div>
    </div>
  )
}

export default function PropertyDetail() {
  const { id } = useParams()
  const { isAuthenticated, isAdmin, user } = useAuth()
  const [inm, setInm] = useState(null)
  const [ubi, setUbi] = useState(null)
  const [fotos, setFotos] = useState([])
  const [fotoActiva, setFotoActiva] = useState(0)
  const [historial, setHistorial] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [contacto, setContacto] = useState({ nombre: '', correo: '', mensaje: '' })
  const [contactoMsg, setContactoMsg] = useState({ ok: '', err: '' })
  const [visitaFecha, setVisitaFecha] = useState('')
  const [visitaMsg, setVisitaMsg] = useState({ ok: '', err: '' })
  const [rentaMsg, setRentaMsg] = useState({ ok: '', err: '' })
  const [renta, setRenta] = useState({ fecha_inicio: '', fecha_fin: '' })
  const [compraMsg, setCompraMsg] = useState({ ok: '', err: '' })

  useEffect(() => {
    let activo = true
    async function cargar() {
      setLoading(true); setError('')
      try {
        const data = await propertiesApi.get(id)
        if (!activo) return
        setInm(data)
        setUbi(data.ubicacion || null)
        setFotos(data.imagenes || [])
        const h = await Promise.allSettled([historyApi.byInmueble(id)])
        if (!activo) return
        if (h[0].status === 'fulfilled') setHistorial(h[0].value || [])
      } catch (err) {
        if (activo) setError(err.response?.data?.detail || 'No se pudo cargar el inmueble.')
      } finally {
        if (activo) setLoading(false)
      }
    }
    cargar()
    return () => { activo = false }
  }, [id])

  async function enviarContacto(e) {
    e.preventDefault()
    setContactoMsg({ ok: '', err: '' })
    const errTexto = validarTexto(contacto.nombre, 'El nombre') || validarTexto(contacto.mensaje, 'El mensaje')
    if (errTexto) { setContactoMsg({ ok: '', err: errTexto }); return }
    try {
      await contactsApi.create({
        nombre: contacto.nombre.trim(),
        correo: contacto.correo.trim(),
        mensaje: contacto.mensaje.trim(),
        inmueble_id: Number(id),
      })
      setContactoMsg({ ok: 'Mensaje enviado. Te contactaremos pronto.', err: '' })
      setContacto({ nombre: '', correo: '', mensaje: '' })
    } catch (err) {
      const detail = err.response?.status === 401
        ? 'Inicia sesión para enviar un mensaje.'
        : (err.response?.data?.detail || 'No se pudo enviar el mensaje.')
      setContactoMsg({ ok: '', err: detail })
    }
  }

  function mesesEntre(ini, fin) {
    if (!ini || !fin) return 0
    const a = new Date(ini), b = new Date(fin)
    if (b <= a) return 0
    return Math.max(1, Math.round((b - a) / (1000 * 60 * 60 * 24 * 30)))
  }

  async function solicitarRenta(e) {
    e.preventDefault()
    setRentaMsg({ ok: '', err: '' })
    if (!renta.fecha_inicio || !renta.fecha_fin) {
      setRentaMsg({ ok: '', err: 'Indica las fechas de inicio y fin de la renta.' }); return
    }
    if (renta.fecha_inicio < hoyISO) {
      setRentaMsg({ ok: '', err: 'La fecha de inicio no puede ser anterior a hoy.' }); return
    }
    if (new Date(renta.fecha_fin) <= new Date(renta.fecha_inicio)) {
      setRentaMsg({ ok: '', err: 'La fecha de fin debe ser posterior a la de inicio.' }); return
    }
    try {
      await rentalsApi.create({
        inmueble_id: Number(id),
        fecha_inicio: renta.fecha_inicio,
        fecha_fin: renta.fecha_fin,
        duracion_meses: mesesEntre(renta.fecha_inicio, renta.fecha_fin),
      })
      setRentaMsg({ ok: 'Solicitud de renta enviada. Síguela en "Mis solicitudes".', err: '' })
    } catch (err) {
      setRentaMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo enviar la solicitud.' })
    }
  }

  async function solicitarCompra() {
    setCompraMsg({ ok: '', err: '' })
    const ok = window.confirm(
      `Vas a enviar una SOLICITUD DE COMPRA del inmueble "${inm.titulo}" por ${formatoMoneda(inm.precio)}.\n\n` +
      'Esto inicia un trámite formal: el administrador la revisará y, si la aprueba, ' +
      'generará un contrato de compraventa. Todavía no es un pago.\n\n¿Deseas continuar?'
    )
    if (!ok) return
    try {
      await rentalsApi.create({ inmueble_id: Number(id), tipo_operacion: 'venta' })
      setCompraMsg({ ok: 'Solicitud de compra enviada. Síguela en "Mis solicitudes".', err: '' })
    } catch (err) {
      setCompraMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo enviar la solicitud.' })
    }
  }

  async function agendarVisita(e) {
    e.preventDefault()
    setVisitaMsg({ ok: '', err: '' })
    if (!visitaFecha || visitaFecha.slice(0, 10) <= hoyISO) {
      setVisitaMsg({ ok: '', err: 'La visita debe agendarse para una fecha posterior a hoy.' }); return
    }
    try {
      const estados = await visitsApi.states()
      const programada = estados.find((s) => s.valor === 'programada') || estados[0]
      await visitsApi.create({
        estado_id: programada.id,
        inmueble_id: Number(id),
        usuario_id: user.id,
        fecha: new Date(visitaFecha).toISOString(),
      })
      setVisitaMsg({ ok: 'Visita agendada correctamente.', err: '' })
      setVisitaFecha('')
    } catch (err) {
      setVisitaMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo agendar la visita.' })
    }
  }

  if (loading) return <div style={{ paddingTop: '2rem' }}><Spinner label="Cargando inmueble…" /></div>
  if (error) return <Alert type="error">{error}</Alert>
  if (!inm) return null

  const estado = estadoDe(inm)
  const fotoHero = fotos[fotoActiva]

  return (
    <div>
      {/* ---- GALERÍA ---- */}
      {fotos.length > 0 ? (
        <section aria-label="Fotografías del inmueble" className="detail-gallery">
          <div className="detail-hero-img">
            <img
              src={fotoHero.url_archivo}
              alt={fotoHero.descripcion || `Fotografía principal de ${inm.titulo}`}
            />
          </div>
          {fotos.length > 1 && (
            <div className="detail-thumbs" role="list" aria-label="Miniaturas">
              {fotos.map((f, i) => (
                <img
                  key={f.id}
                  src={f.url_archivo}
                  alt={f.descripcion || `Fotografía ${i + 1} de ${inm.titulo}`}
                  role="listitem"
                  className={i === fotoActiva ? 'selected' : ''}
                  onClick={() => setFotoActiva(i)}
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && setFotoActiva(i)}
                />
              ))}
            </div>
          )}
        </section>
      ) : (
        <div style={{ background: 'var(--n-100)', borderRadius: 'var(--radius-lg)', height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 'var(--sp-6)', color: 'var(--n-400)' }}>
          <p>Este inmueble no tiene fotografías aún.</p>
        </div>
      )}

      {/* ---- LAYOUT: contenido principal + sidebar ---- */}
      <div className="detail-layout">
        {/* Columna principal */}
        <div className="stack">
          {/* Header de la propiedad */}
          <div>
            <div className="row" style={{ marginBottom: 'var(--sp-2)' }}>
              <span className={`badge ${claseEstado(estado)}`}>{capitalizar(estado)}</span>
              <span style={{ color: 'var(--n-500)', fontSize: 'var(--text-sm)' }}>
                {capitalizar(tipoDe(inm))} · {capitalizar(usoDe(inm))}
              </span>
            </div>
            <h1 style={{ marginBottom: 'var(--sp-2)' }}>{inm.titulo}</h1>
            {ubi?.direccion_completa && (
              <p className="muted" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginBottom: 0 }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                  <circle cx="12" cy="10" r="3"/>
                </svg>
                {ubi.direccion_completa}
              </p>
            )}
          </div>

          {/* Descripción */}
          {inm.descripcion && (
            <div className="card">
              <h2>Descripción</h2>
              <p style={{ margin: 0, lineHeight: 1.8 }}>{inm.descripcion}</p>
            </div>
          )}

          {/* Características */}
          <div className="card">
            <h2>Características</h2>
            <div className="detail-feats-grid">
              <DetailFeat label="Tipo" value={capitalizar(tipoDe(inm))} />
              <DetailFeat label="Operación" value={capitalizar(operacionDe(inm)) || '—'} />
              <DetailFeat label="Uso" value={capitalizar(usoDe(inm))} />
              <DetailFeat label="Recámaras" value={inm.num_recamaras ?? '—'} />
              <DetailFeat label="Baños" value={inm.num_banos ?? '—'} />
              <DetailFeat label="Estacionamientos" value={inm.num_estacionamientos ?? '—'} />
              <DetailFeat label="Área construcción" value={inm.area_construccion ? `${inm.area_construccion} m²` : '—'} />
              <DetailFeat label="Amueblado" value={inm.amueblado ? 'Sí' : 'No'} />
            </div>
          </div>

          {/* Mapa */}
          {ubi && (
            <div className="card">
              <h2>Ubicación</h2>
              <PropertyMap
                points={[{ id: inm.id, titulo: inm.titulo, lat: ubi.latitud, lng: ubi.longitud, direccion: ubi.direccion_completa }]}
              />
            </div>
          )}

          {/* Formulario de contacto */}
          {!isAdmin && (
            <div className="card">
              <h2>Contactar al anunciante</h2>
              <Alert type="error">{contactoMsg.err}</Alert>
              <Alert type="success">{contactoMsg.ok}</Alert>
              <form onSubmit={enviarContacto} noValidate>
                <div className="grid form-2">
                  <Field label="Tu nombre" value={contacto.nombre} onChange={(e) => setContacto((c) => ({ ...c, nombre: e.target.value }))} required maxLength={100} />
                  <Field label="Tu correo" type="email" value={contacto.correo} onChange={(e) => setContacto((c) => ({ ...c, correo: e.target.value }))} required maxLength={100} />
                </div>
                <Field label="Mensaje" as="textarea" value={contacto.mensaje} onChange={(e) => setContacto((c) => ({ ...c, mensaje: e.target.value }))} required maxLength={1000} />
                <button className="btn" type="submit">Enviar mensaje</button>
              </form>
            </div>
          )}

          {/* Historial de estados */}
          {historial.length > 0 && (
            <div className="card">
              <h2>Historial de estados</h2>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {historial.map((h) => (
                  <li key={h.id} style={{ fontSize: 'var(--text-sm)', color: 'var(--n-600)' }}>
                    <strong style={{ color: 'var(--n-800)' }}>{capitalizar(h.estado_inmueble?.valor)}</strong>
                    {' — desde '}{new Date(h.fecha_inicio).toLocaleDateString('es-MX')}
                    {h.fecha_fin ? ` hasta ${new Date(h.fecha_fin).toLocaleDateString('es-MX')}` : ' (actual)'}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* ---- SIDEBAR ---- */}
        <div className="detail-sidebar stack">
          {/* Precio + badge */}
          <div className="card" style={{ borderColor: 'var(--p-200)' }}>
            <div className="detail-price">{formatoMoneda(inm.precio)}</div>
            <div style={{ marginTop: 'var(--sp-2)' }}>
              <span className={`badge ${claseEstado(estado)}`}>{capitalizar(estado)}</span>
            </div>

            {/* Agendar visita */}
            {!isAdmin && (
              <div style={{ marginTop: 'var(--sp-4)', paddingTop: 'var(--sp-4)', borderTop: '1px solid var(--n-100)' }}>
                <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--sp-3)' }}>Agendar visita</h3>
                {isAuthenticated ? (
                  <>
                    <Alert type="error">{visitaMsg.err}</Alert>
                    <Alert type="success">{visitaMsg.ok}</Alert>
                    <form onSubmit={agendarVisita} noValidate>
                      <Field
                        label="Fecha y hora"
                        type="datetime-local"
                        value={visitaFecha}
                        min={minVisitaLocal}
                        onChange={(e) => setVisitaFecha(e.target.value)}
                        required
                        hint="A partir de mañana."
                      />
                      <button className="btn full" type="submit" disabled={!visitaFecha}>
                        Agendar visita
                      </button>
                    </form>
                  </>
                ) : (
                  <p className="muted" style={{ fontSize: 'var(--text-sm)', margin: 0 }}>
                    <a href="/login">Inicia sesión</a> para agendar una visita.
                  </p>
                )}
              </div>
            )}

            {/* Solicitar renta */}
            {!isAdmin && estado === 'en renta' && (
              <div style={{ marginTop: 'var(--sp-4)', paddingTop: 'var(--sp-4)', borderTop: '1px solid var(--n-100)' }}>
                <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--sp-3)' }}>Solicitar renta</h3>
                <Alert type="error">{rentaMsg.err}</Alert>
                <Alert type="success">{rentaMsg.ok}</Alert>
                {isAuthenticated ? (
                  <form onSubmit={solicitarRenta} className="stack">
                    <p className="muted" style={{ margin: 0, fontSize: 'var(--text-xs)' }}>
                      Indica el periodo que deseas rentar.
                    </p>
                    <Field label="Inicio de la renta" type="date" value={renta.fecha_inicio} min={hoyISO}
                      onChange={(e) => setRenta((r) => ({ ...r, fecha_inicio: e.target.value }))} required />
                    <Field label="Fin de la renta" type="date" value={renta.fecha_fin} min={renta.fecha_inicio || hoyISO}
                      onChange={(e) => setRenta((r) => ({ ...r, fecha_fin: e.target.value }))} required />
                    {mesesEntre(renta.fecha_inicio, renta.fecha_fin) > 0 && (
                      <p className="muted" style={{ margin: 0, fontSize: 'var(--text-xs)' }}>
                        Duración estimada: <strong>{mesesEntre(renta.fecha_inicio, renta.fecha_fin)} mes(es)</strong>
                      </p>
                    )}
                    <button className="btn full" type="submit" disabled={!!rentaMsg.ok}>
                      Solicitar renta
                    </button>
                  </form>
                ) : (
                  <p className="muted" style={{ fontSize: 'var(--text-sm)', margin: 0 }}>
                    <a href="/login">Inicia sesión</a> para solicitar la renta.
                  </p>
                )}
              </div>
            )}

            {/* Solicitar compra */}
            {!isAdmin && estado === 'en venta' && (
              <div style={{ marginTop: 'var(--sp-4)', paddingTop: 'var(--sp-4)', borderTop: '1px solid var(--n-100)' }}>
                <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--sp-3)' }}>Solicitar compra</h3>
                <Alert type="error">{compraMsg.err}</Alert>
                <Alert type="success">{compraMsg.ok}</Alert>
                {isAuthenticated ? (
                  <>
                    <p className="muted" style={{ fontSize: 'var(--text-xs)', marginBottom: 'var(--sp-3)' }}>
                      Envía tu solicitud y el administrador te contactará para continuar el proceso.
                    </p>
                    <button className="btn full" type="button" onClick={solicitarCompra} disabled={!!compraMsg.ok}>
                      Solicitar compra
                    </button>
                  </>
                ) : (
                  <p className="muted" style={{ fontSize: 'var(--text-sm)', margin: 0 }}>
                    <a href="/login">Inicia sesión</a> para solicitar la compra.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
