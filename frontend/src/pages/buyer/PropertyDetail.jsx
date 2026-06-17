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
// Mínimo para agendar visita: mañana a las 09:00 (no hoy ni fechas pasadas).
const minVisitaLocal = (() => {
  const d = new Date(); d.setDate(d.getDate() + 1); d.setHours(9, 0, 0, 0)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
})()

export default function PropertyDetail() {
  const { id } = useParams()
  const { isAuthenticated, isAdmin, user } = useAuth()
  const [inm, setInm] = useState(null)
  const [ubi, setUbi] = useState(null)
  const [fotos, setFotos] = useState([])
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

  // Duración estimada en meses a partir de las fechas elegidas.
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
    // La visita debe ser a partir de mañana (no fechas pasadas ni el mismo día).
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

  if (loading) return <Spinner label="Cargando inmueble…" />
  if (error) return <Alert type="error">{error}</Alert>
  if (!inm) return null

  return (
    <div className="stack">
      <h1>{inm.titulo}</h1>
      <p className="row">
        <span className="price" style={{ fontSize: '1.5rem' }}>{formatoMoneda(inm.precio)}</span>
        <span className={`badge ${claseEstado(estadoDe(inm))}`}>{capitalizar(estadoDe(inm))}</span>
      </p>

      {/* Galería accesible: cada imagen con su texto alternativo */}
      <section aria-label="Fotografías del inmueble">
        {fotos.length === 0 ? (
          <p className="muted">Este inmueble no tiene fotografías.</p>
        ) : (
          <div className="grid cards">
            {fotos.map((f) => (
              <img
                key={f.id}
                src={f.url_archivo}
                alt={f.descripcion || `Fotografía de ${inm.titulo}`}
                style={{ width: '100%', borderRadius: 'var(--radius)' }}
              />
            ))}
          </div>
        )}
      </section>

      <div className="layout-2col">
        <div className="card stack">
          <h2>Características</h2>
          <dl className="stack">
            <div><dt style={{ fontWeight: 600 }}>Tipo</dt><dd>{capitalizar(tipoDe(inm))}</dd></div>
            <div><dt style={{ fontWeight: 600 }}>Operación</dt><dd>{capitalizar(operacionDe(inm)) || '—'}</dd></div>
            <div><dt style={{ fontWeight: 600 }}>Uso</dt><dd>{capitalizar(usoDe(inm))}</dd></div>
            <div><dt style={{ fontWeight: 600 }}>Recámaras</dt><dd>{inm.num_recamaras ?? '—'}</dd></div>
            <div><dt style={{ fontWeight: 600 }}>Baños</dt><dd>{inm.num_banos ?? '—'}</dd></div>
            <div><dt style={{ fontWeight: 600 }}>Estacionamientos</dt><dd>{inm.num_estacionamientos ?? '—'}</dd></div>
            <div><dt style={{ fontWeight: 600 }}>Área construcción</dt><dd>{inm.area_construccion ? `${inm.area_construccion} m²` : '—'}</dd></div>
            <div><dt style={{ fontWeight: 600 }}>Amueblado</dt><dd>{inm.amueblado ? 'Sí' : 'No'}</dd></div>
          </dl>
        </div>

        <div className="stack">
          {inm.descripcion && (
            <div className="card">
              <h2>Descripción</h2>
              <p>{inm.descripcion}</p>
            </div>
          )}

          {ubi && (
            <div className="card stack">
              <h2>Ubicación</h2>
              <p>{ubi.direccion_completa}</p>
              <PropertyMap points={[{ id: inm.id, titulo: inm.titulo, lat: ubi.latitud, lng: ubi.longitud, direccion: ubi.direccion_completa }]} />
            </div>
          )}
        </div>
      </div>

      {/* Contacto y visita son acciones de cliente: no se muestran al administrador. */}
      {!isAdmin && (
        <>
          {/* Contacto */}
          <div className="card stack">
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

          {/* Agendar visita (requiere sesión de cliente) */}
          <div className="card stack">
            <h2>Agendar una visita</h2>
            {isAuthenticated ? (
              <>
                <Alert type="error">{visitaMsg.err}</Alert>
                <Alert type="success">{visitaMsg.ok}</Alert>
                <form onSubmit={agendarVisita} noValidate>
                  <Field
                    label="Fecha y hora" type="datetime-local"
                    value={visitaFecha} min={minVisitaLocal} onChange={(e) => setVisitaFecha(e.target.value)} required
                    hint="La visita debe agendarse a partir de mañana."
                  />
                  <button className="btn" type="submit" disabled={!visitaFecha}>Agendar visita</button>
                </form>
              </>
            ) : (
              <p className="muted">Inicia sesión para agendar una visita.</p>
            )}
          </div>
        </>
      )}

      {/* Historial de estados */}
      {historial.length > 0 && (
        <div className="card">
          <h2>Historial de estados</h2>
          <ul>
            {historial.map((h) => (
              <li key={h.id}>
                <strong>{capitalizar(h.estado_inmueble?.valor)}</strong> — desde {new Date(h.fecha_inicio).toLocaleDateString('es-MX')}
                {h.fecha_fin ? ` hasta ${new Date(h.fecha_fin).toLocaleDateString('es-MX')}` : ' (actual)'}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Solicitar renta/compra son acciones de cliente: no se muestran al administrador. */}

      {/* Solicitud de renta en línea (al final, junto a su formulario) */}
      {!isAdmin && estadoDe(inm) === 'en renta' && (
        <div className="card stack">
          <h2>Solicitar renta</h2>
          <Alert type="error">{rentaMsg.err}</Alert>
          <Alert type="success">{rentaMsg.ok}</Alert>
          {isAuthenticated ? (
            <form onSubmit={solicitarRenta} className="stack">
              <p className="muted" style={{ margin: 0 }}>
                Indica el periodo que deseas rentar. Podrás darle seguimiento en "Mis solicitudes".
              </p>
              <div className="grid form-2">
                <Field label="Inicio de la renta" type="date" value={renta.fecha_inicio} min={hoyISO}
                       onChange={(e) => setRenta((r) => ({ ...r, fecha_inicio: e.target.value }))} required />
                <Field label="Fin de la renta" type="date" value={renta.fecha_fin} min={renta.fecha_inicio || hoyISO}
                       onChange={(e) => setRenta((r) => ({ ...r, fecha_fin: e.target.value }))} required />
              </div>
              {mesesEntre(renta.fecha_inicio, renta.fecha_fin) > 0 && (
                <p className="muted" style={{ margin: 0 }}>
                  Duración estimada: <strong>{mesesEntre(renta.fecha_inicio, renta.fecha_fin)} mes(es)</strong>
                </p>
              )}
              <button className="btn" type="submit" disabled={!!rentaMsg.ok}>Solicitar renta</button>
            </form>
          ) : (
            <p className="muted">Inicia sesión para solicitar la renta de este inmueble.</p>
          )}
        </div>
      )}

      {/* Solicitud de compra en línea (al final, junto a su formulario) */}
      {!isAdmin && estadoDe(inm) === 'en venta' && (
        <div className="card stack">
          <h2>Solicitar compra</h2>
          <Alert type="error">{compraMsg.err}</Alert>
          <Alert type="success">{compraMsg.ok}</Alert>
          {isAuthenticated ? (
            <div className="row">
              <p className="muted" style={{ margin: 0, flex: 1, minWidth: 200 }}>
                ¿Te interesa comprar este inmueble? Envía tu solicitud de compra y dale seguimiento desde tu panel.
              </p>
              <button className="btn" type="button" onClick={solicitarCompra} disabled={!!compraMsg.ok}>
                Solicitar compra
              </button>
            </div>
          ) : (
            <p className="muted">Inicia sesión para solicitar la compra de este inmueble.</p>
          )}
        </div>
      )}
    </div>
  )
}
