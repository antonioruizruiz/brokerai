from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    name: str
    sector: str
    indice: str | None = None
    moneda: str = "EUR"
    activa: bool = True
    last_price: float | None = None
    change_pct: float | None = None
    last_price_date: date | None = None


class CompanyCreateIn(BaseModel):
    ticker: str
    name: str
    sector: str
    moneda: str = "EUR"


class CompanyActivaIn(BaseModel):
    activa: bool


class NewsItemOut(BaseModel):
    title: str
    publisher: str | None = None
    link: str
    published_at: datetime | None = None


class TradingSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    capital_total: float
    riesgo_pct_operacion: float
    comision_pct: float
    comision_minima: float
    deslizamiento_pct: float


class TradingSettingsIn(BaseModel):
    capital_total: float
    riesgo_pct_operacion: float
    comision_pct: float
    comision_minima: float
    deslizamiento_pct: float


class RankingItemOut(BaseModel):
    ticker: str
    name: str
    sector: str
    indice: str | None = None
    moneda: str = "EUR"
    activa: bool = True
    momentum: float | None = None
    tendencia: float | None = None
    estabilidad: float | None = None
    fuerza_sector: float | None = None
    score_global: float | None = None
    distancia_maximo_52_semanas_pct: float | None = None
    volumen_relativo: float | None = None


class RecomendacionOut(BaseModel):
    ticker: str
    name: str
    sector: str
    indice: str | None = None
    moneda: str = "EUR"
    activa: bool = True
    regla: str
    motivo: str
    entrada: float
    stop: float
    objetivo: float
    plazo: str
    acciones: int
    beneficio_riesgo_neto: float | None = None
    riesgo: str


class VigilanciaOut(BaseModel):
    ticker: str
    name: str
    sector: str
    indice: str | None = None
    moneda: str = "EUR"
    activa: bool = True
    regla: str
    motivo: str


class RecomendacionesOut(BaseModel):
    recomendaciones: list[RecomendacionOut]
    vigilancia: list[VigilanciaOut]


class OperacionBacktestOut(BaseModel):
    ticker: str
    name: str
    moneda: str = "EUR"
    regla: str
    fecha_entrada: date
    fecha_salida: date
    dias_en_posicion: int
    entrada: float
    stop: float
    objetivo: float
    precio_salida: float
    motivo_salida: str
    acciones: int
    beneficio_neto_euros: float
    retorno_pct: float
    beneficio_riesgo_neto: float | None = None
    acierto: bool


class ResumenReglaOut(BaseModel):
    n_operaciones: int
    tasa_acierto_pct: float | None = None
    retorno_medio_pct: float | None = None
    beneficio_riesgo_neto_medio: float | None = None


class ComparacionIndiceOut(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    retorno_total_pct: float
    retorno_anualizado_pct: float | None = None


class PortfolioEntryIn(BaseModel):
    ticker: str
    fecha_compra: date
    precio_compra: float
    cantidad: int
    tipo: Literal["corto_plazo", "largo_plazo", "dividendos"]
    notas: str | None = None


class PortfolioEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    name: str
    moneda: str = "EUR"
    fecha_compra: date
    precio_compra: float
    cantidad: int
    tipo: str
    notas: str | None = None
    precio_actual: float | None = None
    fecha_precio_actual: date | None = None
    valor_actual_euros: float | None = None
    ganancia_perdida_euros: float | None = None
    ganancia_perdida_pct: float | None = None
    aviso: str | None = None


class ResumenCarteraOut(BaseModel):
    valor_invertido_euros: float
    valor_actual_euros: float | None = None
    ganancia_perdida_euros: float | None = None
    ganancia_perdida_pct: float | None = None


class CarteraOut(BaseModel):
    posiciones: list[PortfolioEntryOut]
    resumen: ResumenCarteraOut


class DividendoHistorialOut(BaseModel):
    date: date
    amount: float


class DividendoResumenOut(BaseModel):
    ticker: str
    name: str
    sector: str
    indice: str | None = None
    moneda: str = "EUR"
    activa: bool = True
    last_price: float | None = None
    rentabilidad_pct: float | None = None
    total_ultimo_anio_euros: float | None = None
    fecha_ultimo: date | None = None
    importe_ultimo: float | None = None
    fecha_estimada_proximo: date | None = None
    historial: list[DividendoHistorialOut]


class FiabilidadOut(BaseModel):
    resumen_global: ResumenReglaOut
    por_regla: dict[str, ResumenReglaOut]
    seguimiento_medio: dict[str, float | None]
    comparacion_indice: ComparacionIndiceOut | None = None
    comparacion_indice_nota: str | None = None
    operaciones: list[OperacionBacktestOut]


class IndiceOut(BaseModel):
    indice: str | None
    nombre: str
    n_empresas: int


class PriceBarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class SyncEstadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    descarga_completa_en_progreso: bool
    ultima_descarga_completa: datetime | None = None
    ultima_actualizacion_horaria: datetime | None = None
    ultimo_error: str | None = None
