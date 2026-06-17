import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div style={{ textAlign: 'center', padding: '4rem 1rem', maxWidth: 480, margin: '0 auto' }}>
      <div style={{
        fontSize: '5rem', fontWeight: 800, fontFamily: 'var(--font-display)',
        background: 'linear-gradient(135deg, var(--p-600), var(--p-400))',
        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        backgroundClip: 'text', lineHeight: 1, marginBottom: '1rem',
      }}>
        404
      </div>
      <h1 style={{ fontSize: 'var(--text-2xl)', marginBottom: '0.5rem' }}>Página no encontrada</h1>
      <p className="muted" style={{ marginBottom: '2rem' }}>
        La página que buscas no existe o fue movida a otra ubicación.
      </p>
      <Link className="btn large" to="/">Volver al inicio</Link>
    </div>
  )
}
