# Guía de recomendaciones y gráficos

Esta guía explica cómo leer las páginas **Ranking**, **Hoy**, **Fiabilidad** y la ficha de una empresa. Describe el comportamiento que tiene actualmente el código; no representa una promesa de rentabilidad ni asesoramiento financiero.

## Qué queda por hacer

Según las casillas pendientes de [ROADMAP.md](ROADMAP.md), las fases 1 a 5 y la fase 7 están marcadas como terminadas. Quedan estos pasos:

1. **Decidir si se activa la revisión con IA.** La fase 6 está aplazada hasta disponer de una clave de la API de Anthropic. Esa revisión debería estudiar noticias y hechos relevantes y poder pedir prudencia o descartar una señal; no inventar compras. También falta registrar tokens/coste y mostrarlos en Ajustes. La licencia de Claude.ai no equivale por sí sola a una clave de la API de pago por uso.
2. **Probar el despliegue completo en local.** La fase 8 tiene Dockerfiles, Compose, PostgreSQL, Caddy, autenticación y copias de seguridad, pero el roadmap dice que falta probar el conjunto. La guía de ejecución está en [deploy/LEEME.md](deploy/LEEME.md). En particular, hay que comprobar acceso con contraseña, reinicio conservando los datos, tarea diaria y backup/restauración.
3. **Decidir cuándo pasar al VPS.** Contratarlo, apuntar un dominio y activar HTTPS son tareas posteriores y opcionales hasta que quieras publicar la aplicación. No hace falta abrir los puertos del backend ni PostgreSQL a Internet.

La descarga histórica y el análisis local ya funcionan; las incidencias recientes de watchdog y volúmenes grandes se corrigieron en código y se probaron. Eso no sustituye la prueba de extremo a extremo del despliegue de la fase 8.

## De los datos a una recomendación

El proceso actual es mecánico y se puede resumir así:

1. **Datos de mercado.** Se usa Yahoo Finance mediante `yfinance` para obtener velas diarias y dividendos. La información puede venir retrasada, revisarse o faltar; no es un feed profesional garantizado.
2. **Indicadores y Ranking.** A partir de precios y volumen se calculan momentum, tendencia, estabilidad y fuerza del sector. Cada factor se expresa como percentil frente a la cesta seleccionada.
3. **Reglas de Hoy.** Dos reglas buscan posibles entradas: ruptura de máximos con volumen o retroceso cerca de la media de 50 sesiones durante una tendencia alcista.
4. **Plan mecánico.** Si hay señal, se calculan entrada, stop, objetivo, plazo, cantidad y beneficio/riesgo neto estimado de costes.
5. **Revisión humana.** Hoy no hay aprobación de Claude ni lectura automática de noticias/CNMV. La fase 6 está pendiente. La persona debe revisar la señal y sus datos antes de tomar cualquier decisión.

Una señal significa **“se cumplen estas condiciones técnicas”**, no “la acción va a subir”. Puede acabar en pérdida, saltar el stop con un hueco de precio o cambiar al actualizarse los datos.

## Ranking: qué significan los factores

El Ranking necesita aproximadamente **273 sesiones bursátiles** (un poco más de un año) para calcular todos los factores. Si no hay suficiente historial, aparece `—`.

| Factor | Qué calcula | Cómo interpretar 0–100 |
| --- | --- | --- |
| **Momentum** | Rentabilidad de aproximadamente los 12 meses anteriores, excluyendo el último mes (momentum 12-1). | Percentil frente a la cesta: 80 significa que está por encima de cerca del 80 % de los valores comparables en este indicador. No es un 80 % de probabilidad de ganar. |
| **Tendencia** | Compara el último cierre con las medias simples de 50 y 200 sesiones; combina ambas distancias a partes iguales. | Un percentil alto indica una posición más alcista que la mayoría de la cesta. |
| **Estabilidad** | Calcula la volatilidad anualizada de los retornos diarios de las últimas 60 sesiones. Menos volatilidad obtiene mejor percentil. | Un valor alto indica movimientos históricos más tranquilos en comparación con la cesta, no ausencia de riesgo. |
| **Fuerza del sector** | Calcula el momentum medio de las empresas de cada sector y compara los sectores entre sí. | Un valor alto indica que el sector ha tenido mejor momentum relativo; no necesariamente que la empresa concreta sea buena. |

