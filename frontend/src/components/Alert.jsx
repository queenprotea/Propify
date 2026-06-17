import { useEffect, useRef } from 'react'

// Mensaje de estado con aria-live para que los lectores de pantalla lo anuncien.
// Al aparecer, se desplaza a la vista para que el usuario lo note aunque la
// página sea larga o haya actuado en un formulario más abajo.
export default function Alert({ type = 'info', children }) {
  const ref = useRef(null)
  useEffect(() => {
    if (children && ref.current) {
      ref.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [children])

  if (!children) return null
  return (
    <div ref={ref} className={`alert ${type}`} role={type === 'error' ? 'alert' : 'status'} aria-live="polite">
      {children}
    </div>
  )
}
