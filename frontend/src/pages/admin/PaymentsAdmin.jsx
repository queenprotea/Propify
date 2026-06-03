import { useState } from 'react'
import { contractsApi, paymentsApi } from '../../api/contracts'
import { METODOS_PAGO } from '../../utils/constants'
import Field from '../../components/Field'
import Alert from '../../components/Alert'

export default function PaymentsAdmin() {
  const [manual, setManual] = useState({ contrato_id: '', monto: '', metodo: 'transferencia' })
  const [stripe, setStripe] = useState({ contrato_id: '', monto: '' })
  const [consulta, setConsulta] = useState('')
  const [estadoPago, setEstadoPago] = useState(null)
  const [msg, setMsg] = useState({ ok: '', err: '' })

  async function registrarManual(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    try {
      await contractsApi.addPayment(Number(manual.contrato_id), {
        monto: Number(manual.monto),
        metodo: manual.metodo,
      })
      setMsg({ ok: 'Pago registrado correctamente.', err: '' })
      setManual({ contrato_id: '', monto: '', metodo: 'transferencia' })
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo registrar el pago.' })
    }
  }

  async function pagarConStripe(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    try {
      const res = await paymentsApi.start({
        contrato_id: Number(stripe.contrato_id),
        monto: Number(stripe.monto),
        success_url: `${window.location.origin}/admin/pagos?status=ok`,
        cancel_url: `${window.location.origin}/admin/pagos?status=cancel`,
      })
      // Redirige al checkout de Stripe.
      window.location.href = res.checkout_url
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo iniciar el pago con Stripe.' })
    }
  }

  async function consultarEstado(e) {
    e.preventDefault()
    setEstadoPago(null); setMsg({ ok: '', err: '' })
    try {
      setEstadoPago(await paymentsApi.status(Number(consulta)))
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se encontró el pago.' })
    }
  }

  return (
    <div className="stack">
      <h1>Pagos</h1>
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>

      <div className="card stack">
        <h2>Registrar pago manual</h2>
        <p className="muted">Para transferencias o efectivo.</p>
        <form onSubmit={registrarManual} noValidate className="toolbar">
          <Field label="ID contrato" type="number" value={manual.contrato_id} onChange={(e) => setManual((m) => ({ ...m, contrato_id: e.target.value }))} required />
          <Field label="Monto (MXN)" type="number" min="0" value={manual.monto} onChange={(e) => setManual((m) => ({ ...m, monto: e.target.value }))} required />
          <Field label="Método" as="select" options={METODOS_PAGO} value={manual.metodo} onChange={(e) => setManual((m) => ({ ...m, metodo: e.target.value }))} required />
          <button className="btn" type="submit">Registrar pago</button>
        </form>
      </div>

      <div className="card stack">
        <h2>Pago con tarjeta (Stripe)</h2>
        <form onSubmit={pagarConStripe} noValidate className="toolbar">
          <Field label="ID contrato" type="number" value={stripe.contrato_id} onChange={(e) => setStripe((s) => ({ ...s, contrato_id: e.target.value }))} required />
          <Field label="Monto (MXN)" type="number" min="0" value={stripe.monto} onChange={(e) => setStripe((s) => ({ ...s, monto: e.target.value }))} required />
          <button className="btn" type="submit">Pagar con Stripe</button>
        </form>
      </div>

      <div className="card stack">
        <h2>Consultar estado de un pago</h2>
        <form onSubmit={consultarEstado} noValidate className="toolbar">
          <Field label="ID pago" type="number" value={consulta} onChange={(e) => setConsulta(e.target.value)} required />
          <button className="btn secondary" type="submit">Consultar</button>
        </form>
        {estadoPago && (
          <p>Pago #{estadoPago.pago_id} — <strong>{estadoPago.estado}</strong> (contrato #{estadoPago.contrato_id})</p>
        )}
      </div>
    </div>
  )
}
