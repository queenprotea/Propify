import { useEffect, useRef } from 'react'

// Diálogo accesible: rol dialog, foco atrapado básico, cierre con Escape,
// retorno de foco al disparador. (WCAG 2.1.1 — operable por teclado)
export default function Modal({ title, onClose, children }) {
  const ref = useRef(null)
  const titleId = 'modal-title'

  useEffect(() => {
    const prevFocus = document.activeElement
    const node = ref.current
    const focusables = node?.querySelectorAll(
      'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])',
    )
    focusables?.[0]?.focus()

    function onKey(e) {
      if (e.key === 'Escape') { onClose(); return }
      if (e.key === 'Tab' && focusables && focusables.length) {
        const first = focusables[0]
        const last = focusables[focusables.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault(); last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault(); first.focus()
        }
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      if (prevFocus instanceof HTMLElement) prevFocus.focus()
    }
  }, [onClose])

  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem', zIndex: 1000,
      }}
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="card"
        style={{ maxWidth: 560, width: '100%', maxHeight: '90vh', overflow: 'auto' }}
      >
        <div className="row" style={{ justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <h2 id={titleId} style={{ margin: 0 }}>{title}</h2>
          <button className="btn small secondary" onClick={onClose} aria-label="Cerrar diálogo">✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}
