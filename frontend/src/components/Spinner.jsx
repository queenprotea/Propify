export default function Spinner({ label = 'Cargando…' }) {
  return (
    <p role="status" aria-live="polite" className="muted" style={{ padding: '1rem 0' }}>
      {label}
    </p>
  )
}
