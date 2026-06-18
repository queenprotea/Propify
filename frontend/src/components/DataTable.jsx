// Tabla de datos accesible y genérica.
// columns: [{ key, header, render?(row) }]
export default function DataTable({ caption, columns, rows, empty = 'Sin registros.', rowKey = 'id' }) {
  if (!rows || rows.length === 0) {
    return <p className="muted">{empty}</p>
  }
  return (
    <div className="table-wrap">
      <table className="data">
        {caption && <caption>{caption}</caption>}
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} scope="col">{c.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[rowKey]}>
              {columns.map((c) => (
                <td key={c.key}>{c.render ? c.render(row) : row[c.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
