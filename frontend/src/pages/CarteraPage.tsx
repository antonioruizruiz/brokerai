import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  borrarPosicionCartera,
  crearPosicionCartera,
  getCartera,
  getCompanies,
  type PortfolioEntryInput,
  type TipoPosicion,
} from '@/lib/api'
import { formatDate, formatEuro, formatPct, formatPrecio } from '@/lib/format'
import { cn } from '@/lib/utils'

const ETIQUETA_TIPO: Record<TipoPosicion, string> = {
  corto_plazo: 'Corto plazo',
  largo_plazo: 'Largo plazo',
  dividendos: 'Dividendos',
}

const EXPLICACION_TIPO: Record<TipoPosicion, string> = {
  corto_plazo: 'Esperas que suba rápido: avisa si pierde más de un 5% o si gana más de un 15% (para valorar vender).',
  largo_plazo: 'La mantienes mucho tiempo: solo avisa si pierde más de un 20% (una caída ya seria).',
  dividendos: 'La tienes sobre todo por el dividendo: no avisa de ganancia/pérdida, sino de cuándo se espera el próximo pago.',
}

const FORMULARIO_INICIAL: PortfolioEntryInput = {
  ticker: '',
  fecha_compra: new Date().toISOString().slice(0, 10),
  precio_compra: 0,
  cantidad: 1,
  tipo: 'largo_plazo',
  notas: '',
}

