"""
Test script to verify that the financial assistant functionality is working correctly.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path to fix imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.load_api_key import load_api_key
from src.financial_assistant import get_asset_forecast, get_financial_assistant

def test_financial_assistant():
    """
    Test that the financial assistant functionality is working correctly.
    """
    # Load API key from sensitive-data.txt
    print("Cargando API key desde sensitive-data.txt...")
    load_api_key()
    
    # Check if the API key is set in the environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ API key no encontrada en variables de entorno.")
        return False
    
    # Print the first few characters of the API key (for security)
    print(f"✅ API key cargada: {api_key[:10]}...")
    
    # Try to use the API key to generate a forecast
    print("Probando funcionalidad de asistente financiero...")
    try:
        # Generate a forecast for BTC
        symbol = "BTC"
        
        print(f"Generando pronóstico para {symbol}...")
        forecast = get_asset_forecast(symbol)
        
        # Print the forecast
        print("\n" + "="*50)
        print("PRONÓSTICO GENERADO:")
        print("="*50)
        print(forecast)
        print("="*50 + "\n")
        
        # Check if the forecast contains the expected sections
        if "Predicción para" in forecast and "Tendencia esperada" in forecast:
            print("✅ Pronóstico generado correctamente con el formato esperado.")
            return True
        else:
            print("❌ El pronóstico no tiene el formato esperado.")
            return False
            
    except Exception as e:
        print(f"❌ Error al generar pronóstico: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_previous_analysis_comparison():
    """
    Test the comparison with previous analysis functionality.
    """
    # Load API key
    load_api_key()
    
    # Get the financial assistant instance
    assistant = get_financial_assistant()
    
    # Create a mock previous analysis
    mock_analysis = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "asset": "BTC",
        "current_price": 50000.0,
        "timestamp": (datetime.now().replace(hour=0, minute=0, second=0)).isoformat(),
        "raw_analysis": "Mock analysis",
        "prediction": {
            "trend": "ALCISTA",
            "min_price": 49000.0,
            "max_price": 52000.0,
            "likely_price": 51000.0,
            "support": 48500.0,
            "resistance": 52500.0,
            "comments": "Análisis de prueba"
        },
        "closed": False
    }
    
    # Add the mock analysis to the assistant
    assistant.analyses.append(mock_analysis)
    assistant._save_analyses()
    
    print("Análisis de prueba añadido. Ejecute el test principal después de 24 horas para probar la comparación.")
    return True

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--add-mock":
        test_previous_analysis_comparison()
    else:
        test_financial_assistant()
