export default function Spinner({ label = 'Cargando…' }) {
  return (
    <div role="status" aria-live="polite" className="spinner-wrap">
      <div className="spinner" aria-hidden="true"></div>
      <span className="spinner-label">{label}</span>
    </div>
  )
}