El **Score** es la media simple de los cuatro factores. Por tanto, todos pesan igual y basta que uno sea bajo para reducir la media. En general, 50 representa una posición intermedia de la cesta actual, no una calificación absoluta.

La cesta depende del filtro elegido. Si se selecciona un índice, la comparación se limita a ese grupo. Si se eligen todas las empresas, se mezclan mercados y tamaños distintos, por lo que la comparación es menos homogénea. La puntuación puede cambiar aunque el precio de una empresa no cambie, si cambian las demás empresas de la cesta.

**Importante:** pese a que a veces se habla de factores “fundamentales”, el Ranking actual solo usa precios y volumen. Calidad de negocio, deuda, beneficios, valoración y noticias todavía no forman parte del cálculo.

## Hoy: reglas que pueden generar señales

Antes de probar las reglas se calculan los indicadores anteriores. Si falta historial suficiente, no se genera señal.

### Ruptura de máximos con volumen

- Compara el cierre actual con el máximo de los aproximadamente 252 días bursátiles anteriores, sin incluir el día actual.
- La señal se activa si el cierre supera ese máximo y el volumen del día alcanza al menos **1,5 veces** el volumen medio de las últimas 20 sesiones.
- La entrada propuesta es el cierre actual.
- El stop se sitúa en el mínimo de las últimas 10 sesiones.
- El plazo mostrado es corto: aproximadamente 2–4 semanas (20 sesiones en el backtest).
- Si el precio está hasta un 2 % por debajo del máximo previo, puede aparecer **En vigilancia**, sin plan de entrada.

### Retroceso en tendencia alcista

- La media de 50 sesiones debe estar por encima de la media de 200 sesiones.
- El cierre debe seguir por encima de la media de 200.
- Si el precio está entre 0 % y 2 % por encima de la media de 50, se activa la regla.
- La entrada propuesta es el cierre actual. El stop se coloca en el menor de estos dos niveles: la media de 200 o el mínimo de las últimas 10 sesiones.
- El plazo mostrado es medio: aproximadamente 1–3 meses (60 sesiones en el backtest).
- Si está hasta un 2 % por debajo de la media de 50, la empresa puede quedar **En vigilancia**, sin plan de entrada.

Cuando ambas reglas pudieran darse el mismo día, se prioriza la ruptura. “En vigilancia” significa que una condición se está acercando, no que la regla de entrada se haya activado.

### Cómo se calculan objetivo, acciones y riesgo

- **Riesgo por acción:** entrada menos stop. Si el stop no está por debajo de la entrada, no se genera plan.
- **Objetivo:** entrada más dos veces el riesgo por acción. Antes de costes, el objetivo busca una relación potencial de 2 a 1.
- **Presupuesto de riesgo:** capital configurado multiplicado por el porcentaje de riesgo por operación.
- **Acciones:** parte entera de presupuesto de riesgo dividido por riesgo por acción. El cálculo usa el riesgo hasta el stop; no debe confundirse con el valor total de la posición.
- **Beneficio/riesgo neto:** estima beneficio al objetivo y riesgo al stop, descontando comisión mínima o porcentual y deslizamiento tanto a la entrada como a la salida estimada.
- **Riesgo bajo/medio/alto:** es una clasificación basada únicamente en el percentil de estabilidad: 66 o más = bajo; 33 a menos de 66 = medio; menos de 33 = alto. No mide la probabilidad de pérdida ni sustituye un análisis del negocio.

