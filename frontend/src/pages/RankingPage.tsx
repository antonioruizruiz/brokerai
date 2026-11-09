import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, ReferenceLine, XAxis, YAxis } from 'recharts'
import { Link } from 'react-router-dom'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getRanking, type RankingItem } from '@/lib/api'
import { TODOS, useIndiceSeleccionado } from '@/lib/indiceContext'
import { cn } from '@/lib/utils'

const FACTORES: { clave: keyof RankingItem; etiqueta: string; explicacion: string }[] = [
  {
    clave: 'momentum',
    etiqueta: 'Momentum',
    explicacion:
      'Cuánto ha subido (o bajado) el precio en el último año, sin contar el último mes, comparado con las demás empresas de la cesta seleccionada. Un valor alto indica que ha subido más que la mayoría; uno bajo, que ha subido menos o ha caído más.',
  },
  {
    clave: 'tendencia',
    etiqueta: 'Tendencia',
    explicacion:
      'Compara el precio de hoy con sus medias de los últimos 50 y 200 días de cotización. Si el precio está por encima de esas medias la tendencia es alcista; si está por debajo, bajista. Un valor alto significa una tendencia más alcista que la del resto de la cesta.',
  },
  {
    clave: 'estabilidad',
    etiqueta: 'Estabilidad',
    explicacion:
      'Mide lo bruscos que son los sube y baja diarios del precio (la volatilidad) en los últimos meses. Un valor alto indica una cotización más tranquila, con menos sobresaltos, que la de las demás empresas; uno bajo, un valor que se mueve con fuerza en ambas direcciones.',
  },
  {
    clave: 'fuerza_sector',
    etiqueta: 'Fuerza del sector',
    explicacion:
      'Cómo de bien le está yendo, en conjunto, al sector de la empresa (p. ej. Banca, Energía, Construcción) frente a los demás sectores de la cesta seleccionada. Un valor alto significa que ese sector, en general, está subiendo más que el resto del mercado.',
  },
]

function BarraFactor({ valor }: { valor: number | null }) {
  if (valor == null) {
    return <span className="text-muted-foreground">—</span>
  }
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
        <div
          className={cn('h-full rounded-full', valor >= 50 ? 'bg-success' : 'bg-danger')}
          style={{ width: `${valor}%` }}
        />
      </div>
      <span className="w-9 text-right tabular-nums">{valor.toFixed(0)}</span>
    </div>
  )
}

export function RankingPage() {
  const { indice, indiceParaApi } = useIndiceSeleccionado()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['ranking', indiceParaApi],
    queryFn: () => getRanking(indiceParaApi),
  })
  const [tickerSeleccionado, setTickerSeleccionado] = useState<string | null>(null)

  const empresaSeleccionada = data?.find((fila) => fila.ticker === tickerSeleccionado) ?? data?.[0]

  const datosGrafico = empresaSeleccionada
    ? FACTORES.map(({ clave, etiqueta }) => ({
        factor: etiqueta,
        valor: empresaSeleccionada[clave] as number | null,
      }))
    : []

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Ranking</h1>
        <p className="text-sm text-muted-foreground">
          Factores de 0 a 100 calculados comparando cada empresa con el resto de la cesta seleccionada arriba a la
          derecha ({indice === TODOS ? 'todas las empresas seguidas' : indice} — 100 = la mejor de la cesta hoy en
          ese factor). Solo con datos de precio y volumen: de momento no incluye calidad ni valoración. No es una
          recomendación de compra o venta.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>¿Qué significa cada factor?</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 sm:grid-cols-2">
            {FACTORES.map(({ clave, etiqueta, explicacion }) => (
              <div key={clave}>
                <dt className="font-medium">{etiqueta}</dt>
                <dd className="text-sm text-muted-foreground">{explicacion}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-4 text-sm text-muted-foreground">
            El <strong>Score</strong> es la media de los cuatro factores. En todos los casos, 50 es el valor
            "normal" (ni mejor ni peor que el resto de la cesta seleccionada); por debajo de 50 está peor que la
            media en ese aspecto, por encima está mejor.
          </p>
        </CardContent>
      </Card>

      {empresaSeleccionada && (
        <Card>
          <CardHeader>
            <CardTitle>Factores frente al mercado: {empresaSeleccionada.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <BarChart width={560} height={220} data={datosGrafico} layout="vertical" margin={{ left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis type="category" dataKey="factor" width={120} />
              <ReferenceLine x={50} stroke="#64748b" strokeDasharray="4 4" />
              <Bar dataKey="valor" fill="#4338ca" radius={[0, 4, 4, 0]} />
            </BarChart>
          </CardContent>
        </Card>
      )}

      <Card className="overflow-hidden">
        {isLoading && <p className="p-5 text-muted-foreground">Cargando...</p>}
        {isError && <p className="p-5 text-danger">No se ha podido conectar con el backend.</p>}

        {data && (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th className="px-5 py-3 font-medium">Empresa</th>
                <th className="px-5 py-3 font-medium">Sector</th>
                <th className="px-5 py-3 text-right font-medium">Score</th>
                {FACTORES.map(({ clave, etiqueta, explicacion }) => (
                  <th key={clave} className="cursor-help px-5 py-3 font-medium" title={explicacion}>
                    {etiqueta}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((fila) => (
                <tr
                  key={fila.ticker}
                  onClick={() => setTickerSeleccionado(fila.ticker)}
                  className={cn(
                    'cursor-pointer border-b border-border last:border-0 hover:bg-muted',
                    fila.ticker === empresaSeleccionada?.ticker && 'bg-muted',
                  )}
                >
                  <td className="px-5 py-3">
                    <Link
                      to={`/mercado/${fila.ticker}`}
                      onClick={(e) => e.stopPropagation()}
                      className="font-medium text-primary"
                    >
                      {fila.ticker}
                    </Link>
                    <span className="ml-2 text-muted-foreground">{fila.name}</span>
                    {!fila.activa && (
                      <span className="ml-2 rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                        Inactiva
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-muted-foreground">{fila.sector}</td>
                  <td className="px-5 py-3 text-right font-semibold tabular-nums">
                    {fila.score_global != null ? fila.score_global.toFixed(1) : '—'}
                  </td>
                  {FACTORES.map(({ clave }) => (
                    <td key={clave} className="px-5 py-3">
                      <BarraFactor valor={fila[clave] as number | null} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
