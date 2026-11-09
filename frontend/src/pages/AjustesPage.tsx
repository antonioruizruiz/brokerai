import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getSettings, getSyncEstado, lanzarDescargaCompleta, updateSettings, type TradingSettings } from '@/lib/api'
import { formatDateTime } from '@/lib/format'

const CAMPOS: { clave: keyof TradingSettings; etiqueta: string; ayuda: string; sufijo: string }[] = [
  {
    clave: 'capital_total',
    etiqueta: 'Capital total',
    ayuda: 'El capital disponible para invertir, usado para calcular cuántas acciones comprar en cada plan.',
    sufijo: '€',
  },
  {
    clave: 'riesgo_pct_operacion',
    etiqueta: 'Riesgo máximo por operación',
    ayuda: 'Qué porcentaje del capital total estás dispuesto a perder si salta el stop de una sola recomendación.',
    sufijo: '%',
  },
  {
    clave: 'comision_pct',
    etiqueta: 'Comisión del bróker',
    ayuda: 'Porcentaje que cobra tu bróker por cada compra o venta.',
    sufijo: '%',
  },
  {
    clave: 'comision_minima',
    etiqueta: 'Comisión mínima',
    ayuda: 'Importe mínimo que cobra el bróker por operación, aunque el % salga más bajo.',
    sufijo: '€',
  },
  {
    clave: 'deslizamiento_pct',
    etiqueta: 'Deslizamiento estimado',
    ayuda: 'Diferencia habitual entre el precio al que querías comprar/vender y el precio real de ejecución.',
    sufijo: '%',
  },
]

export function AjustesPage() {
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({ queryKey: ['settings'], queryFn: getSettings })
  const [valores, setValores] = useState<TradingSettings | null>(null)

  useEffect(() => {
    if (data) setValores(data)
  }, [data])

  const mutacion = useMutation({
    mutationFn: updateSettings,
    onSuccess: (nuevosValores) => {
      queryClient.setQueryData(['settings'], nuevosValores)
    },
  })

  const { data: syncEstado } = useQuery({
    queryKey: ['sync-estado'],
    queryFn: getSyncEstado,
    refetchInterval: (query) => (query.state.data?.descarga_completa_en_progreso ? 5_000 : 60_000),
  })

  const descargaMutacion = useMutation({
    mutationFn: lanzarDescargaCompleta,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-estado'] })
    },
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Ajustes</h1>
        <p className="text-sm text-muted-foreground">
          Capital, riesgo por operación y costes que se usan para calcular los planes de la página Hoy.
        </p>
      </div>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Capital y riesgo</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && <p className="text-muted-foreground">Cargando...</p>}
          {isError && <p className="text-danger">No se ha podido conectar con el backend.</p>}

          {valores && (
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault()
                mutacion.mutate(valores)
              }}
            >
              {CAMPOS.map(({ clave, etiqueta, ayuda, sufijo }) => (
                <div key={clave}>
                  <label className="block text-sm font-medium" htmlFor={clave}>
                    {etiqueta}
                  </label>
                  <p className="mb-1 text-xs text-muted-foreground">{ayuda}</p>
                  <div className="flex items-center gap-2">
                    <input
                      id={clave}
                      type="number"
                      step="any"
                      className="w-40 rounded-md border border-border bg-transparent px-3 py-1.5 text-sm"
                      value={valores[clave]}
                      onChange={(e) =>
                        setValores({ ...valores, [clave]: e.target.value === '' ? 0 : Number(e.target.value) })
                      }
                    />
                    <span className="text-sm text-muted-foreground">{sufijo}</span>
                  </div>
                </div>
              ))}

              <div className="flex items-center gap-3 pt-2">
                <Button type="submit" disabled={mutacion.isPending}>
                  {mutacion.isPending ? 'Guardando...' : 'Guardar'}
                </Button>
                {mutacion.isSuccess && <span className="text-sm text-success">Guardado.</span>}
                {mutacion.isError && <span className="text-sm text-danger">No se ha podido guardar.</span>}
              </div>
            </form>
          )}
        </CardContent>
      </Card>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Datos de mercado</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-muted-foreground">
            Los precios se refrescan solos cada hora mientras el backend está encendido. Si quieres volver a
            descargar los 10 años de histórico completo de todo el universo (tarda varios minutos), usa este botón.
          </p>

          <div className="space-y-1 text-sm">
            <p>
              <span className="text-muted-foreground">Última actualización horaria: </span>
              {syncEstado?.ultima_actualizacion_horaria ? formatDateTime(syncEstado.ultima_actualizacion_horaria) : '—'}
            </p>
            <p>
              <span className="text-muted-foreground">Última descarga completa: </span>
              {syncEstado?.ultima_descarga_completa ? formatDateTime(syncEstado.ultima_descarga_completa) : '—'}
            </p>
            {syncEstado?.ultimo_error && <p className="text-xs text-danger">Último error: {syncEstado.ultimo_error}</p>}
          </div>

          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="outline"
              disabled={syncEstado?.descarga_completa_en_progreso || descargaMutacion.isPending}
              onClick={() => descargaMutacion.mutate()}
            >
              {syncEstado?.descarga_completa_en_progreso ? 'Descargando...' : 'Descargar todo el histórico de nuevo'}
            </Button>
            {descargaMutacion.isSuccess && !syncEstado?.descarga_completa_en_progreso && (
              <span className="text-sm text-success">Iniciada.</span>
            )}
            {descargaMutacion.isError && <span className="text-sm text-danger">No se ha podido iniciar.</span>}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
