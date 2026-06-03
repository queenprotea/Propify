import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { propertiesApi, locationsApi, imagesApi } from '../../api/properties'
import { ESTADOS_REPUBLICA, capitalizar } from '../../utils/constants'
import { useCategorias } from '../../hooks/useCategorias'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'
import LocationPicker from '../../components/LocationPicker'

const inmuebleInit = {
  titulo: '', descripcion: '', precio: '', tipo: '', operacion: '', uso: '', estado: 'disponible',
  num_recamaras: '', num_banos: '', num_estacionamientos: '', niveles: '',
  area_construccion: '', area_terreno: '', amueblado: false,
}
const ubicacionInit = {
  estado: '', ciudad: '', colonia: '', calle: '', numero_exterior: '', numero_interior: '',
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
        if (data.ubicacion_id) {
          const u = await locationsApi.get(data.ubicacion_id)
          if (activo) setUbi({ ...ubicacionInit, ...u, numero_interior: u.numero_interior || '' })
        }
        const f = await imagesApi.byInmueble(id)
        if (activo) setFotos(f || [])
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
  function aplicarUbicacionMapa(info) {
    setUbi((s) => {
      const next = { ...s }
      for (const [k, v] of Object.entries(info)) {
        if (k === 'direccion_completa') continue
        if (v !== undefined && v !== null && v !== '') next[k] = String(v)
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
      tipo: inm.tipo,
      operacion: inm.operacion,
      uso: inm.uso,
      estado: inm.estado,
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
      estado: ubi.estado, ciudad: ubi.ciudad, colonia: ubi.colonia, calle: ubi.calle,
      numero_exterior: ubi.numero_exterior, numero_interior: ubi.numero_interior || null,
      codigo_postal: ubi.codigo_postal, latitud: num(ubi.latitud), longitud: num(ubi.longitud),
    }
  }

  async function onSubmit(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
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
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>

      <form onSubmit={onSubmit} noValidate className="stack">
        <fieldset className="card">
          <legend><h2 style={{ display: 'inline' }}>Datos del inmueble</h2></legend>
          <Field label="Título" value={inm.titulo} onChange={setI('titulo')} required hint="Mínimo 5 caracteres." />
          <Field label="Descripción" as="textarea" value={inm.descripcion} onChange={setI('descripcion')} />
          <div className="grid form-2">
            <Field label="Precio (MXN)" type="number" min="0" value={inm.precio} onChange={setI('precio')} required />
            <Field label="Tipo" as="select" options={cat.tipos.map((t) => ({ value: t, label: capitalizar(t) }))} value={inm.tipo} onChange={setI('tipo')} required />
            <Field label="Operación" as="select" options={cat.operaciones.map((t) => ({ value: t, label: capitalizar(t) }))} value={inm.operacion} onChange={setI('operacion')} required />
            <Field label="Uso" as="select" options={cat.usos.map((t) => ({ value: t, label: capitalizar(t) }))} value={inm.uso} onChange={setI('uso')} required />
            <Field label="Estado" as="select" options={cat.estados.map((t) => ({ value: t, label: capitalizar(t) }))} value={inm.estado} onChange={setI('estado')} required />
            <Field label="Recámaras" type="number" min="0" value={inm.num_recamaras} onChange={setI('num_recamaras')} />
            <Field label="Baños" type="number" min="0" value={inm.num_banos} onChange={setI('num_banos')} />
            <Field label="Estacionamientos" type="number" min="0" value={inm.num_estacionamientos} onChange={setI('num_estacionamientos')} />
            <Field label="Niveles" type="number" min="0" value={inm.niveles} onChange={setI('niveles')} />
            <Field label="Área construcción (m²)" type="number" min="0" value={inm.area_construccion} onChange={setI('area_construccion')} />
            <Field label="Área terreno (m²)" type="number" min="0" value={inm.area_terreno} onChange={setI('area_terreno')} />
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
            <Field label="Estado" as="select" options={ESTADOS_REPUBLICA} value={ubi.estado} onChange={setU('estado')} required />
            <Field label="Ciudad" value={ubi.ciudad} onChange={setU('ciudad')} required />
            <Field label="Colonia" value={ubi.colonia} onChange={setU('colonia')} required />
            <Field label="Calle" value={ubi.calle} onChange={setU('calle')} required />
            <Field label="Número exterior" value={ubi.numero_exterior} onChange={setU('numero_exterior')} required />
            <Field label="Número interior" value={ubi.numero_interior} onChange={setU('numero_interior')} />
            <Field label="Código postal" value={ubi.codigo_postal} onChange={setU('codigo_postal')} required />
            <Field label="Latitud" type="number" step="any" value={ubi.latitud} onChange={setU('latitud')} hint="Para el mapa." />
            <Field label="Longitud" type="number" step="any" value={ubi.longitud} onChange={setU('longitud')} hint="Para el mapa." />
          </div>
        </fieldset>

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
                <img src={f.url_archivo} alt={f.texto_alternativo} style={{ width: '100%', borderRadius: 'var(--radius)' }} />
                <figcaption className="muted">{f.texto_alternativo}</figcaption>
                <button className="btn small danger" type="button" onClick={() => eliminarImagen(f.id)}>
                  Eliminar<span className="sr-only"> imagen: {f.texto_alternativo}</span>
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
