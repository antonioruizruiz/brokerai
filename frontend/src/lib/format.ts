const LOCALE_POR_MONEDA: Record<string, string> = {
  EUR: 'es-ES',
  USD: 'en-US',
  CHF: 'de-CH',
  DKK: 'da-DK',
  GBP: 'en-GB',
}

export function formatPrecio(value: number, moneda: string = 'EUR'): string {
  const locale = LOCALE_POR_MONEDA[moneda] ?? 'en-US'
  return new Intl.NumberFormat(locale, { style: 'currency', currency: moneda }).format(value)
}

export function formatEuro(value: number): string {
  return formatPrecio(value, 'EUR')
}

export function formatPct(value: number): string {
  const signo = value > 0 ? '+' : ''
  return `${signo}${value.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} %`
}

export function formatDate(iso: string): string {
  const [year, month, day] = iso.split('-')
  return `${day}/${month}/${year}`
}

export function formatDateTime(isoUtc: string): string {
  const fecha = new Date(isoUtc.endsWith('Z') ? isoUtc : `${isoUtc}Z`)
  return fecha.toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Europe/Madrid',
  })
}
