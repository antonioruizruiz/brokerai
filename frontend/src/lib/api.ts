const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface Company {
  ticker: string
  name: string
  sector: string
  indice: string | null
  moneda: string
  activa: boolean
  last_price: number | null
  change_pct: number | null
  last_price_date: string | null
}

export interface CompanyCreateInput {
  ticker: string
  name: string
  sector: string
  moneda: string
}

export interface IndiceInfo {
  indice: string | null
  nombre: string
  n_empresas: number
}

export interface PriceBar {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface NewsItem {
  title: string
  publisher: string | null
  link: string
  published_at: string | null
}

export interface RankingItem {
  ticker: string
  name: string
  sector: string
  indice: string | null
  moneda: string
  activa: boolean
  momentum: number | null
  tendencia: number | null
  estabilidad: number | null
  fuerza_sector: number | null
  score_global: number | null
  distancia_maximo_52_semanas_pct: number | null
  volumen_relativo: number | null
}

export interface SyncEstado {
  descarga_completa_en_progreso: boolean
  ultima_descarga_completa: string | null
  ultima_actualizacion_horaria: string | null
  ultimo_error: string | null
}

export interface TradingSettings {
  capital_total: number
  riesgo_pct_operacion: number
  comision_pct: number
  comision_minima: number
  deslizamiento_pct: number
}

export interface Recomendacion {
  ticker: string
  name: string
  sector: string
  indice: string | null
  moneda: string
  activa: boolean
  regla: string
  motivo: string
  entrada: number
  stop: number
  objetivo: number
  plazo: string
  acciones: number
  beneficio_riesgo_neto: number | null
  riesgo: 'bajo' | 'medio' | 'alto' | 'desconocido'
}

export interface Vigilancia {
  ticker: string
  name: string
  sector: string
  indice: string | null
  moneda: string
  activa: boolean
  regla: string
  motivo: string
}

export interface Recomendaciones {
  recomendaciones: Recomendacion[]
  vigilancia: Vigilancia[]
}

export interface OperacionBacktest {
  ticker: string
  name: string
  moneda: string
  regla: string
  fecha_entrada: string
  fecha_salida: string
  dias_en_posicion: number
  entrada: number
  stop: number
  objetivo: number
  precio_salida: number
  motivo_salida: 'objetivo' | 'stop' | 'tiempo'
  acciones: number
  beneficio_neto_euros: number
  retorno_pct: number
  beneficio_riesgo_neto: number | null
  acierto: boolean
}

export interface ResumenRegla {
  n_operaciones: number
  tasa_acierto_pct: number | null
  retorno_medio_pct: number | null
  beneficio_riesgo_neto_medio: number | null
}

export interface ComparacionIndice {
  fecha_inicio: string
  fecha_fin: string
  retorno_total_pct: number
  retorno_anualizado_pct: number | null
}

export interface Fiabilidad {
  resumen_global: ResumenRegla
  por_regla: Record<string, ResumenRegla>
  seguimiento_medio: Record<string, number | null>
  comparacion_indice: ComparacionIndice | null
  comparacion_indice_nota: string | null
  operaciones: OperacionBacktest[]
}

export type TipoPosicion = 'corto_plazo' | 'largo_plazo' | 'dividendos'

export interface PortfolioEntryInput {
  ticker: string
  fecha_compra: string
  precio_compra: number
  cantidad: number
  tipo: TipoPosicion
  notas?: string | null
}

export interface PortfolioEntry {
  id: number
  ticker: string
  name: string
  moneda: string
  fecha_compra: string
  precio_compra: number
  cantidad: number
  tipo: TipoPosicion
  notas: string | null
  precio_actual: number | null
  valor_actual_euros: number | null
  ganancia_perdida_euros: number | null
  ganancia_perdida_pct: number | null
  aviso: string | null
}

export interface ResumenCartera {
  valor_invertido_euros: number
  valor_actual_euros: number | null
  ganancia_perdida_euros: number | null
  ganancia_perdida_pct: number | null
}

export interface Cartera {
  posiciones: PortfolioEntry[]
  resumen: ResumenCartera
}

export interface DividendoHistorial {
  date: string
  amount: number
}

export interface DividendoResumen {
  ticker: string
  name: string
  sector: string
  indice: string | null
  moneda: string
  activa: boolean
  last_price: number | null
  rentabilidad_pct: number | null
  total_ultimo_anio_euros: number | null
  fecha_ultimo: string | null
  importe_ultimo: number | null
  fecha_estimada_proximo: string | null
  historial: DividendoHistorial[]
}

function conIndice(path: string, indice?: string | null): string {
  return indice ? `${path}${path.includes('?') ? '&' : '?'}indice=${encodeURIComponent(indice)}` : path
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`)
  if (!res.ok) {
    throw new Error(`Error ${res.status} al llamar a ${path}`)
  }
  return res.json() as Promise<T>
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(`Error ${res.status} al llamar a ${path}`)
  }
  return res.json() as Promise<T>
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const detalle = await res.json().catch(() => null)
    throw new Error(detalle?.detail ?? `Error ${res.status} al llamar a ${path}`)
  }
  return res.json() as Promise<T>
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const detalle = await res.json().catch(() => null)
    throw new Error(detalle?.detail ?? `Error ${res.status} al llamar a ${path}`)
  }
  return res.json() as Promise<T>
}

async function del(path: string): Promise<void> {
  const res = await fetch(`${API_URL}${path}`, { method: 'DELETE' })
  if (!res.ok) {
    const detalle = await res.json().catch(() => null)
    throw new Error(detalle?.detail ?? `Error ${res.status} al llamar a ${path}`)
  }
}

export function getIndices(): Promise<IndiceInfo[]> {
  return get<IndiceInfo[]>('/api/indices')
}

export function getCompanies(indice?: string | null): Promise<Company[]> {
  return get<Company[]>(conIndice('/api/companies', indice))
}

export function crearEmpresaSuelta(datos: CompanyCreateInput): Promise<Company> {
  return post<Company>('/api/companies', datos)
}

export function getCompany(ticker: string): Promise<Company> {
  return get<Company>(`/api/companies/${ticker}`)
}

export function actualizarActivaEmpresa(ticker: string, activa: boolean): Promise<Company> {
  return patch<Company>(`/api/companies/${ticker}`, { activa })
}

export function borrarEmpresaSuelta(ticker: string): Promise<void> {
  return del(`/api/companies/${ticker}`)
}

export function getCompanyPrices(ticker: string): Promise<PriceBar[]> {
  return get<PriceBar[]>(`/api/companies/${ticker}/prices`)
}

export function getCompanyNews(ticker: string): Promise<NewsItem[]> {
  return get<NewsItem[]>(`/api/companies/${ticker}/news`)
}

export function getRanking(indice?: string | null): Promise<RankingItem[]> {
  return get<RankingItem[]>(conIndice('/api/ranking', indice))
}

export function getSettings(): Promise<TradingSettings> {
  return get<TradingSettings>('/api/settings')
}

export function updateSettings(datos: TradingSettings): Promise<TradingSettings> {
  return put<TradingSettings>('/api/settings', datos)
}

export function getRecomendaciones(indice?: string | null): Promise<Recomendaciones> {
  return get<Recomendaciones>(conIndice('/api/recomendaciones', indice))
}

export function getFiabilidad(indice?: string | null): Promise<Fiabilidad> {
  return get<Fiabilidad>(conIndice('/api/fiabilidad', indice))
}

export function getCartera(): Promise<Cartera> {
  return get<Cartera>('/api/cartera')
}

export function crearPosicionCartera(datos: PortfolioEntryInput): Promise<PortfolioEntry> {
  return post<PortfolioEntry>('/api/cartera', datos)
}

export function borrarPosicionCartera(id: number): Promise<void> {
  return del(`/api/cartera/${id}`)
}

export function getDividendos(indice?: string | null): Promise<DividendoResumen[]> {
  return get<DividendoResumen[]>(conIndice('/api/dividendos', indice))
}

export function getSyncEstado(): Promise<SyncEstado> {
  return get<SyncEstado>('/api/sync/estado')
}

export function lanzarDescargaCompleta(): Promise<{ detail: string }> {
  return post<{ detail: string }>('/api/sync/descarga-completa', {})
}
