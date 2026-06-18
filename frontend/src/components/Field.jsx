import { useId } from 'react'

// Campo de formulario accesible: label asociada, hint y error con aria.
export default function Field({
  label, type = 'text', as = 'input', options = [], hint, error,
  required = false, value, onChange, ...rest
}) {
  const id = useId()
  const hintId = hint ? `${id}-hint` : undefined
  const errId = error ? `${id}-err` : undefined
  const describedBy = [hintId, errId].filter(Boolean).join(' ') || undefined

  // En inputs numéricos, bloquea la notación científica y signos (e, E, +, -)
  // que el navegador admite por defecto en type="number".
  const onKeyDown = type === 'number'
    ? (e) => { if (['e', 'E', '+', '-'].includes(e.key)) e.preventDefault() }
    : rest.onKeyDown

  const common = {
    id,
    value: value ?? '',
    onChange,
    required,
    'aria-invalid': error ? 'true' : undefined,
    'aria-describedby': describedBy,
    ...rest,
    ...(type === 'number' ? { onKeyDown } : {}),
  }

  return (
    <div className="field">
      <label htmlFor={id}>
        {label} {required && <span aria-hidden="true">*</span>}
        {required && <span className="sr-only">(obligatorio)</span>}
      </label>

      {as === 'select' ? (
        <select {...common}>
          <option value="">— Selecciona —</option>
          {options.map((opt) => {
            const val = typeof opt === 'string' ? opt : opt.value
            const lbl = typeof opt === 'string' ? opt : opt.label
            return <option key={val} value={val}>{lbl}</option>
          })}
        </select>
      ) : as === 'textarea' ? (
        <textarea rows={4} {...common} />
      ) : (
        <input type={type} {...common} />
      )}

      {hint && <p id={hintId} className="hint">{hint}</p>}
      {error && <p id={errId} className="error-text" role="alert">{error}</p>}
    </div>
  )
}
