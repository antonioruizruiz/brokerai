import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Card } from '@/components/ui/card'
import { getDividendos, type DividendoResumen } from '@/lib/api'
import { formatDate, formatPrecio } from '@/lib/format'
import { TODOS, useIndiceSeleccionado } from '@/lib/indiceContext'
import { cn } from '@/lib/utils'

export function DividendosPage() {
  const { indice, indiceParaApi } = useIndiceSeleccionado()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['dividendos', indiceParaApi],
    queryFn: () => getDividendos(indiceParaApi),
  })
  const [expandido, setExpandido] = useState<string | null>(null)

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Dividendos</h1>
        <p className="text-sm text-muted-foreground">
          Rentabilidad por dividendo (lo pagado en el último año frente al precio actual) e historial de
          {indice === TODOS ? ' cada empresa seguida' : ` las empresas de ${indice === 'NINGUNO' ? 'las acciones sueltas' : indice}`}
          . La "próxima fecha" es una estimación a partir del intervalo entre los últimos pagos, no una fecha
          confirmada por la empresa.
        </p>
      </div>

      <Card className="overflow-hidden">
        {isLoading && <p className="p-5 text-muted-foreground">Cargando...</p>}
        {isError && <p className="p-5 text-danger">No se ha podido conectar con el backend.</p>}

        {data && (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th className="px-5 py-3 font-medium">Empresa</th>
                <th className="px-5 py-3 font-medium">Sector</th>
                <th className="px-5 py-3 text-right font-medium">Rentabilidad</th>
                <th className="px-5 py-3 font-medium">Último pago</th>
                <th className="px-5 py-3 font-medium">Próximo (estimado)</th>
              </tr>
            </thead>
            <tbody>
              {data.map((d) => (
                <ExpandableRow
                  key={d.ticker}
                  dividendo={d}
                  abierto={expandido === d.ticker}
                  onToggle={() => setExpandido(expandido === d.ticker ? null : d.ticker)}
                />
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}

function ExpandableRow({
  dividendo,
  abierto,
  onToggle,
}: {
  dividendo: DividendoResumen
  abierto: boolean
  onToggle: () => void
}) {
  return (
    <>
      <tr className="cursor-pointer border-b border-border last:border-0 hover:bg-muted" onClick={onToggle}>
        <td className="px-5 py-3">
          <Link to={`/mercado/${dividendo.ticker}`} onClick={(e) => e.stopPropagation()} className="font-medium text-primary">
            {dividendo.ticker}
          </Link>
          <span className="ml-2 text-muted-foreground">{dividendo.name}</span>
          {!dividendo.activa && (
            <span className="ml-2 rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
              Inactiva
            </span>
          )}
        </td>
        <td className="px-5 py-3 text-muted-foreground">{dividendo.sector}</td>
        <td className={cn('px-5 py-3 text-right font-medium', dividendo.rentabilidad_pct == null && 'text-muted-foreground')}>
          {dividendo.rentabilidad_pct != null ? `${dividendo.rentabilidad_pct.toFixed(2)} %` : '—'}
        </td>
        <td className="px-5 py-3">
          {dividendo.fecha_ultimo
            ? `${formatDate(dividendo.fecha_ultimo)} (${formatPrecio(dividendo.importe_ultimo ?? 0, dividendo.moneda)})`
            : '—'}
        </td>
        <td className="px-5 py-3 text-muted-foreground">
          {dividendo.fecha_estimada_proximo ? formatDate(dividendo.fecha_estimada_proximo) : '—'}
        </td>
      </tr>
      {abierto && (
        <tr className="border-b border-border bg-muted/40 last:border-0">
          <td colSpan={5} className="px-5 py-3">
            {dividendo.historial.length === 0 ? (
              <p className="text-muted-foreground">Sin historial de dividendos descargado.</p>
            ) : (
              <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground">
                {dividendo.historial.map((h) => (
                  <span key={h.date}>
                    {formatDate(h.date)}: {formatPrecio(h.amount, dividendo.moneda)}
                  </span>
                ))}
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  )
}
