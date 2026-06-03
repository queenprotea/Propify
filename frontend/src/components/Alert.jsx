// Mensaje de estado con aria-live para que los lectores de pantalla lo anuncien.
export default function Alert({ type = 'info', children }) {
  if (!children) return null
  return (
    <div className={`alert ${type}`} role={type === 'error' ? 'alert' : 'status'} aria-live="polite">
      {children}
    </div>
  )
}
