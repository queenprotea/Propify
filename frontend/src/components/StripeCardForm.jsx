import { useEffect, useRef, useState } from 'react'
import client from '../api/client'

// Carga Stripe.js una sola vez (sin dependencias npm).
let stripeJsPromise = null
function cargarStripeJs() {
  if (window.Stripe) return Promise.resolve()
  if (!stripeJsPromise) {
    stripeJsPromise = new Promise((resolve, reject) => {
      const s = document.createElement('script')
      s.src = 'https://js.stripe.com/v3/'
      s.onload = resolve
      s.onerror = () => reject(new Error('No se pudo cargar Stripe.js'))
      document.head.appendChild(s)
    })
  }
  return stripeJsPromise
}

// Formulario de tarjeta con Stripe Elements. Captura datos reales y devuelve
// el payment_method al confirmar; el cobro real lo hace el backend.
export default function StripeCardForm({ monto, onPay, disabled }) {
  const cardRef = useRef(null)
  const cardElement = useRef(null)
  const stripe = useRef(null)
  const [listo, setListo] = useState(false)
  const [error, setError] = useState('')
  const [procesando, setProcesando] = useState(false)

  useEffect(() => {
    let activo = true
    async function init() {
      try {
        const { publishable_key } = await client
          .get('/contracts/stripe-config')
          .then((r) => r.data)
        if (!publishable_key) {
          if (activo) setError('Falta configurar la clave publicable de Stripe (STRIPE_PUBLISHABLE_KEY).')
          return
        }
        await cargarStripeJs()
        if (!activo) return
        stripe.current = window.Stripe(publishable_key)
        const elements = stripe.current.elements()
        cardElement.current = elements.create('card', { hidePostalCode: true })
        cardElement.current.mount(cardRef.current)
        if (activo) setListo(true)
      } catch (e) {
        if (activo) setError(e.message || 'No se pudo inicializar el formulario de pago.')
      }
    }
    init()
    return () => {
      activo = false
      try { cardElement.current?.destroy() } catch { /* */ }
    }
  }, [])

  async function pagar() {
    setError('')
    if (!stripe.current || !cardElement.current) return
    if (!monto || Number(monto) <= 0) { setError('Indica un monto válido.'); return }
    setProcesando(true)
    try {
      const { error: e, paymentMethod } = await stripe.current.createPaymentMethod({
        type: 'card',
        card: cardElement.current,
      })
      if (e) { setError(e.message); setProcesando(false); return }
      await onPay(paymentMethod.id)
      cardElement.current.clear()
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo procesar el pago.')
    } finally {
      setProcesando(false)
    }
  }

  return (
    <div className="stack" style={{ gap: '0.5rem' }}>
      <label style={{ fontWeight: 500 }}>Datos de la tarjeta</label>
      <div ref={cardRef} style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', padding: '10px 12px', background: '#fff' }} />
      {error && <p className="muted" style={{ color: 'var(--color-danger)', margin: 0 }}>{error}</p>}
      <button className="btn" type="button" onClick={pagar} disabled={!listo || disabled || procesando}>
        {procesando ? 'Procesando…' : 'Pagar con tarjeta'}
      </button>
    </div>
  )
}