export function CarteraPage() {
  const queryClient = useQueryClient()
  const { data: cartera, isLoading, isError } = useQuery({ queryKey: ['cartera'], queryFn: getCartera })
  const { data: empresas } = useQuery({ queryKey: ['companies'], queryFn: () => getCompanies() })
  const [formulario, setFormulario] = useState<PortfolioEntryInput>(FORMULARIO_INICIAL)

  const crear = useMutation({
    mutationFn: crearPosicionCartera,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cartera'] })
      setFormulario(FORMULARIO_INICIAL)
    },
  })

  const borrar = useMutation({
    mutationFn: borrarPosicionCartera,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cartera'] }),
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Cartera</h1>
        <p className="text-sm text-muted-foreground">
          Tus operaciones reales (o simuladas), con su valor actual y ganancia/pérdida, y un aviso sencillo según
          para qué compraste cada una.
        </p>
      </div>

      {isLoading && <p className="text-muted-foreground">Cargando...</p>}
      {isError && <p className="text-danger">No se ha podido conectar con el backend.</p>}

      {cartera && (
        <Card>
          <CardHeader>
            <CardTitle>Resumen</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs text-muted-foreground">Invertido</p>
              <p className="text-xl font-semibold">{formatEuro(cartera.resumen.valor_invertido_euros)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Valor actual</p>
              <p className="text-xl font-semibold">
                {cartera.resumen.valor_actual_euros != null ? formatEuro(cartera.resumen.valor_actual_euros) : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Ganancia/pérdida</p>
              <p
                className={cn(
                  'text-xl font-semibold',
                  cartera.resumen.ganancia_perdida_euros != null &&
                    (cartera.resumen.ganancia_perdida_euros >= 0 ? 'text-success' : 'text-danger'),
                )}
              >
                {cartera.resumen.ganancia_perdida_euros != null
                  ? `${formatEuro(cartera.resumen.ganancia_perdida_euros)} (${formatPct(cartera.resumen.ganancia_perdida_pct ?? 0)})`
                  : '—'}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Añadir posición</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="grid grid-cols-2 gap-3 sm:grid-cols-3"
            onSubmit={(e) => {
              e.preventDefault()
              if (!formulario.ticker) return
              crear.mutate({ ...formulario, notas: formulario.notas || null })
            }}
          >
            <label className="col-span-2 text-sm sm:col-span-1">
              Empresa
              <select
                className="mt-1 w-full rounded-md border border-border bg-transparent px-2 py-1.5 text-sm"
                value={formulario.ticker}
                onChange={(e) => setFormulario({ ...formulario, ticker: e.target.value })}
                required
              >
                <option value="">Selecciona...</option>
                {empresas?.map((c) => (
                  <option key={c.ticker} value={c.ticker}>
                    {c.ticker} — {c.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm">
              Fecha de compra
              <input
                type="date"
                className="mt-1 w-full rounded-md border border-border bg-transparent px-2 py-1.5 text-sm"
                value={formulario.fecha_compra}
                onChange={(e) => setFormulario({ ...formulario, fecha_compra: e.target.value })}
                required
              />
            </label>

            <label className="text-sm">
              Tipo
              <select
                className="mt-1 w-full rounded-md border border-border bg-transparent px-2 py-1.5 text-sm"
                value={formulario.tipo}
                title={EXPLICACION_TIPO[formulario.tipo]}
                onChange={(e) => setFormulario({ ...formulario, tipo: e.target.value as TipoPosicion })}
              >
                {Object.entries(ETIQUETA_TIPO).map(([valor, etiqueta]) => (
                  <option key={valor} value={valor}>
                    {etiqueta}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-muted-foreground">{EXPLICACION_TIPO[formulario.tipo]}</p>
            </label>

            <label className="text-sm">
              Precio de compra ({empresas?.find((c) => c.ticker === formulario.ticker)?.moneda ?? '€'})
              <input
                type="number"
                step="any"
                min="0"
                className="mt-1 w-full rounded-md border border-border bg-transparent px-2 py-1.5 text-sm"
                value={formulario.precio_compra}
                onChange={(e) => setFormulario({ ...formulario, precio_compra: Number(e.target.value) })}
                required
              />
            </label>

            <label className="text-sm">
              Cantidad
              <input
                type="number"
                min="1"
                step="1"
                className="mt-1 w-full rounded-md border border-border bg-transparent px-2 py-1.5 text-sm"
                value={formulario.cantidad}
                onChange={(e) => setFormulario({ ...formulario, cantidad: Number(e.target.value) })}
                required
              />
            </label>

            <label className="col-span-2 text-sm sm:col-span-3">
              Notas (opcional)
              <input
                type="text"
                className="mt-1 w-full rounded-md border border-border bg-transparent px-2 py-1.5 text-sm"
                value={formulario.notas ?? ''}
                onChange={(e) => setFormulario({ ...formulario, notas: e.target.value })}
              />
            </label>

            <div className="col-span-2 sm:col-span-3">
              <Button type="submit" disabled={crear.isPending}>
                {crear.isPending ? 'Añadiendo...' : 'Añadir'}
              </Button>
              {crear.isError && <span className="ml-3 text-sm text-danger">No se ha podido añadir.</span>}
            </div>
          </form>
        </CardContent>
      </Card>

      {cartera && (
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle>Posiciones ({cartera.posiciones.length})</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {cartera.posiciones.length === 0 && (
              <p className="p-5 text-muted-foreground">Todavía no has añadido ninguna posición.</p>
            )}
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="px-5 py-3 font-medium">Empresa</th>
                  <th className="px-5 py-3 font-medium">Tipo</th>
                  <th className="px-5 py-3 font-medium">Compra</th>
                  <th className="px-5 py-3 text-right font-medium">Valor actual</th>
                  <th className="px-5 py-3 text-right font-medium">Ganancia/pérdida</th>
                  <th className="px-5 py-3 font-medium">Aviso</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody>
                {cartera.posiciones.map((p) => (
                  <tr key={p.id} className="border-b border-border last:border-0">
                    <td className="px-5 py-3">
                      <Link to={`/mercado/${p.ticker}`} className="font-medium text-primary">
                        {p.ticker}
                      </Link>
                      <span className="ml-1 text-muted-foreground">{p.name}</span>
                    </td>
                    <td className="px-5 py-3 text-muted-foreground" title={EXPLICACION_TIPO[p.tipo]}>
                      {ETIQUETA_TIPO[p.tipo]}
                    </td>
                    <td className="px-5 py-3">
                      {formatDate(p.fecha_compra)}
                      <br />
                      <span className="text-muted-foreground">
                        {p.cantidad} × {formatPrecio(p.precio_compra, p.moneda)}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      {p.valor_actual_euros != null ? formatPrecio(p.valor_actual_euros, p.moneda) : '—'}
                    </td>
                    <td
                      className={cn(
                        'px-5 py-3 text-right font-medium',
                        p.ganancia_perdida_pct != null && (p.ganancia_perdida_pct >= 0 ? 'text-success' : 'text-danger'),
                      )}
                    >
                      {p.ganancia_perdida_pct != null
                        ? `${formatEuro(p.ganancia_perdida_euros ?? 0)} (${formatPct(p.ganancia_perdida_pct)})`
                        : '—'}
                    </td>
                    <td className="px-5 py-3 text-xs text-muted-foreground">{p.aviso ?? '—'}</td>
                    <td className="px-5 py-3 text-right">
                      <Button variant="ghost" size="sm" onClick={() => borrar.mutate(p.id)}>
                        Borrar
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
