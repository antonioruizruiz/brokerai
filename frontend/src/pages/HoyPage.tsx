import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getRecomendaciones } from '@/lib/api'
import { formatPrecio } from '@/lib/format'
import { useIndiceSeleccionado } from '@/lib/indiceContext'
import { cn } from '@/lib/utils'

const COLOR_RIESGO: Record<string, string> = {
  bajo: 'bg-success/15 text-success',
  medio: 'bg-amber-500/15 text-amber-600',
  alto: 'bg-danger/15 text-danger',
  desconocido: 'bg-muted text-muted-foreground',
}

export function HoyPage() {
  const { indiceParaApi } = useIndiceSeleccionado()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['recomendaciones', indiceParaApi],
    queryFn: () => getRecomendaciones(indiceParaApi),
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Hoy</h1>
        <p className="text-sm text-muted-foreground">
          Recomendaciones generadas con reglas técnicas mecánicas (ruptura de máximos con volumen, retroceso en
          tendencia alcista) sobre el histórico de precios. Todavía no pasan por la revisión de la IA (eso es la
          Fase 6). No es una recomendación de compra o venta, solo una ayuda de estudio.
        </p>
      </div>

      {isLoading && <p className="text-muted-foreground">Cargando...</p>}
      {isError && <p className="text-danger">No se ha podido conectar con el backend.</p>}

      {data && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Recomendaciones de hoy ({data.recomendaciones.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.recomendaciones.length === 0 && (
                <p className="text-muted-foreground">Ninguna regla se ha activado hoy.</p>
              )}
              {data.recomendaciones.map((rec) => (
                <div key={rec.ticker} className="rounded-lg border border-border p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <Link to={`/mercado/${rec.ticker}`} className="font-semibold text-primary">
                        {rec.ticker}
                      </Link>
                      <span className="ml-2 text-muted-foreground">{rec.name}</span>
                      <span className="ml-2 text-xs text-muted-foreground">· {rec.sector}</span>
                      {!rec.activa && (
                        <span className="ml-2 rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                          Inactiva
                        </span>
                      )}
                    </div>
                    <span className={cn('rounded-full px-2.5 py-0.5 text-xs font-medium', COLOR_RIESGO[rec.riesgo])}>
                      Riesgo {rec.riesgo}
                    </span>
                  </div>

                  <p className="mt-1 text-sm font-medium">{rec.regla}</p>
                  <p className="text-sm text-muted-foreground">{rec.motivo}</p>

                  <div className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Entrada</p>
                      <p className="font-medium">{formatPrecio(rec.entrada, rec.moneda)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Stop</p>
                      <p className="font-medium">{formatPrecio(rec.stop, rec.moneda)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Objetivo</p>
                      <p className="font-medium">{formatPrecio(rec.objetivo, rec.moneda)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Plazo</p>
                      <p className="font-medium">{rec.plazo}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Acciones a comprar</p>
                      <p className="font-medium">{rec.acciones}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Beneficio/riesgo neto de costes</p>
                      <p className="font-medium">
                        {rec.beneficio_riesgo_neto != null ? `${rec.beneficio_riesgo_neto.toFixed(2)}x` : '—'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>En vigilancia ({data.vigilancia.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-sm text-muted-foreground">
                Señales que se están formando, cerca de activarse, pero todavía sin plan de compra.
              </p>
              {data.vigilancia.length === 0 && <p className="text-muted-foreground">Nada en vigilancia hoy.</p>}
              {data.vigilancia.map((v) => (
                <div key={v.ticker} className="flex flex-wrap items-center gap-2 border-b border-border py-2 last:border-0">
                  <Link to={`/mercado/${v.ticker}`} className="font-medium text-primary">
                    {v.ticker}
                  </Link>
                  <span className="text-muted-foreground">{v.name}</span>
                  {!v.activa && (
                    <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                      Inactiva
                    </span>
                  )}
                  <span className="text-sm">— {v.regla}:</span>
                  <span className="text-sm text-muted-foreground">{v.motivo}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
