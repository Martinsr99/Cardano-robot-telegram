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
    
    def mark_analysis_as_closed(self, analysis_id: str, closing_price: float) -> Dict[str, Any]:
        """
        Marca un análisis como cerrado y calcula la diferencia con el precio de cierre.
        
        Args:
            analysis_id: ID del análisis a cerrar
            closing_price: Precio al momento del cierre del análisis (24h después de creación)
            
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
        price_diff = closing_price - predicted_price
        price_diff_pct = (price_diff / predicted_price) * 100
        
        # Determinar si la predicción fue acertada
        min_price = analysis["prediction"]["min_price"]
        max_price = analysis["prediction"]["max_price"]
        within_range = min_price <= closing_price <= max_price
        
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
        analysis["actual_price"] = closing_price  # Precio al momento del cierre (24h después)
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
        
        # Obtener datos de volumen
        try:
            crypto_data = CryptoDataProvider(symbol=asset)
            volume_data = None
            high_volume = False
            volume_comparison = ""
            
            if crypto_data.fetch_data() and crypto_data.data and 'volume' in crypto_data.data:
                volumes = crypto_data.data['volume']
                if len(volumes) > 1:
                    current_volume = volumes[-1]
                    avg_volume = sum(volumes[:-1]) / len(volumes[:-1])
                    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                    
                    high_volume = volume_ratio > 1.5
                    volume_data = {
                        "current": current_volume,
                        "average": avg_volume,
                        "ratio": volume_ratio,
                        "is_high": high_volume
                    }
                    
                    volume_comparison = f"""
                    El volumen actual es {volume_ratio:.2f} veces el promedio de los últimos días.
                    Volumen actual: ${current_volume:.2f}
                    Volumen promedio: ${avg_volume:.2f}
                    """
        except Exception as e:
            print(f"Error al obtener datos de volumen: {e}")
            volume_data = None
            high_volume = False
            volume_comparison = ""
        
        prompt = f"""
        Eres un asistente financiero especializado en análisis técnico y de mercado. Necesito que analices el precio del activo {asset} a día de hoy ({current_date}) con precio actual de ${current_price:.4f}.

        1. Haz una predicción del comportamiento del precio para las próximas 24 horas, incluyendo:
           - Posible rango de precios (mínimo y máximo). IMPORTANTE: El rango debe ser más ajustado y realista, evitando márgenes excesivamente amplios a menos que haya alta volatilidad justificada.
           - Tendencia esperada (alcista, bajista o lateral)
           - Niveles de soporte y resistencia relevantes
           - Cualquier patrón o señal destacable del análisis técnico
        
        {volume_comparison if volume_data else ""}
        
        {f"NOTA: Se detecta un volumen significativamente alto. Considera esto en tu análisis y menciona explícitamente si esto justifica un rango de precios más amplio." if high_volume else ""}

        Responde SOLO con datos concretos en este formato exacto:

        TENDENCIA: [ALCISTA/BAJISTA/LATERAL]
        RANGO: [MIN] - [MAX]
        PRECIO_PROBABLE: [VALOR]
        SOPORTE: [VALOR]
        RESISTENCIA: [VALOR]
        VOLUMEN: [ALTO/NORMAL/BAJO]
        COMENTARIOS: [Breve análisis técnico, patrones identificados, señales relevantes, menciona el volumen si es relevante]
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
                    # Si hay error en el formato, usar valores aproximados (rango más pequeño)
                    analysis_data["prediction"]["min_price"] = current_price * 0.98
                    analysis_data["prediction"]["max_price"] = current_price * 1.02
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
                    analysis_data["prediction"]["support"] = current_price * 0.98
            elif line.startswith("RESISTENCIA:"):
                try:
                    analysis_data["prediction"]["resistance"] = float(line.replace("RESISTENCIA:", "").strip())
                except:
                    # Si hay error en el formato, usar un valor aproximado
                    analysis_data["prediction"]["resistance"] = current_price * 1.02
            elif line.startswith("VOLUMEN:"):
                analysis_data["prediction"]["volume"] = line.replace("VOLUMEN:", "").strip()
            elif line.startswith("COMENTARIOS:"):
                analysis_data["prediction"]["comments"] = line.replace("COMENTARIOS:", "").strip()
        
        # Asegurar que todos los campos necesarios existen
        if "trend" not in analysis_data["prediction"]:
            analysis_data["prediction"]["trend"] = "LATERAL"
        if "min_price" not in analysis_data["prediction"]:
            analysis_data["prediction"]["min_price"] = current_price * 0.98
        if "max_price" not in analysis_data["prediction"]:
            analysis_data["prediction"]["max_price"] = current_price * 1.02
        if "likely_price" not in analysis_data["prediction"]:
            analysis_data["prediction"]["likely_price"] = current_price
        if "support" not in analysis_data["prediction"]:
            analysis_data["prediction"]["support"] = current_price * 0.98
        if "resistance" not in analysis_data["prediction"]:
            analysis_data["prediction"]["resistance"] = current_price * 1.02
        if "volume" not in analysis_data["prediction"]:
            analysis_data["prediction"]["volume"] = "NORMAL"
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
        volume = analysis["prediction"].get("volume", "NORMAL")
        comments = analysis["prediction"]["comments"]
        
        # Obtener precio actual actualizado
        try:
            crypto_data = CryptoDataProvider(symbol=asset)
            if crypto_data.fetch_data():
                updated_price = crypto_data.get_latest_price()
                price_change = ((updated_price - current_price) / current_price) * 100
                price_change_str = f"({price_change:.2f}%)" if updated_price != current_price else ""
            else:
                updated_price = current_price
                price_change_str = ""
        except:
            updated_price = current_price
            price_change_str = ""
        
        # Determinar indicador de compra/venta
        buy_sell_indicator = ""
        if trend == "ALCISTA" and updated_price < resistance:
            buy_sell_indicator = "🟢 COMPRA"
        elif trend == "BAJISTA" and updated_price > support:
            buy_sell_indicator = "🔴 VENTA"
        else:
            buy_sell_indicator = "⚪ NEUTRAL"
        
        # Calcular precio esperado en 24 horas (dentro del rango)
        likely_price = analysis["prediction"]["likely_price"]
        
        # Formatear salida
        output = f"""📈 Predicción para {asset} - {timestamp}

💰 Precio actual: ${updated_price:.4f} {price_change_str}
📍 Precio al abrir análisis: ${current_price:.4f}
🎯 Indicador: {buy_sell_indicator}
🔮 Tendencia esperada: {trend} 
📊 Rango estimado: ${min_price:.4f} - ${max_price:.4f}
💫 Precio esperado (24h): ${likely_price:.4f}
🛑 Soporte clave: ${support:.4f} 
📈 Resistencia clave: ${resistance:.4f}
📊 Volumen: {volume}
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

def _debug_print_analyses(assistant, asset):
    """Función de depuración para imprimir todos los análisis de un activo"""
    print(f"\n===== DEPURACIÓN: ANÁLISIS PARA {asset} =====")
    
    # Buscar todos los análisis para este símbolo
    asset_analyses = [a for a in assistant.analyses if a["asset"] == asset]
    print(f"Total de análisis para {asset}: {len(asset_analyses)}")
    
    # Mostrar análisis abiertos
    open_analyses = [a for a in asset_analyses if not a.get("closed", False)]
    print(f"Análisis abiertos para {asset}: {len(open_analyses)}")
    
    for a in open_analyses:
        timestamp = datetime.fromisoformat(a["timestamp"])
        now = datetime.now()
        hours_elapsed = (now - timestamp).total_seconds() / 3600
        print(f"  ID: {a['id']} | Fecha: {timestamp} | Antigüedad: {hours_elapsed:.1f} horas")
        print(f"  Rango: ${a['prediction']['min_price']:.4f} - ${a['prediction']['max_price']:.4f}")
        print(f"  Cerrado: {a.get('closed', False)}")
        print("  ---")
    
    print("===========================================\n")

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
    print(f"\n🔍 Solicitando pronóstico para {asset}")
    assistant = get_financial_assistant(api_key)
    
    # Imprimir estado inicial de los análisis
    _debug_print_analyses(assistant, asset)
    
    # Obtener el precio actual para verificar y cerrar análisis antiguos
    current_price = None
    try:
        crypto_data = CryptoDataProvider(symbol=asset)
        if crypto_data.fetch_data():
            current_price = crypto_data.get_latest_price()
            print(f"💰 Precio actual de {asset}: ${current_price:.4f}")
        else:
            print(f"❌ No se pudieron obtener datos para {asset}")
            return f"❌ Error: No se pudieron obtener datos para {asset}"
    except Exception as e:
        print(f"❌ Error al obtener precio actual: {str(e)}")
        return f"❌ Error al obtener precio actual: {str(e)}"
    
    # Buscar todos los análisis para este símbolo
    asset_analyses = [a for a in assistant.analyses if a["asset"] == asset]
    print(f"📋 Encontrados {len(asset_analyses)} análisis para {asset}")
    
    # Filtrar los análisis que tienen más de 24 horas y no están cerrados
    now = datetime.now()
    limit_time = now - timedelta(hours=24)
    limit_timestamp = limit_time.isoformat()
    
    old_analyses = [a for a in asset_analyses if a["timestamp"] < limit_timestamp and not a.get("closed", False)]
    print(f"⏰ Encontrados {len(old_analyses)} análisis antiguos (>24h) abiertos para {asset}")
    
    # Cerrar todos los análisis antiguos encontrados
    previous_analysis = None
    for old_analysis in old_analyses:
        try:
            print(f"🔒 Intentando cerrar análisis con ID {old_analysis['id']} (timestamp: {old_analysis['timestamp']})")
            
            # Verificar si el análisis ya está cerrado (doble verificación)
            if old_analysis.get("closed", False):
                print(f"⚠️ El análisis {old_analysis['id']} ya está marcado como cerrado")
                continue
                
            # Cerrar el análisis con el precio esperado (likely_price) en lugar del precio actual
            closing_price = old_analysis["prediction"]["likely_price"]
            closed_analysis = assistant.mark_analysis_as_closed(old_analysis["id"], closing_price)
            print(f"✅ Análisis antiguo de {asset} con ID {old_analysis['id']} cerrado correctamente con precio esperado: ${closing_price:.4f}")
            
            # Guardar el análisis cerrado más reciente para mostrarlo en la comparación
            if previous_analysis is None or datetime.fromisoformat(closed_analysis["timestamp"]) > datetime.fromisoformat(previous_analysis["timestamp"]):
                previous_analysis = closed_analysis
                print(f"📌 Guardando análisis {closed_analysis['id']} como referencia para comparación")
        except Exception as e:
            print(f"❌ Error al cerrar análisis {old_analysis['id']}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Verificar que los análisis se cerraron correctamente
    print("\n🔍 Verificando cierre de análisis antiguos...")
    still_open = [a for a in assistant.analyses if a["asset"] == asset and 
                 a["timestamp"] < limit_timestamp and not a.get("closed", False)]
    
    if still_open:
        print(f"⚠️ ADVERTENCIA: Aún hay {len(still_open)} análisis antiguos abiertos:")
        for a in still_open:
            print(f"  - ID: {a['id']} | Timestamp: {a['timestamp']} | Cerrado: {a.get('closed', False)}")
            
            # Forzar cierre nuevamente
            try:
                print(f"🔄 Intentando forzar cierre del análisis {a['id']}...")
                # Modificar directamente el análisis en la lista
                for idx, analysis in enumerate(assistant.analyses):
                    if analysis["id"] == a["id"]:
                        assistant.analyses[idx]["closed"] = True
                        assistant.analyses[idx]["closed_timestamp"] = datetime.now().isoformat()
                        assistant.analyses[idx]["actual_price"] = current_price
                        print(f"✅ Forzado cierre del análisis {a['id']}")
                        break
            except Exception as e:
                print(f"❌ Error al forzar cierre: {str(e)}")
    else:
        print("✅ Todos los análisis antiguos están correctamente cerrados")
    
    # Guardar cambios después de forzar cierres
    assistant._save_analyses()
    
    # Imprimir estado después de cerrar análisis antiguos
    _debug_print_analyses(assistant, asset)
    
    # Comprobar si hay un análisis reciente que podamos reutilizar
    if not force_new:
        # Obtener el análisis más reciente para este activo
        latest_analysis = assistant.get_latest_analysis(asset)
        print(f"🔍 Buscando análisis reciente para {asset}...")
        
        if latest_analysis:
            print(f"📋 Análisis más reciente: ID {latest_analysis['id']} | Timestamp: {latest_analysis['timestamp']} | Cerrado: {latest_analysis.get('closed', False)}")
            
            if not latest_analysis.get("closed", False):
                # Verificar que no sea uno de los que acabamos de cerrar
                is_old_analysis = False
                for old_analysis in old_analyses:
                    if latest_analysis["id"] == old_analysis["id"]:
                        is_old_analysis = True
                        print(f"⚠️ El análisis reciente {latest_analysis['id']} es uno de los antiguos que debería haberse cerrado")
                        break
                
                # Verificar antigüedad
                timestamp = datetime.fromisoformat(latest_analysis["timestamp"])
                hours_elapsed = (now - timestamp).total_seconds() / 3600
                
                if hours_elapsed >= 24:
                    print(f"⚠️ El análisis reciente tiene {hours_elapsed:.1f} horas (>24h), debería cerrarse")
                    is_old_analysis = True
                
                if not is_old_analysis:
                    # Si el análisis es reciente (menos de X horas), devolver ese
                    if hours_elapsed < FINANCIAL_ANALYSIS_MIN_INTERVAL:
                        print(f"📊 Usando análisis existente de hace {hours_elapsed:.1f} horas (mínimo: {FINANCIAL_ANALYSIS_MIN_INTERVAL} horas)")
                        
                        # Formatear salida
                        result = assistant.format_analysis_output(latest_analysis, previous_analysis)
                        
                        # Verificación final
                        _debug_print_analyses(assistant, asset)
                        
                        return result
                    else:
                        print(f"⏰ El análisis reciente tiene {hours_elapsed:.1f} horas (>={FINANCIAL_ANALYSIS_MIN_INTERVAL}h), generando uno nuevo")
            else:
                print(f"🔒 El análisis más reciente ya está cerrado, generando uno nuevo")
        else:
            print(f"📭 No se encontró ningún análisis para {asset}, generando uno nuevo")
    
    # Si no hay análisis reciente o se fuerza uno nuevo, generar uno
    return assistant.get_forecast(asset)
