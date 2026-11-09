import type { PriceBar } from '@/lib/api'

export interface RetornoPeriodo {
  etiqueta: string
  pct: number | null
}

export interface ResumenCotizacion {
  precioActual: number
  fechaActual: string
  retornos: RetornoPeriodo[]
}

function restarMeses(fecha: Date, meses: number): Date {
  const resultado = new Date(fecha)
  resultado.setMonth(resultado.getMonth() - meses)
  return resultado
}

function aIso(fecha: Date): string {
  return fecha.toISOString().slice(0, 10)
}

/** Cierre de la última sesión en `fechaObjetivo` o, si no cotizó ese día (fin de semana, festivo), la anterior. */
function cierreEnOAntesDe(bars: PriceBar[], fechaObjetivoIso: string): number | null {
  let resultado: number | null = null
  for (const bar of bars) {
    if (bar.date <= fechaObjetivoIso) {
      resultado = bar.close
    } else {
      break
    }
  }
  return resultado
}

function calcularPct(actual: number, referencia: number | null): number | null {
  if (referencia == null || referencia === 0) return null
  return ((actual - referencia) / referencia) * 100
}

/**
 * Calcula la cotización actual y la rentabilidad a 1D, 5D, 1M, 3M, YTD y 1Y a partir del
 * histórico de velas diarias ya descargado (bars ordenadas ascendentemente por fecha).
 * 1D y 5D se miden en sesiones de mercado (no en días naturales); el resto, en fechas de
 * calendario buscando la sesión más cercana en o antes de esa fecha.
 */
export function calcularResumenCotizacion(bars: PriceBar[]): ResumenCotizacion | null {
  if (bars.length === 0) return null

  const ultimo = bars[bars.length - 1]
  const fechaActual = new Date(`${ultimo.date}T00:00:00`)

  const referencia1D = bars.length >= 2 ? bars[bars.length - 2].close : null
  const referencia5D = bars.length >= 6 ? bars[bars.length - 6].close : null

  const periodosPorFecha: { etiqueta: string; fechaObjetivo: Date }[] = [
    { etiqueta: '1M', fechaObjetivo: restarMeses(fechaActual, 1) },
    { etiqueta: '3M', fechaObjetivo: restarMeses(fechaActual, 3) },
    { etiqueta: 'YTD', fechaObjetivo: new Date(fechaActual.getFullYear() - 1, 11, 31) },
    { etiqueta: '1Y', fechaObjetivo: restarMeses(fechaActual, 12) },
  ]

  const retornos: RetornoPeriodo[] = [
    { etiqueta: '1D', pct: calcularPct(ultimo.close, referencia1D) },
    { etiqueta: '5D', pct: calcularPct(ultimo.close, referencia5D) },
    ...periodosPorFecha.map(({ etiqueta, fechaObjetivo }) => ({
      etiqueta,
      pct: calcularPct(ultimo.close, cierreEnOAntesDe(bars, aIso(fechaObjetivo))),
    })),
  ]

  return { precioActual: ultimo.close, fechaActual: ultimo.date, retornos }
}
