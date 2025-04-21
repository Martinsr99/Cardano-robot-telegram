"""
Financial Assistant - Asistente financiero especializado en análisis técnico y de mercado.

Este módulo proporciona funcionalidades para analizar activos financieros,
hacer predicciones de precios y comparar con análisis previos.
"""

import os
import json
import time
import datetime
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from openai import OpenAI
from src.crypto_data_provider import CryptoDataProvider
from forecast_system.forecast_manager import ForecastManager
from utils.load_api_key import get_api_key

# Add parent directory to path to fix imports when running from tests
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Directorio para almacenar los análisis
ANALYSIS_DIR = "forecast_system/data/financial_analysis"

# Asegurar que el directorio existe
os.makedirs(ANALYSIS_DIR, exist_ok=True)

class FinancialAssistant:
    """
    Asistente financiero especializado en análisis técnico y de mercado.
    """
    def __init__(self, api_key=None):
        """
        Inicializa el asistente financiero.
        
        Args:
            api_key (str, optional): OpenAI API key. Si no se proporciona, se usará OPENAI_API_KEY del entorno.
        """
        self.api_key = api_key or get_api_key()
        self.client = OpenAI(api_key=self.api_key)
        self.forecast_manager = ForecastManager(data_dir=ANALYSIS_DIR)
        self.analysis_file = os.path.join(ANALYSIS_DIR, "asset_analysis.json")
        self.analyses = self._load_analyses()
    
    def _load_analyses(self) -> List[Dict[str, Any]]:
        """Carga los análisis guardados desde el archivo"""
        if os.path.exists(self.analysis_file):
            try:
                with open(self.analysis_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error al cargar análisis de {self.analysis_file}")
                return []
        return []
    
    def _save_analyses(self):
        """Guarda los análisis en el archivo"""
        with open(self.analysis_file, 'w') as f:
            json.dump(self.analyses, f, indent=2)
    
    def get_latest_analysis(self, asset: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el análisis más reciente para un activo.
        
        Args:
            asset: Símbolo del activo (ej. "BTC", "ETH")
            
        Returns:
            Análisis más reciente o None si no hay análisis
        """
        # Filtrar análisis para el activo especificado
        asset_analyses = [a for a in self.analyses if a["asset"] == asset]
        
        if not asset_analyses:
            return None
        
        # Ordenar por timestamp y obtener el más reciente
        sorted_analyses = sorted(asset_analyses, key=lambda x: x["timestamp"], reverse=True)
        return sorted_analyses[0]
    
    def get_analysis_older_than(self, asset: str, hours: int = 24) -> Optional[Dict[str, Any]]:
        """
        Obtiene el análisis más reciente para un activo que sea más antiguo que las horas especificadas.
        
        Args:
            asset: Símbolo del activo (ej. "BTC", "ETH")
            hours: Número de horas de antigüedad mínima
            
        Returns:
            Análisis más reciente con la antigüedad especificada o None si no hay análisis
        """
        # Filtrar análisis para el activo especificado
        asset_analyses = [a for a in self.analyses if a["asset"] == asset]
        
        if not asset_analyses:
            return None
        
        # Calcular el timestamp límite
        current_time = datetime.now()
        limit_time = current_time - timedelta(hours=hours)
        limit_timestamp = limit_time.isoformat()
        
        # Filtrar análisis más antiguos que el límite y que no estén cerrados
        old_analyses = [a for a in asset_analyses if a["timestamp"] < limit_timestamp and not a.get("closed", False)]
        
        if not old_analyses:
            return None
        
        # Ordenar por timestamp y obtener el más reciente
        sorted_analyses = sorted(old_analyses, key=lambda x: x["timestamp"], reverse=True)
        return sorted_analyses[0]
    
    def mark_analysis_as_closed(self, analysis_id: str, current_price: float) -> Dict[str, Any]:
        """
        Marca un análisis como cerrado y calcula la diferencia con el precio actual.
        
        Args:
            analysis_id: ID del análisis a cerrar
            current_price: Precio actual del activo
            
        Returns:
            Análisis actualizado
        """
        # Buscar el análisis
        analysis = None
        for a in self.analyses:
            if a["id"] == analysis_id:
                analysis = a
                break
        
        if not analysis:
            raise ValueError(f"Análisis con ID {analysis_id} no encontrado")
        
        # Calcular diferencia con el precio predicho
        predicted_price = analysis["prediction"]["likely_price"]
        price_diff = current_price - predicted_price
        price_diff_pct = (price_diff / predicted_price) * 100
        
        # Determinar si la predicción fue acertada
        min_price = analysis["prediction"]["min_price"]
        max_price = analysis["prediction"]["max_price"]
        within_range = min_price <= current_price <= max_price
        
        # Determinar precisión
        if within_range:
            if abs(price_diff_pct) < 2:
                precision = "ACERTADA"
            else:
                precision = "PARCIAL"
        else:
            precision = "FALLIDA"
        
        # Actualizar análisis
        analysis["closed"] = True
        analysis["closed_timestamp"] = datetime.now().isoformat()
        analysis["actual_price"] = current_price
        analysis["price_diff"] = price_diff
        analysis["price_diff_pct"] = price_diff_pct
        analysis["within_range"] = within_range
        analysis["precision"] = precision
        
        # Guardar cambios
        self._save_analyses()
        
        return analysis
    
    def analyze_asset(self, asset: str, current_price: float) -> Dict[str, Any]:
        """
        Analiza un activo financiero y genera una predicción.
        
        Args:
            asset: Símbolo del activo (ej. "BTC", "ETH")
            current_price: Precio actual del activo
            
        Returns:
            Análisis generado
        """
        # Generar prompt para el análisis
        prompt = self._generate_analysis_prompt(asset, current_price)
        
        try:
            # Llamar a la API de OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "Eres un analista financiero experto en análisis técnico y de mercado."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Extraer el análisis
            analysis_text = response.choices[0].message.content
            
            # Procesar el análisis para extraer datos estructurados
            analysis_data = self._parse_analysis(analysis_text, asset, current_price)
            
            # Guardar el análisis
            self.analyses.append(analysis_data)
            self._save_analyses()
            
            return analysis_data
            
        except Exception as e:
            error_msg = f"Error al generar análisis: {str(e)}"
            print(error_msg)
            return {
                "error": error_msg,
                "asset": asset,
                "current_price": current_price,
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_analysis_prompt(self, asset: str, current_price: float) -> str:
        """
        Genera el prompt para el análisis de un activo.
        
        Args:
            asset: Símbolo del activo
            current_price: Precio actual del activo
            
        Returns:
            Prompt para el análisis
        """
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        prompt = f"""
        Eres un asistente financiero especializado en análisis técnico y de mercado. Necesito que analices el precio del activo {asset} a día de hoy ({current_date}) con precio actual de ${current_price:.4f}.

        1. Haz una predicción del comportamiento del precio para las próximas 24 horas, incluyendo:
           - Posible rango de precios (mínimo y máximo)
           - Tendencia esperada (alcista, bajista o lateral)
           - Niveles de soporte y resistencia relevantes
           - Cualquier patrón o señal destacable del análisis técnico

        Responde SOLO con datos concretos en este formato exacto:

        TENDENCIA: [ALCISTA/BAJISTA/LATERAL]
        RANGO: [MIN] - [MAX]
        PRECIO_PROBABLE: [VALOR]
        SOPORTE: [VALOR]
        RESISTENCIA: [VALOR]
        COMENTARIOS: [Breve análisis técnico, patrones identificados, señales relevantes]
        """
        
        return prompt
    
    def _parse_analysis(self, analysis_text: str, asset: str, current_price: float) -> Dict[str, Any]:
        """
        Procesa el texto del análisis para extraer datos estructurados.
        
        Args:
            analysis_text: Texto del análisis
            asset: Símbolo del activo
            current_price: Precio actual del activo
            
        Returns:
            Datos estructurados del análisis
        """
        # Inicializar datos
        analysis_data = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "asset": asset,
            "current_price": current_price,
            "timestamp": datetime.now().isoformat(),
            "raw_analysis": analysis_text,
            "prediction": {},
            "closed": False
        }
        
        # Extraer datos del análisis
        lines = analysis_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("TENDENCIA:"):
                analysis_data["prediction"]["trend"] = line.replace("TENDENCIA:", "").strip()
            elif line.startswith("RANGO:"):
                range_str = line.replace("RANGO:", "").strip()
                try:
                    min_str, max_str = range_str.split('-')
                    analysis_data["prediction"]["min_price"] = float(min_str.strip())
                    analysis_data["prediction"]["max_price"] = float(max_str.strip())
                except:
                    # Si hay error en el formato, usar valores aproximados
                    analysis_data["prediction"]["min_price"] = current_price * 0.95
                    analysis_data["prediction"]["max_price"] = current_price * 1.05
            elif line.startswith("PRECIO_PROBABLE:"):
                try:
                    analysis_data["prediction"]["likely_price"] = float(line.replace("PRECIO_PROBABLE:", "").strip())
                except:
                    # Si hay error en el formato, usar el precio actual
                    analysis_data["prediction"]["likely_price"] = current_price
            elif line.startswith("SOPORTE:"):
                try:
                    analysis_data["prediction"]["support"] = float(line.replace("SOPORTE:", "").strip())
                except:
                    # Si hay error en el formato, usar un valor aproximado
                    analysis_data["prediction"]["support"] = current_price * 0.97
            elif line.startswith("RESISTENCIA:"):
                try:
                    analysis_data["prediction"]["resistance"] = float(line.replace("RESISTENCIA:", "").strip())
                except:
                    # Si hay error en el formato, usar un valor aproximado
                    analysis_data["prediction"]["resistance"] = current_price * 1.03
            elif line.startswith("COMENTARIOS:"):
                analysis_data["prediction"]["comments"] = line.replace("COMENTARIOS:", "").strip()
        
        # Asegurar que todos los campos necesarios existen
        if "trend" not in analysis_data["prediction"]:
            analysis_data["prediction"]["trend"] = "LATERAL"
        if "min_price" not in analysis_data["prediction"]:
            analysis_data["prediction"]["min_price"] = current_price * 0.95
        if "max_price" not in analysis_data["prediction"]:
            analysis_data["prediction"]["max_price"] = current_price * 1.05
        if "likely_price" not in analysis_data["prediction"]:
            analysis_data["prediction"]["likely_price"] = current_price
        if "support" not in analysis_data["prediction"]:
            analysis_data["prediction"]["support"] = current_price * 0.97
        if "resistance" not in analysis_data["prediction"]:
            analysis_data["prediction"]["resistance"] = current_price * 1.03
        if "comments" not in analysis_data["prediction"]:
            analysis_data["prediction"]["comments"] = "Análisis no disponible"
        
        return analysis_data
    
    def format_analysis_output(self, analysis: Dict[str, Any], previous_analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Formatea el análisis para su presentación.
        
        Args:
            analysis: Datos del análisis
            previous_analysis: Análisis previo para comparación (opcional)
            
        Returns:
            Texto formateado del análisis
        """
        asset = analysis["asset"]
        timestamp = datetime.fromisoformat(analysis["timestamp"]).strftime("%Y-%m-%d %H:%M")
        current_price = analysis["current_price"]
        
        # Datos de la predicción
        trend = analysis["prediction"]["trend"]
        min_price = analysis["prediction"]["min_price"]
        max_price = analysis["prediction"]["max_price"]
        support = analysis["prediction"]["support"]
        resistance = analysis["prediction"]["resistance"]
        comments = analysis["prediction"]["comments"]
        
        # Formatear salida
        output = f"""📈 Predicción para {asset} - {timestamp}

🔮 Tendencia esperada: {trend} 
📊 Rango estimado: ${min_price:.4f} - ${max_price:.4f} 
🛑 Soporte clave: ${support:.4f} 
📈 Resistencia clave: ${resistance:.4f}
"""
        
        # Añadir comparación con análisis anterior si existe
        if previous_analysis and previous_analysis.get("closed"):
            prev_timestamp = datetime.fromisoformat(previous_analysis["timestamp"]).strftime("%Y-%m-%d %H:%M")
            prev_min = previous_analysis["prediction"]["min_price"]
            prev_max = previous_analysis["prediction"]["max_price"]
            actual_price = previous_analysis["actual_price"]
            price_diff = previous_analysis["price_diff"]
            precision = previous_analysis["precision"]
            
            output += f"""
📂 Comparación con análisis anterior:

    Fecha anterior: {prev_timestamp}
    
    Predicción: ${prev_min:.4f} - ${prev_max:.4f}
    
    Precio actual: ${actual_price:.4f}
    
    Diferencia: ${price_diff:.4f} ({previous_analysis["price_diff_pct"]:.2f}%)
    
    Precisión: {precision}
"""
        
        # Añadir comentarios adicionales
        output += f"""
💡 Comentarios adicionales: {comments}
"""
        
        return output
    
    def get_forecast(self, asset: str) -> str:
        """
        Obtiene un pronóstico para un activo, comprobando si hay análisis previos.
        
        Args:
            asset: Símbolo del activo (ej. "BTC", "ETH")
            
        Returns:
            Texto formateado del pronóstico
        """
        try:
            # Obtener datos del mercado usando CoinGecko
            crypto_data = CryptoDataProvider(symbol=asset)
            if not crypto_data.fetch_data():
                return f"❌ Error: No se pudieron obtener datos para {asset}"
            
            current_price = crypto_data.get_latest_price()
            
            # Comprobar si hay un análisis anterior con más de 24 horas
            previous_analysis = self.get_analysis_older_than(asset, hours=24)
            
            # Si hay un análisis anterior, marcarlo como cerrado
            if previous_analysis:
                previous_analysis = self.mark_analysis_as_closed(previous_analysis["id"], current_price)
            
            # Generar nuevo análisis
            new_analysis = self.analyze_asset(asset, current_price)
            
            # Formatear salida
            return self.format_analysis_output(new_analysis, previous_analysis)
            
        except Exception as e:
            error_msg = f"❌ Error al generar pronóstico: {str(e)}"
            print(error_msg)
            return error_msg

# Instancia singleton
_instance = None

def get_financial_assistant(api_key=None):
    """
    Obtiene la instancia singleton de FinancialAssistant.
    
    Args:
        api_key (str, optional): OpenAI API key. Si no se proporciona, se usará OPENAI_API_KEY del entorno.
        
    Returns:
        FinancialAssistant: Instancia del asistente financiero
    """
    global _instance
    if _instance is None:
        _instance = FinancialAssistant(api_key)
    return _instance

from config.config import FINANCIAL_ANALYSIS_MIN_INTERVAL

def get_asset_forecast(asset: str, api_key=None, force_new=False) -> str:
    """
    Obtiene un pronóstico para un activo.
    
    Args:
        asset: Símbolo del activo (ej. "BTC", "ETH")
        api_key (str, optional): OpenAI API key. Si no se proporciona, se usará OPENAI_API_KEY del entorno.
        force_new (bool, optional): Si es True, fuerza la generación de un nuevo análisis
                                   independientemente del tiempo transcurrido.
        
    Returns:
        str: Texto formateado del pronóstico
    """
    assistant = get_financial_assistant(api_key)
    
    # Comprobar si hay un análisis reciente
    if not force_new:
        latest_analysis = assistant.get_latest_analysis(asset)
        if latest_analysis:
            # Calcular tiempo transcurrido desde el último análisis
            timestamp = datetime.fromisoformat(latest_analysis["timestamp"])
            now = datetime.now()
            hours_elapsed = (now - timestamp).total_seconds() / 3600
            
            # Si el análisis es reciente (menos de X horas), devolver ese
            if hours_elapsed < FINANCIAL_ANALYSIS_MIN_INTERVAL:
                print(f"📊 Usando análisis existente de hace {hours_elapsed:.1f} horas (mínimo: {FINANCIAL_ANALYSIS_MIN_INTERVAL} horas)")
                previous_analysis = None
                
                # Comprobar si hay un análisis anterior con más de 24 horas para comparación
                old_analysis = assistant.get_analysis_older_than(asset, hours=24)
                if old_analysis and old_analysis["id"] != latest_analysis["id"]:
                    # Marcar como cerrado si no lo está ya
                    if not old_analysis.get("closed", False):
                        current_price = latest_analysis["current_price"]
                        previous_analysis = assistant.mark_analysis_as_closed(old_analysis["id"], current_price)
                    else:
                        previous_analysis = old_analysis
                
                # Formatear salida
                return assistant.format_analysis_output(latest_analysis, previous_analysis)
    
    # Si no hay análisis reciente o se fuerza uno nuevo, generar uno
    return assistant.get_forecast(asset)
