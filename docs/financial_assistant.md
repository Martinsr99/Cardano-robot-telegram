# Financial Assistant

El Asistente Financiero es un módulo especializado en análisis técnico y de mercado que proporciona predicciones de precios para activos financieros.

## Características

- **Análisis técnico**: Genera análisis técnicos detallados para cualquier activo financiero.
- **Predicciones de precios**: Proporciona predicciones de rango de precios para las próximas 24 horas.
- **Comparación con análisis previos**: Compara las predicciones actuales con análisis anteriores para evaluar la precisión.
- **Integración con Telegram**: Permite recibir pronósticos financieros directamente en Telegram.
- **Reutilización de análisis recientes**: Para evitar generar análisis innecesarios, reutiliza análisis recientes si no ha pasado el tiempo mínimo configurado.

## Uso desde la línea de comandos

Se puede utilizar el script `financial_forecast.py` para generar pronósticos desde la línea de comandos:

```bash
python financial_forecast.py BTC                # Genera un pronóstico para Bitcoin
python financial_forecast.py ETH                # Genera un pronóstico para Ethereum
python financial_forecast.py BTC force          # Fuerza un nuevo análisis para Bitcoin
python financial_forecast.py --list             # Lista todos los análisis guardados
python financial_forecast.py --list-open        # Lista los análisis abiertos
python financial_forecast.py --list-closed      # Lista los análisis cerrados
python financial_forecast.py --details ID       # Muestra detalles de un análisis específico
python financial_forecast.py --delete ID        # Elimina un análisis específico
python financial_forecast.py --clean            # Limpia análisis con datos incorrectos
```

### Configuración del tiempo mínimo entre análisis

El sistema está configurado para reutilizar análisis recientes si no ha pasado un tiempo mínimo desde el último análisis. Este tiempo se puede configurar mediante la variable de entorno `FINANCIAL_ANALYSIS_MIN_INTERVAL` (en horas). Por defecto, es de 4 horas.

```bash
# Establecer el tiempo mínimo a 2 horas
export FINANCIAL_ANALYSIS_MIN_INTERVAL=2
python financial_forecast.py BTC

# Forzar un nuevo análisis independientemente del tiempo transcurrido
python financial_forecast.py BTC force
```

## Uso desde Telegram

El asistente financiero está integrado con el bot de Telegram y proporciona los siguientes comandos:

- `/financial_forecast [SYMBOL]`: Genera un pronóstico financiero para el activo especificado.
- `/financial_forecast [SYMBOL] force`: Fuerza un nuevo análisis independientemente del tiempo transcurrido.
- `/financial_analyses [SYMBOL] [LIMIT]`: Muestra los análisis guardados, opcionalmente filtrados por símbolo y limitados a un número específico.

Ejemplos:
```
/financial_forecast BTC
/financial_forecast ETH force
/financial_analyses BTC 3
/financial_analyses 5
```

## Estructura de datos

El asistente financiero almacena los análisis en el directorio `forecast_system/data/financial_analysis` en formato JSON. Cada análisis contiene la siguiente información:

- **ID**: Identificador único del análisis.
- **Asset**: Símbolo del activo analizado.
- **Current Price**: Precio actual del activo en el momento del análisis.
- **Timestamp**: Fecha y hora del análisis.
- **Prediction**: Predicción generada, que incluye:
  - **Trend**: Tendencia esperada (ALCISTA, BAJISTA, LATERAL).
  - **Min Price**: Precio mínimo esperado.
  - **Max Price**: Precio máximo esperado.
  - **Likely Price**: Precio más probable.
  - **Support**: Nivel de soporte clave.
  - **Resistance**: Nivel de resistencia clave.
  - **Comments**: Comentarios adicionales sobre el análisis.

## Evaluación de predicciones

El asistente financiero evalúa automáticamente las predicciones anteriores cuando se genera un nuevo análisis para el mismo activo. La evaluación incluye:

- **Precio actual vs. precio predicho**: Diferencia entre el precio actual y el precio predicho.
- **Dentro del rango**: Indica si el precio actual está dentro del rango predicho.
- **Precisión**: Clasificación de la predicción como ACERTADA, PARCIAL o FALLIDA.

## Integración con el sistema de pronóstico

El asistente financiero está integrado con el sistema de pronóstico existente y puede utilizar sus funcionalidades para mejorar las predicciones. Esto incluye:

- **Modelos de IA**: Utiliza modelos de IA entrenados para mejorar las predicciones.
- **Alertas de precio**: Genera alertas cuando se detectan movimientos significativos.
- **Seguimiento de posiciones**: Permite seguir posiciones abiertas basadas en las predicciones.

## Desarrollo

Para extender o modificar el asistente financiero, se pueden editar los siguientes archivos:

- `src/financial_assistant.py`: Implementación principal del asistente financiero.
- `tests/test_financial_assistant.py`: Pruebas para el asistente financiero.
- `financial_forecast.py`: Script de línea de comandos para generar pronósticos.

### Nota sobre fuentes de datos

El sistema actualmente utiliza Yahoo Finance a través de la biblioteca yfinance para obtener datos de mercado. En un entorno de producción, es recomendable:

1. Utilizar una API financiera más confiable como Alpha Vantage, CoinGecko o un servicio de pago.
2. Asegurarse de que los símbolos estén correctamente formateados para la API que se está utilizando.
3. Verificar la calidad de los datos antes de generar pronósticos.

Para cambiar la fuente de datos, modifique la clase `MarketData` en `src/data_provider.py`.

## Ejemplo de salida

```
📈 Predicción para BTC - 2025-04-21 16:46

🔮 Tendencia esperada: LATERAL 
📊 Rango estimado: $38800.0000 - $39500.0000 
🛑 Soporte clave: $38800.0000 
📈 Resistencia clave: $39500.0000

💡 Comentarios adicionales: La acción del precio de BTC muestra un comportamiento lateral con una consolidación alrededor del nivel actual de $39.1350. No se observan patrones de reversión claros ni impulso significativo que sugiera una ruptura inminente. La volatilidad parece ser baja lo que podría mantener el precio dentro del rango estrecho especificado. Se recomienda monitorear cualquier cambio en el volumen de trading que pueda indicar un movimiento más decisivo.
