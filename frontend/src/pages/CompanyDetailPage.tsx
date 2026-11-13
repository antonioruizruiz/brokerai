import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { PriceChart } from '@/components/PriceChart'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  actualizarActivaEmpresa,
  actualizarDatosEmpresa,
  getCompany,
  getCompanyNews,
  getCompanyPrices,
  getSyncEstado,
} from '@/lib/api'
import { formatDate, formatDateTime, formatPct, formatPrecio } from '@/lib/format'
import { calcularResumenCotizacion } from '@/lib/retornos'
import { cn } from '@/lib/utils'

export function CompanyDetailPage() {
  const { ticker = '' } = useParams()
  const queryClient = useQueryClient()

  const { data: empresa } = useQuery({
    queryKey: ['company', ticker],
    queryFn: () => getCompany(ticker),
    enabled: ticker.length > 0,
  })

  const activaMutacion = useMutation({
    mutationFn: (activa: boolean) => actualizarActivaEmpresa(ticker, activa),
    onSuccess: (actualizada) => {
      queryClient.setQueryData(['company', ticker], actualizada)
      // También afecta a Mercado/Ranking/Hoy/Dividendos (muestran el estado activa/inactiva).
      queryClient.invalidateQueries()
    },
  })

  const datosMutacion = useMutation({
    mutationFn: () => actualizarDatosEmpresa(ticker),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prices', ticker] })
      queryClient.invalidateQueries({ queryKey: ['company', ticker] })
    },
  })

  const { data, isLoading, isError } = useQuery({
    queryKey: ['prices', ticker],
    queryFn: () => getCompanyPrices(ticker),
    enabled: ticker.length > 0,
  })

  const resumenCotizacion = data ? calcularResumenCotizacion(data) : null

  const { data: syncEstado } = useQuery({ queryKey: ['sync-estado'], queryFn: getSyncEstado })

  const {
    data: noticias,
    isLoading: cargandoNoticias,
    isError: errorNoticias,
  } = useQuery({
    queryKey: ['news', ticker],
    queryFn: () => getCompanyNews(ticker),
    enabled: ticker.length > 0,
  })

  return (
    <div className="space-y-4">
      <div>
        <Link to="/mercado" className="text-sm text-primary">
          ← Volver a Mercado
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold">{ticker}</h1>
          {empresa && !empresa.activa && (
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
              Inactiva
            </span>
          )}
        </div>
        <p className="text-sm text-muted-foreground">Precio histórico con medias de 50 y 200 sesiones.</p>
        {empresa && (
          <div className="mt-2 flex items-center gap-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={datosMutacion.isPending}
              onClick={() => datosMutacion.mutate()}
            >
              {datosMutacion.isPending ? 'Actualizando...' : 'Actualizar datos'}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={activaMutacion.isPending}
              onClick={() => activaMutacion.mutate(!empresa.activa)}
            >
              {empresa.activa ? 'Marcar como inactiva' : 'Reactivar'}
            </Button>
            {empresa.activa === false && (
              <span className="text-xs text-muted-foreground">
                No se le intentará descargar precio nuevo, pero conserva todo su histórico.
              </span>
            )}
            {activaMutacion.isError && <span className="text-xs text-danger">No se ha podido actualizar.</span>}
          </div>
        )}
        {datosMutacion.isSuccess && (
          <p className="mt-2 text-xs text-success">
            Datos actualizados: {datosMutacion.data.precios_actualizados} precios y{' '}
            {datosMutacion.data.dividendos_nuevos} dividendos nuevos.
          </p>
        )}
        {datosMutacion.isError && (
          <p className="mt-2 text-xs text-danger">{datosMutacion.error.message || 'No se pudieron actualizar los datos.'}</p>
        )}
      </div>

      {resumenCotizacion && (
        <Card>
          <CardHeader>
            <CardTitle>Cotización</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap items-baseline gap-3">
              <span className="text-2xl font-semibold">
                {formatPrecio(resumenCotizacion.precioActual, empresa?.moneda)}
              </span>
              <span className="text-sm text-muted-foreground">a {formatDate(resumenCotizacion.fechaActual)}</span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Datos de mercado actualizados:{' '}
              {syncEstado?.ultima_actualizacion_horaria ? formatDateTime(syncEstado.ultima_actualizacion_horaria) : '—'}
            </p>
            <div className="mt-3 grid grid-cols-3 gap-3 sm:grid-cols-6">
              {resumenCotizacion.retornos.map(({ etiqueta, pct }) => (
                <div key={etiqueta} className="rounded-lg border border-border p-2 text-center">
                  <p className="text-xs text-muted-foreground">{etiqueta}</p>
                  <p
                    className={cn(
                      'font-medium',
                      pct == null && 'text-muted-foreground',
                      pct != null && pct > 0 && 'text-success',
                      pct != null && pct < 0 && 'text-danger',
                    )}
                  >
                    {pct != null ? formatPct(pct) : '—'}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Precio</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && <p className="text-muted-foreground">Cargando...</p>}
          {isError && <p className="text-danger">No se ha podido conectar con el backend.</p>}
          {data && data.length === 0 && (
            <p className="text-muted-foreground">
              Todavía no hay histórico descargado para este valor. Lanza{' '}
              <code>python scripts/download_history.py</code> en el backend.
            </p>
          )}
          {data && data.length > 0 && <PriceChart bars={data} />}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Noticias recientes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {cargandoNoticias && <p className="text-muted-foreground">Cargando...</p>}
          {errorNoticias && <p className="text-danger">No se han podido cargar las noticias.</p>}
          {noticias && noticias.length === 0 && (
            <p className="text-muted-foreground">No se han encontrado noticias recientes.</p>
          )}
          {noticias?.map((item) => (
            <a
              key={item.link}
              href={item.link}
              target="_blank"
              rel="noreferrer"
              className="block rounded-md border border-border p-3 hover:bg-muted"
            >
              <p className="font-medium text-primary">{item.title}</p>
              <p className="text-xs text-muted-foreground">
                {[item.publisher, item.published_at ? formatDate(item.published_at.slice(0, 10)) : null]
                  .filter(Boolean)
                  .join(' · ')}
              </p>
            </a>
          ))}
          <p className="text-xs text-muted-foreground">
            Titulares de prensa vía Google News, no son hechos verificados ni asesoramiento.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
