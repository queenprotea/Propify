import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="stack">
      <h1>Página no encontrada</h1>
      <p>La página que buscas no existe.</p>
      <Link className="btn" to="/">Volver al inicio</Link>
    </div>
  )
}
