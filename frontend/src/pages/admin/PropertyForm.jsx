import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { propertiesApi, locationsApi, imagesApi } from '../../api/properties'
import { capitalizar, validarTexto } from '../../utils/constants'
import { useCategorias } from '../../hooks/useCategorias'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'
import LocationPicker from '../../components/LocationPicker'

const inmuebleInit = {
  titulo: '', descripcion: '', precio: '', tipo_id: '', estado_id: '',
  num_recamaras: '', num_banos: '', num_estacionamientos: '', niveles: '',
  area_construccion: '', area_terreno: '', amueblado: false,
}
const ubicacionInit = {
  estado_id: '', ciudad: '', colonia: '', calle: '', numero_exterior: '', numero_interior: '',
  codigo_postal: '', latitud: '', longitud: '',
}

export default function PropertyForm() {
  const { id } = useParams()
  const editando = Boolean(id)
  const navigate = useNavigate()
  const cat = useCategorias()

  const [inm, setInm] = useState(inmuebleInit)
  const [ubi, setUbi] = useState(ubicacionInit)
  const [ubicacionId, setUbicacionId] = useState(null)
  const [fotos, setFotos] = useState([])
  const [archivo, setArchivo] = useState(null)
  const [textoAlt, setTextoAlt] = useState('')
  const [loading, setLoading] = useState(editando)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState({ ok: '', err: '' })

  useEffect(() => {
    if (!editando) return
    let activo = true
    async function cargar() {
      try {
        const data = await propertiesApi.get(id)
        if (!activo) return
        setInm({ ...inmuebleInit, ...data, descripcion: data.descripcion || '' })
        setUbicacionId(data.ubicacion_id)
        if (data.ubicacion) {
          setUbi({ ...ubicacionInit, ...data.ubicacion, numero_interior: data.ubicacion.numero_interior || '' })
        }
        setFotos(data.imagenes || [])
      } catch (err) {
        if (activo) setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cargar el inmueble.' })
      } finally {
        if (activo) setLoading(false)
      }
    }
    cargar()
    return () => { activo = false }
  }, [id, editando])

  const setI = (f) => (e) => setInm((s) => ({ ...s, [f]: e.target.value }))
  const setU = (f) => (e) => setUbi((s) => ({ ...s, [f]: e.target.value }))

  // Aplica la ubicación elegida en el mapa, rellenando solo los campos con valor.
  // El nombre del estado (geocodificador) se traduce a su id de catálogo.
  function aplicarUbicacionMapa(info) {
    setUbi((s) => {
      const next = { ...s }
      for (const [k, v] of Object.entries(info)) {
        if (k === 'direccion_completa' || k === 'estado') continue
        if (v !== undefined && v !== null && v !== '') next[k] = String(v)
      }
      if (info.estado) {
        const normaliza = (t) => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
        const match = cat.estados_republica.find((e) => normaliza(e.valor) === normaliza(info.estado))
        if (match) next.estado_id = String(match.id)
      }
      return next
    })
  }

  function payloadInmueble(ubiId) {
    const num = (v) => (v === '' || v == null ? null : Number(v))
    return {
      titulo: inm.titulo.trim(),
      descripcion: inm.descripcion.trim() || null,
      precio: Number(inm.precio),
      tipo_id: Number(inm.tipo_id),
      estado_id: Number(inm.estado_id),
      num_recamaras: num(inm.num_recamaras),
      num_banos: num(inm.num_banos),
      num_estacionamientos: num(inm.num_estacionamientos),
      niveles: num(inm.niveles),
      area_construccion: num(inm.area_construccion),
      area_terreno: num(inm.area_terreno),
      amueblado: Boolean(inm.amueblado),
      ubicacion_id: ubiId,
    }
  }

  function payloadUbicacion() {
    const num = (v) => (v === '' || v == null ? null : Number(v))
    return {
      estado_id: Number(ubi.estado_id), ciudad: ubi.ciudad, colonia: ubi.colonia, calle: ubi.calle,
      numero_exterior: ubi.numero_exterior, numero_interior: ubi.numero_interior || null,
      codigo_postal: ubi.codigo_postal, latitud: num(ubi.latitud), longitud: num(ubi.longitud),
    }
  }

  async function onSubmit(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    // Validación de caracteres en los campos de texto antes de enviar.
    const errTexto = validarTexto(inm.titulo, 'El título')
      || validarTexto(inm.descripcion, 'La descripción')
      || validarTexto(ubi.ciudad, 'La ciudad') || validarTexto(ubi.colonia, 'La colonia')
      || validarTexto(ubi.calle, 'La calle')
    if (errTexto) { setMsg({ ok: '', err: errTexto }); return }
    setBusy(true)
    try {
      if (editando) {
        if (ubicacionId) await locationsApi.update(ubicacionId, payloadUbicacion())
        await propertiesApi.update(id, payloadInmueble(ubicacionId))
        setMsg({ ok: 'Inmueble actualizado.', err: '' })
      } else {
        const u = await locationsApi.create(payloadUbicacion())
        const creado = await propertiesApi.create(payloadInmueble(u.id))
        navigate(`/admin/inmuebles/${creado.id}/editar`)
        setMsg({ ok: 'Inmueble creado. Ya puedes subir fotografías.', err: '' })
      }
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo guardar el inmueble.' })
    } finally {
      setBusy(false)
    }
  }

  async function subirImagen(e) {
    e.preventDefault()
    if (!archivo || !textoAlt.trim()) return
    setMsg({ ok: '', err: '' })
    try {
      await imagesApi.upload(Number(id), archivo, textoAlt.trim())
      setArchivo(null); setTextoAlt('')
      setFotos(await imagesApi.byInmueble(id))
      setMsg({ ok: 'Imagen subida.', err: '' })
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo subir la imagen.' })
    }
  }

  async function eliminarImagen(imgId) {
    try {
      await imagesApi.remove(imgId)
      setFotos((f) => f.filter((x) => x.id !== imgId))
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo eliminar la imagen.' })
    }
  }

  if (loading) return <Spinner label="Cargando inmueble…" />

  return (
    <div className="stack" style={{ maxWidth: 800 }}>
      <h1>{editando ? 'Editar inmueble' : 'Publicar inmueble'}</h1>

      <form onSubmit={onSubmit} noValidate className="stack">
        <fieldset className="card">
          <legend><h2 style={{ display: 'inline' }}>Datos del inmueble</h2></legend>
          <Field label="Título" value={inm.titulo} onChange={setI('titulo')} required minLength={5} maxLength={100} hint="Entre 5 y 100 caracteres." />
          <Field label="Descripción" as="textarea" value={inm.descripcion} onChange={setI('descripcion')} maxLength={2000} hint="Máximo 2000 caracteres." />
          <div className="grid form-2">
            <Field label="Precio (MXN)" type="number" min="1" max="999999999" step="0.01" value={inm.precio} onChange={setI('precio')} required />
            <Field label="Tipo" as="select" options={cat.tipos.map((t) => ({ value: t.id, label: capitalizar(t.valor) }))} value={inm.tipo_id} onChange={setI('tipo_id')} required />
            <Field label="Estado" as="select" options={cat.estados.map((t) => ({ value: t.id, label: capitalizar(t.valor) }))} value={inm.estado_id} onChange={setI('estado_id')} required hint="'En venta' o 'en renta' define la operación ofertada." />
            <Field label="Recámaras" type="number" min="0" max="100" value={inm.num_recamaras} onChange={setI('num_recamaras')} />
            <Field label="Baños" type="number" min="0" max="100" value={inm.num_banos} onChange={setI('num_banos')} />
            <Field label="Estacionamientos" type="number" min="0" max="100" value={inm.num_estacionamientos} onChange={setI('num_estacionamientos')} />
            <Field label="Niveles" type="number" min="0" max="100" value={inm.niveles} onChange={setI('niveles')} />
            <Field label="Área construcción (m²)" type="number" min="0" max="1000000" step="0.01" value={inm.area_construccion} onChange={setI('area_construccion')} />
            <Field label="Área terreno (m²)" type="number" min="0" max="1000000" step="0.01" value={inm.area_terreno} onChange={setI('area_terreno')} />
          </div>
          <div className="field">
            <label htmlFor="amueblado">
              <input
                id="amueblado" type="checkbox" checked={inm.amueblado}
                onChange={(e) => setInm((s) => ({ ...s, amueblado: e.target.checked }))}
                style={{ width: 'auto', marginRight: '0.5rem' }}
              />
              Amueblado
            </label>
          </div>
        </fieldset>

        <fieldset className="card">
          <legend><h2 style={{ display: 'inline' }}>Ubicación</h2></legend>

          <LocationPicker value={ubi} onPick={aplicarUbicacionMapa} />

          <p className="muted" style={{ marginTop: '1rem' }}>
            Puedes ajustar los datos manualmente. La dirección completa se genera automáticamente.
          </p>
          <div className="grid form-2">
            <Field label="Estado" as="select" options={cat.estados_republica.map((e) => ({ value: e.id, label: e.valor }))} value={ubi.estado_id} onChange={setU('estado_id')} required />
            <Field label="Ciudad" value={ubi.ciudad} onChange={setU('ciudad')} required maxLength={100} />
            <Field label="Colonia" value={ubi.colonia} onChange={setU('colonia')} required maxLength={100} />
            <Field label="Calle" value={ubi.calle} onChange={setU('calle')} required maxLength={100} />
            <Field label="Número exterior" value={ubi.numero_exterior} onChange={setU('numero_exterior')} required maxLength={20} />
            <Field label="Número interior" value={ubi.numero_interior} onChange={setU('numero_interior')} maxLength={20} />
            <Field label="Código postal" type="text" inputMode="numeric" value={ubi.codigo_postal}
                   onChange={(e) => setUbi((s) => ({ ...s, codigo_postal: e.target.value.replace(/\D/g, '') }))}
                   required maxLength={5} hint="5 dígitos." />
            <Field label="Latitud" type="number" step="any" value={ubi.latitud} onChange={setU('latitud')} hint="Para el mapa." />
            <Field label="Longitud" type="number" step="any" value={ubi.longitud} onChange={setU('longitud')} hint="Para el mapa." />
          </div>
        </fieldset>

        {/* Retroalimentación junto a la acción que la genera. */}
        <Alert type="error">{msg.err}</Alert>
        <Alert type="success">{msg.ok}</Alert>
        <button className="btn" type="submit" disabled={busy}>
          {busy ? 'Guardando…' : (editando ? 'Guardar cambios' : 'Crear inmueble')}
        </button>
      </form>

      {/* Imágenes: solo disponible al editar (el inmueble ya existe) */}
      {editando && (
        <fieldset className="card">
          <legend><h2 style={{ display: 'inline' }}>Fotografías</h2></legend>
          <div className="grid cards">
            {fotos.map((f) => (
              <figure key={f.id} className="stack">
                <img src={f.url_archivo} alt={f.descripcion} style={{ width: '100%', borderRadius: 'var(--radius)' }} />
                <figcaption className="muted">{f.descripcion}</figcaption>
                <button className="btn small danger" type="button" onClick={() => eliminarImagen(f.id)}>
                  Eliminar<span className="sr-only"> imagen: {f.descripcion}</span>
                </button>
              </figure>
            ))}
          </div>
          <form onSubmit={subirImagen} className="stack" style={{ marginTop: '1rem' }}>
            <div className="field">
              <label htmlFor="archivo">Archivo de imagen (PNG, JPG o WEBP)</label>
              <input id="archivo" type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => setArchivo(e.target.files[0])} />
            </div>
            <Field
              label="Texto alternativo" value={textoAlt} onChange={(e) => setTextoAlt(e.target.value)}
              required hint="Describe la imagen para personas con discapacidad visual (obligatorio)."
            />
            <button className="btn" type="submit" disabled={!archivo || !textoAlt.trim()}>Subir imagen</button>
          </form>
        </fieldset>
      )}
    </div>
  )
}
