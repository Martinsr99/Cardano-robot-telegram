# Sistema de Pronóstico con Retroalimentación para Trading Bot

Este sistema proporciona capacidades avanzadas de pronóstico de precios con retroalimentación y aprendizaje automático para el bot de trading.

## Características Principales

- **Pronósticos de Rango de Precios**: Genera pronósticos para diferentes horizontes temporales (corto, medio y largo plazo)
- **Evaluación Automática**: Compara pronósticos con resultados reales para medir precisión
- **Aprendizaje con IA**: Mejora los pronósticos con el tiempo mediante modelos de aprendizaje automático
- **Visualización**: Genera gráficos comparativos entre pronósticos y precios reales
- **Integración con Telegram**: Comandos para solicitar pronósticos y ver estadísticas de precisión

## Estructura del Sistema

```
forecast_system/
├── data/                      # Almacenamiento de datos históricos
├── models/                    # Modelos de IA para mejorar pronósticos
│   ├── saved/                 # Modelos entrenados guardados
│   └── forecast_model.py      # Implementación de modelos de IA
├── utils/                     # Utilidades comunes
├── visualization/             # Visualización de pronósticos y resultados
│   ├── output/                # Gráficos generados
│   └── forecast_visualizer.py # Generador de visualizaciones
├── forecast_manager.py        # Gestión de pronósticos y evaluaciones
├── forecast_system.py         # Sistema principal de pronóstico
├── integration.py             # Integración con el bot de trading
└── README.md                  # Este archivo
```

## Funcionamiento

### Generación de Pronósticos

El sistema genera pronósticos de rango de precios para tres horizontes temporales:

1. **Corto plazo (24h)**: Pronóstico para las próximas 24 horas
2. **Medio plazo (3-5 días)**: Pronóstico para los próximos 3-5 días
3. **Largo plazo (1-2 semanas)**: Pronóstico para las próximas 1-2 semanas

Cada pronóstico incluye:
- Rango de precios (mínimo y máximo)
- Precio más probable
- Niveles de soporte y resistencia
- Nivel de confianza

### Evaluación y Retroalimentación

El sistema evalúa automáticamente los pronósticos comparándolos con los precios reales:

1. Al iniciar, comprueba el último pronóstico contra el precio actual
2. Registra evaluaciones para diferentes horizontes temporales
3. Calcula métricas de precisión (error porcentual, tasa de acierto en rango)
4. Genera estadísticas de precisión a lo largo del tiempo

### Mejora con IA

El sistema utiliza modelos de aprendizaje automático para mejorar los pronósticos:

1. Entrena modelos con datos históricos de pronósticos y evaluaciones
2. Identifica patrones y factores que afectan la precisión
3. Ajusta los pronósticos futuros basándose en el aprendizaje
4. Mejora continuamente con más datos y evaluaciones

## Comandos de Telegram

El sistema añade dos nuevos comandos a Telegram:

- `/forecast`: Genera un nuevo pronóstico de rango de precios
- `/accuracy`: Muestra estadísticas de precisión del sistema de pronóstico

## Integración con el Bot

El sistema se integra con el bot de trading existente:

1. Al iniciar, comprueba el último pronóstico
2. Genera un nuevo pronóstico si no hay uno reciente
3. Registra y evalúa pronósticos automáticamente
4. Proporciona comandos de Telegram para interactuar con el sistema

## Requisitos

- Python 3.8+
- NumPy, Pandas, Matplotlib, Seaborn
- scikit-learn para modelos de IA
- Acceso a datos históricos de precios

## Uso

El sistema se inicia automáticamente con el bot de trading:

```bash
python main.py --monitor  # Modo monitor
python main.py --ui       # Modo interfaz gráfica
```

## Desarrollo Futuro

- Incorporación de más indicadores técnicos para mejorar pronósticos
- Modelos de IA más avanzados (redes neuronales, series temporales)
- Análisis de sentimiento de mercado y factores externos
- Exportación de pronósticos a formatos externos
