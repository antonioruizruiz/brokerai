import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { getCompanies } from '@/lib/api'
import { formatDate, formatPct, formatPrecio } from '@/lib/format'
import { TODOS, useIndiceSeleccionado } from '@/lib/indiceContext'
import { cn } from '@/lib/utils'

export function MercadoPage() {
  const { indice, indiceParaApi } = useIndiceSeleccionado()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['companies', indiceParaApi],
    queryFn: () => getCompanies(indiceParaApi),
  })
  const [busqueda, setBusqueda] = useState('')

  const termino = busqueda.trim().toLowerCase()
  const datosFiltrados = data?.filter(
    (company) => company.ticker.toLowerCase().includes(termino) || company.name.toLowerCase().includes(termino),
  )

  const fechaActualizacion = data
    ?.map((c) => c.last_price_date)
    .filter((f): f is string => f != null)
    .sort()
    .at(-1)

  const descripcionUniverso = indice === TODOS ? 'Todas las empresas seguidas (IBEX 35 + Dow Jones + Nasdaq-100 + sueltas)' : `Las empresas de ${indice === 'NINGUNO' ? 'las acciones sueltas' : indice}`

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Mercado</h1>
        <p className="text-sm text-muted-foreground">
          {descripcionUniverso}, con su último precio y variación
          {fechaActualizacion ? ` a fecha de ${formatDate(fechaActualizacion)}` : ''}.
        </p>
      </div>

      <Input
        type="search"
        placeholder="Buscar por ticker o nombre..."
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
        className="max-w-xs"
      />

      <Card className="overflow-hidden">
        {isLoading && <p className="p-5 text-muted-foreground">Cargando...</p>}
        {isError && <p className="p-5 text-danger">No se ha podido conectar con el backend.</p>}

        {datosFiltrados && (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th className="px-5 py-3 font-medium">Ticker</th>
                <th className="px-5 py-3 font-medium">Empresa</th>
                <th className="px-5 py-3 font-medium">Sector</th>
                <th className="px-5 py-3 text-right font-medium">Precio</th>
                <th className="px-5 py-3 text-right font-medium">Variación</th>
              </tr>
            </thead>
            <tbody>
              {datosFiltrados.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-5 text-center text-muted-foreground">
                    Ninguna empresa coincide con "{busqueda}".
                  </td>
                </tr>
              )}
              {datosFiltrados.map((company) => (
                <tr key={company.ticker} className="border-b border-border last:border-0 hover:bg-muted">
                  <td className="px-5 py-3">
                    <Link to={`/mercado/${company.ticker}`} className="font-medium text-primary">
                      {company.ticker}
                    </Link>
                  </td>
                  <td className="px-5 py-3">
                    {company.name}
                    {!company.activa && (
                      <span className="ml-2 rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                        Inactiva
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-muted-foreground">{company.sector}</td>
                  <td className="px-5 py-3 text-right">
                    {company.last_price != null ? formatPrecio(company.last_price, company.moneda) : '—'}
                  </td>
                  <td
                    className={cn(
                      'px-5 py-3 text-right font-medium',
                      company.change_pct == null && 'text-muted-foreground',
                      company.change_pct != null && company.change_pct > 0 && 'text-success',
                      company.change_pct != null && company.change_pct < 0 && 'text-danger',
                    )}
                  >
                    {company.change_pct != null ? formatPct(company.change_pct) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