Los costes reales, el precio de ejecución, los impuestos, la liquidez, los huecos de mercado y las restricciones del bróker pueden diferir de la simulación. El número de acciones se basa en el presupuesto de riesgo y no debe interpretarse por sí solo como una comprobación completa de efectivo disponible.

## Gráfico de velas de la ficha

Cada vela representa **una sesión diaria**. La fecha está en el eje horizontal y el precio en el vertical.

- **Apertura (`Open`):** primer precio de la sesión.
- **Máximo (`High`):** precio más alto alcanzado ese día.
- **Mínimo (`Low`):** precio más bajo.
- **Cierre (`Close`):** último precio de la sesión.
- **Cuerpo:** tramo entre apertura y cierre. En este gráfico, verde significa cierre igual o superior a apertura; rojo significa cierre inferior a apertura.
- **Mechas:** líneas por encima y por debajo del cuerpo hasta el máximo y el mínimo. Una mecha larga indica que el precio se movió bastante dentro de la sesión antes de cerrar.

Ejemplos de lectura:

- Vela verde larga: el cierre quedó bastante por encima de la apertura.
- Vela roja larga: el cierre quedó bastante por debajo.
- Cuerpo pequeño con mechas largas: hubo movimiento, pero apertura y cierre acabaron cerca; la sesión fue indecisa o revirtió parte del recorrido.
- La secuencia de velas ayuda a ver tendencia y cambios de ritmo, pero una vela aislada no predice la siguiente.

### Medias dibujadas sobre el precio

- **Media 50** (línea índigo): promedio simple de los últimos 50 cierres.
- **Media 200** (línea fucsia): promedio simple de los últimos 200 cierres.

Una media más corta suele reaccionar antes al precio y también puede cambiar de dirección con más frecuencia. La de 200 es más lenta. Que la media de 50 esté por encima de la de 200 es una de las condiciones de la regla de retroceso, pero por sí sola no produce una recomendación.

El gráfico actual **no dibuja volumen**; el volumen sí se usa en la regla de ruptura. Tampoco dibuja automáticamente las líneas de entrada, stop u objetivo: esos valores aparecen en Hoy. En días sin cotización, el eje temporal puede saltar fechas de calendario porque las velas son sesiones de mercado.

## Fiabilidad y backtest

El backtest recorre las reglas sobre datos históricos y simula operaciones sin solaparlas en la misma empresa. Usa el cierre de la señal como entrada, stop y objetivo calculados, y descuenta comisiones y deslizamiento.

- En ruptura usa un horizonte máximo de 20 sesiones; en retroceso, 60.
- Si en una sesión futura se toca el stop, el backtest registra primero el stop; si no, comprueba el objetivo. Si no se toca ninguno, sale al cierre del horizonte.
- La página resume cantidad de operaciones, porcentaje de operaciones con resultado neto positivo, retorno medio y seguimiento D+1/D+5/D+10/D+20. También compara el periodo con el índice de referencia disponible.

El backtest es una simulación sobre datos pasados, no una prueba de resultados futuros. Puede no representar deslizamientos reales, disponibilidad de precios durante el día, impuestos, liquidez o todos los cambios históricos del universo de empresas. La regla de prioridad cuando una misma vela toca stop y objetivo evita atribuir un resultado favorable sin saber el orden intradía, pero sigue siendo una simplificación.

## Dónde están los cálculos

- Indicadores y percentiles: [backend/app/services/scoring.py](backend/app/services/scoring.py)
- Reglas, niveles y tamaño de posición: [backend/app/services/recommendations.py](backend/app/services/recommendations.py)
- Simulación histórica: [backend/app/services/backtest.py](backend/app/services/backtest.py)
- Gráfico de velas y medias: [frontend/src/components/PriceChart.tsx](frontend/src/components/PriceChart.tsx)
- Estado de fases: [ROADMAP.md](ROADMAP.md)