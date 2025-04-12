"""
Forecast Visualizer - Visualización de pronósticos y comparación con resultados reales
"""

import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import seaborn as sns

class ForecastVisualizer:
    """
    Clase para visualizar pronósticos y comparar con resultados reales.
    """
    def __init__(self, output_dir: str = "forecast_system/visualization/output"):
        """
        Inicializa el visualizador de pronósticos.
        
        Args:
            output_dir: Directorio donde se guardarán las visualizaciones
        """
        self.output_dir = output_dir
        
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Configurar estilo de gráficos
        self._setup_plot_style()
    
    def _setup_plot_style(self):
        """Configura el estilo de los gráficos"""
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.titlesize'] = 16
        plt.rcParams['axes.labelsize'] = 14
    
    def plot_forecast_vs_actual(self, 
                               forecast: Dict[str, Any], 
                               actual_prices: Dict[str, float],
                               price_history: pd.DataFrame,
                               future_prices: Optional[pd.DataFrame] = None,
                               save_path: Optional[str] = None) -> str:
        """
        Genera un gráfico comparando el pronóstico con los precios reales.
        
        Args:
            forecast: Datos del pronóstico
            actual_prices: Precios reales para diferentes horizontes temporales
            price_history: DataFrame con historial de precios (columnas: 'date', 'price')
            future_prices: DataFrame con precios futuros si están disponibles
            save_path: Ruta donde guardar el gráfico (opcional)
            
        Returns:
            Ruta del archivo guardado
        """
        # Crear figura
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Extraer datos del pronóstico
        forecast_data = forecast["data"]
        forecast_date = datetime.fromisoformat(forecast["timestamp"])
        
        # Extraer precios históricos
        history_dates = price_history['date'].values
        history_prices = price_history['price'].values
        
        # Graficar precios históricos
        ax.plot(history_dates, history_prices, 'b-', label='Precio histórico', linewidth=2)
        
        # Graficar precios futuros si están disponibles
        if future_prices is not None:
            future_dates = future_prices['date'].values
            future_prices_values = future_prices['price'].values
            ax.plot(future_dates, future_prices_values, 'g-', label='Precio real (futuro)', linewidth=2)
        
        # Marcar fecha del pronóstico
        ax.axvline(x=forecast_date, color='k', linestyle='--', label='Fecha del pronóstico')
        
        # Añadir rangos de pronóstico
        self._add_forecast_ranges(ax, forecast_data, forecast_date)
        
        # Añadir puntos de precio real
        self._add_actual_price_points(ax, actual_prices, forecast_date)
        
        # Configurar ejes y leyenda
        ax.set_title(f'Pronóstico vs. Realidad - {forecast_date.strftime("%Y-%m-%d %H:%M")}')
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Precio (USD)')
        ax.legend(loc='best')
        
        # Formatear eje x
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.xticks(rotation=45)
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfico
        if save_path is None:
            save_path = os.path.join(self.output_dir, f'forecast_{forecast["id"]}.png')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return save_path
    
    def _add_forecast_ranges(self, ax, forecast_data: Dict[str, Any], forecast_date: datetime):
        """
        Añade los rangos de pronóstico al gráfico.
        
        Args:
            ax: Eje de matplotlib
            forecast_data: Datos del pronóstico
            forecast_date: Fecha del pronóstico
        """
        # Añadir rango a corto plazo (24h)
        short_term_date = forecast_date + timedelta(days=1)
        short_term_min = forecast_data["short_term"]["min"]
        short_term_max = forecast_data["short_term"]["max"]
        short_term_likely = forecast_data["short_term"]["likely"]
        
        ax.fill_between([forecast_date, short_term_date], 
                       [short_term_min, short_term_min], 
                       [short_term_max, short_term_max], 
                       alpha=0.3, color='blue', label='Rango 24h')
        
        ax.plot([forecast_date, short_term_date], 
               [short_term_likely, short_term_likely], 
               'b--', label='Precio más probable 24h')
        
        # Añadir rango a medio plazo (3-5 días)
        medium_term_date = forecast_date + timedelta(days=4)
        medium_term_min = forecast_data["medium_term"]["min"]
        medium_term_max = forecast_data["medium_term"]["max"]
        medium_term_likely = forecast_data["medium_term"]["likely"]
        
        ax.fill_between([short_term_date, medium_term_date], 
                       [medium_term_min, medium_term_min], 
                       [medium_term_max, medium_term_max], 
                       alpha=0.3, color='green', label='Rango 3-5 días')
        
        ax.plot([short_term_date, medium_term_date], 
               [medium_term_likely, medium_term_likely], 
               'g--', label='Precio más probable 3-5 días')
        
        # Añadir rango a largo plazo (1-2 semanas)
        long_term_date = forecast_date + timedelta(days=10)
        long_term_min = forecast_data["long_term"]["min"]
        long_term_max = forecast_data["long_term"]["max"]
        long_term_likely = forecast_data["long_term"]["likely"]
        
        ax.fill_between([medium_term_date, long_term_date], 
                       [long_term_min, long_term_min], 
                       [long_term_max, long_term_max], 
                       alpha=0.3, color='red', label='Rango 1-2 semanas')
        
        ax.plot([medium_term_date, long_term_date], 
               [long_term_likely, long_term_likely], 
               'r--', label='Precio más probable 1-2 semanas')
    
    def _add_actual_price_points(self, ax, actual_prices: Dict[str, float], forecast_date: datetime):
        """
        Añade los puntos de precio real al gráfico.
        
        Args:
            ax: Eje de matplotlib
            actual_prices: Precios reales para diferentes horizontes temporales
            forecast_date: Fecha del pronóstico
        """
        # Añadir precio real a 24h
        if "actual_24h" in actual_prices:
            actual_24h_date = forecast_date + timedelta(days=1)
            ax.scatter([actual_24h_date], [actual_prices["actual_24h"]], 
                      color='blue', s=100, marker='o', label='Precio real 24h')
        
        # Añadir precio real a 3 días
        if "actual_3d" in actual_prices:
            actual_3d_date = forecast_date + timedelta(days=3)
            ax.scatter([actual_3d_date], [actual_prices["actual_3d"]], 
                      color='green', s=100, marker='o', label='Precio real 3 días')
        
        # Añadir precio real a 7 días
        if "actual_7d" in actual_prices:
            actual_7d_date = forecast_date + timedelta(days=7)
            ax.scatter([actual_7d_date], [actual_prices["actual_7d"]], 
                      color='red', s=100, marker='o', label='Precio real 7 días')
    
    def plot_accuracy_over_time(self, evaluations: List[Dict[str, Any]], save_path: Optional[str] = None) -> str:
        """
        Genera un gráfico de la precisión de los pronósticos a lo largo del tiempo.
        
        Args:
            evaluations: Lista de evaluaciones de pronósticos
            save_path: Ruta donde guardar el gráfico (opcional)
            
        Returns:
            Ruta del archivo guardado
        """
        if not evaluations:
            raise ValueError("No hay evaluaciones para graficar")
        
        # Convertir a DataFrame
        data = []
        for eval in evaluations:
            timestamp = datetime.fromisoformat(eval["timestamp"])
            
            # Extraer errores para cada horizonte temporal
            short_term_error = eval["errors"].get("short_term", {}).get("error_pct", np.nan)
            medium_term_error = eval["errors"].get("medium_term", {}).get("error_pct", np.nan)
            long_term_error = eval["errors"].get("long_term", {}).get("error_pct", np.nan)
            
            data.append({
                "timestamp": timestamp,
                "short_term_error": short_term_error,
                "medium_term_error": medium_term_error,
                "long_term_error": long_term_error
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values("timestamp")
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Graficar errores
        ax.plot(df["timestamp"], df["short_term_error"], 'b-', label='Error a 24h', linewidth=2)
        ax.plot(df["timestamp"], df["medium_term_error"], 'g-', label='Error a 3-5 días', linewidth=2)
        ax.plot(df["timestamp"], df["long_term_error"], 'r-', label='Error a 1-2 semanas', linewidth=2)
        
        # Añadir línea de tendencia
        if len(df) >= 5:
            for col, color in zip(["short_term_error", "medium_term_error", "long_term_error"], 
                                 ['blue', 'green', 'red']):
                # Filtrar valores no nulos
                temp_df = df[~df[col].isna()]
                if len(temp_df) >= 5:
                    z = np.polyfit(range(len(temp_df)), temp_df[col], 1)
                    p = np.poly1d(z)
                    ax.plot(temp_df["timestamp"], p(range(len(temp_df))), 
                           f'{color}--', linewidth=1, alpha=0.7)
        
        # Configurar ejes y leyenda
        ax.set_title('Precisión de Pronósticos a lo Largo del Tiempo')
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Error (%)')
        ax.legend(loc='best')
        
        # Formatear eje x
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.xticks(rotation=45)
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfico
        if save_path is None:
            save_path = os.path.join(self.output_dir, 'accuracy_over_time.png')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return save_path
    
    def plot_accuracy_distribution(self, evaluations: List[Dict[str, Any]], save_path: Optional[str] = None) -> str:
        """
        Genera un gráfico de la distribución de errores de pronóstico.
        
        Args:
            evaluations: Lista de evaluaciones de pronósticos
            save_path: Ruta donde guardar el gráfico (opcional)
            
        Returns:
            Ruta del archivo guardado
        """
        if not evaluations:
            raise ValueError("No hay evaluaciones para graficar")
        
        # Extraer errores
        short_term_errors = [e["errors"].get("short_term", {}).get("error_pct", np.nan) 
                            for e in evaluations if "short_term" in e["errors"]]
        medium_term_errors = [e["errors"].get("medium_term", {}).get("error_pct", np.nan) 
                             for e in evaluations if "medium_term" in e["errors"]]
        long_term_errors = [e["errors"].get("long_term", {}).get("error_pct", np.nan) 
                           for e in evaluations if "long_term" in e["errors"]]
        
        # Filtrar valores no nulos
        short_term_errors = [e for e in short_term_errors if not np.isnan(e)]
        medium_term_errors = [e for e in medium_term_errors if not np.isnan(e)]
        long_term_errors = [e for e in long_term_errors if not np.isnan(e)]
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Graficar distribuciones
        if short_term_errors:
            sns.kdeplot(short_term_errors, ax=ax, label='Error a 24h', color='blue')
        if medium_term_errors:
            sns.kdeplot(medium_term_errors, ax=ax, label='Error a 3-5 días', color='green')
        if long_term_errors:
            sns.kdeplot(long_term_errors, ax=ax, label='Error a 1-2 semanas', color='red')
        
        # Configurar ejes y leyenda
        ax.set_title('Distribución de Errores de Pronóstico')
        ax.set_xlabel('Error (%)')
        ax.set_ylabel('Densidad')
        ax.legend(loc='best')
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfico
        if save_path is None:
            save_path = os.path.join(self.output_dir, 'error_distribution.png')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return save_path
    
    def generate_forecast_report(self, 
                               forecast: Dict[str, Any], 
                               evaluation: Dict[str, Any],
                               price_history: pd.DataFrame,
                               future_prices: Optional[pd.DataFrame] = None) -> Dict[str, str]:
        """
        Genera un informe completo de un pronóstico y su evaluación.
        
        Args:
            forecast: Datos del pronóstico
            evaluation: Evaluación del pronóstico
            price_history: DataFrame con historial de precios
            future_prices: DataFrame con precios futuros si están disponibles
            
        Returns:
            Diccionario con rutas de los archivos generados
        """
        # Extraer precios reales
        actual_prices = {}
        for horizon, data in evaluation["errors"].items():
            if horizon == "short_term":
                actual_prices["actual_24h"] = data["actual"]
            elif horizon == "medium_term":
                actual_prices["actual_3d"] = data["actual"]
            elif horizon == "long_term":
                actual_prices["actual_7d"] = data["actual"]
        
        # Generar gráfico de comparación
        comparison_path = self.plot_forecast_vs_actual(
            forecast, actual_prices, price_history, future_prices
        )
        
        # Generar gráfico de distribución de errores
        distribution_path = os.path.join(self.output_dir, f'error_distribution_{forecast["id"]}.png')
        self.plot_accuracy_distribution([evaluation], distribution_path)
        
        return {
            "comparison": comparison_path,
            "distribution": distribution_path
        }
