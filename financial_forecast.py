#!/usr/bin/env python
"""
Financial Forecast CLI - Command line tool for generating financial forecasts.

Usage:
    python financial_forecast.py [SYMBOL]                # Generate forecast for symbol
    python financial_forecast.py --list                  # List all analyses
    python financial_forecast.py --list-open             # List open analyses
    python financial_forecast.py --list-closed           # List closed analyses
    python financial_forecast.py --details ANALYSIS_ID   # Show details for a specific analysis
    python financial_forecast.py --delete ANALYSIS_ID    # Delete a specific analysis
    python financial_forecast.py --clean                 # Clean up analyses with incorrect data

Example:
    python financial_forecast.py BTC
    python financial_forecast.py ETH
    python financial_forecast.py --list
    python financial_forecast.py --clean
"""

import sys
import os
import json
from datetime import datetime
from utils.load_api_key import load_api_key
from src.financial_assistant import get_asset_forecast, get_financial_assistant

def main():
    """Main entry point for the financial forecast CLI."""
    # Load API key
    load_api_key()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        # Check for command options
        if sys.argv[1] == "--list" or sys.argv[1] == "-l":
            list_analyses()
            return 0
        elif sys.argv[1] == "--list-open" or sys.argv[1] == "-o":
            list_analyses(show_closed=False)
            return 0
        elif sys.argv[1] == "--list-closed" or sys.argv[1] == "-c":
            list_analyses(show_open=False)
            return 0
        elif sys.argv[1] == "--details" or sys.argv[1] == "-d":
            if len(sys.argv) > 2:
                show_analysis_details(sys.argv[2])
                return 0
            else:
                print("❌ Error: Debe proporcionar un ID de análisis")
                return 1
        elif sys.argv[1] == "--delete" or sys.argv[1] == "-del":
            if len(sys.argv) > 2:
                delete_analysis(sys.argv[2])
                return 0
            else:
                print("❌ Error: Debe proporcionar un ID de análisis")
                return 1
        elif sys.argv[1] == "--clean" or sys.argv[1] == "-c":
            clean_analyses()
            return 0
        else:
            # Assume it's a symbol
            symbol = sys.argv[1].upper()
    else:
        symbol = "BTC"  # Default to BTC
    
    # Generate forecast
    print(f"Generando pronóstico financiero para {symbol}...")
    
    try:
        # Get forecast
        forecast = get_asset_forecast(symbol)
        
        # Print forecast
        print("\n" + "="*50)
        print(f"PRONÓSTICO FINANCIERO PARA {symbol}")
        print("="*50)
        print(forecast)
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"❌ Error al generar pronóstico: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

def list_analyses(show_open=True, show_closed=True):
    """
    List all analyses, optionally filtering by status.
    
    Args:
        show_open: Whether to show open analyses
        show_closed: Whether to show closed analyses
    """
    # Get financial assistant
    assistant = get_financial_assistant()
    
    # Get all analyses
    analyses = assistant.analyses
    
    if not analyses:
        print("No hay análisis disponibles.")
        return
    
    # Filter analyses
    filtered_analyses = []
    for analysis in analyses:
        is_closed = analysis.get("closed", False)
        if (is_closed and show_closed) or (not is_closed and show_open):
            filtered_analyses.append(analysis)
    
    if not filtered_analyses:
        print("No hay análisis que coincidan con los criterios de filtrado.")
        return
    
    # Sort analyses by timestamp (newest first)
    filtered_analyses.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Print analyses
    print("\n" + "="*50)
    if show_open and show_closed:
        print("TODOS LOS ANÁLISIS")
    elif show_open:
        print("ANÁLISIS ABIERTOS")
    else:
        print("ANÁLISIS CERRADOS")
    print("="*50)
    
    for analysis in filtered_analyses:
        # Get basic info
        asset = analysis["asset"]
        timestamp = datetime.fromisoformat(analysis["timestamp"]).strftime("%Y-%m-%d %H:%M")
        analysis_id = analysis["id"]
        is_closed = analysis.get("closed", False)
        
        # Get prediction info
        trend = analysis["prediction"]["trend"]
        min_price = analysis["prediction"]["min_price"]
        max_price = analysis["prediction"]["max_price"]
        
        # Print analysis summary
        status = "🔴 CERRADO" if is_closed else "🟢 ABIERTO"
        print(f"ID: {analysis_id} | {asset} | {timestamp} | {status}")
        print(f"  Tendencia: {trend} | Rango: ${min_price:.4f} - ${max_price:.4f}")
        
        # Print additional info for closed analyses
        if is_closed:
            actual_price = analysis["actual_price"]
            precision = analysis["precision"]
            print(f"  Precio actual: ${actual_price:.4f} | Precisión: {precision}")
        
        print("-"*50)
    
    print(f"Total: {len(filtered_analyses)} análisis\n")
    print("Para ver detalles de un análisis específico, use:")
    print("  python financial_forecast.py --details ANALYSIS_ID")

def delete_analysis(analysis_id):
    """
    Delete a specific analysis.
    
    Args:
        analysis_id: ID of the analysis to delete
    """
    # Get financial assistant
    assistant = get_financial_assistant()
    
    # Find analysis with the given ID
    analysis = None
    index_to_delete = -1
    for i, a in enumerate(assistant.analyses):
        if a["id"] == analysis_id:
            analysis = a
            index_to_delete = i
            break
    
    if not analysis:
        print(f"❌ Error: No se encontró un análisis con ID {analysis_id}")
        return
    
    # Get basic info for confirmation
    asset = analysis["asset"]
    timestamp = datetime.fromisoformat(analysis["timestamp"]).strftime("%Y-%m-%d %H:%M")
    
    # Delete the analysis
    del assistant.analyses[index_to_delete]
    
    # Save changes
    assistant._save_analyses()
    
    print(f"✅ Análisis eliminado: {asset} | {timestamp} | ID: {analysis_id}")

def clean_analyses():
    """
    Clean up analyses with incorrect price data.
    """
    # Get financial assistant
    assistant = get_financial_assistant()
    
    # IDs to delete (based on user feedback)
    ids_to_delete = [
        "20250421165821",  # BTC with incorrect price
        "20250421165644",  # BTC with incorrect price
        "20250421165406",  # ETH with incorrect price
        "20250421164641",  # BTC with incorrect price
        "20250421164719",  # BTC with incorrect price
    ]
    
    # Delete analyses
    deleted_count = 0
    for analysis_id in ids_to_delete:
        # Find analysis with the given ID
        index_to_delete = -1
        for i, a in enumerate(assistant.analyses):
            if a["id"] == analysis_id:
                index_to_delete = i
                break
        
        if index_to_delete >= 0:
            # Delete the analysis
            del assistant.analyses[index_to_delete]
            deleted_count += 1
    
    # Save changes
    assistant._save_analyses()
    
    print(f"✅ Se eliminaron {deleted_count} análisis con datos incorrectos.")

def show_analysis_details(analysis_id):
    """
    Show details for a specific analysis.
    
    Args:
        analysis_id: ID of the analysis to show
    """
    # Get financial assistant
    assistant = get_financial_assistant()
    
    # Find analysis with the given ID
    analysis = None
    for a in assistant.analyses:
        if a["id"] == analysis_id:
            analysis = a
            break
    
    if not analysis:
        print(f"❌ Error: No se encontró un análisis con ID {analysis_id}")
        return
    
    # Get basic info
    asset = analysis["asset"]
    timestamp = datetime.fromisoformat(analysis["timestamp"]).strftime("%Y-%m-%d %H:%M")
    is_closed = analysis.get("closed", False)
    
    # Get prediction info
    trend = analysis["prediction"]["trend"]
    min_price = analysis["prediction"]["min_price"]
    max_price = analysis["prediction"]["max_price"]
    likely_price = analysis["prediction"]["likely_price"]
    support = analysis["prediction"]["support"]
    resistance = analysis["prediction"]["resistance"]
    comments = analysis["prediction"]["comments"]
    
    # Print analysis details
    print("\n" + "="*50)
    print(f"DETALLES DEL ANÁLISIS {analysis_id}")
    print("="*50)
    
    print(f"Activo: {asset}")
    print(f"Fecha: {timestamp}")
    print(f"Estado: {'CERRADO' if is_closed else 'ABIERTO'}")
    print(f"Precio en el momento del análisis: ${analysis['current_price']:.4f}")
    print("\nPredicción:")
    print(f"  Tendencia: {trend}")
    print(f"  Rango: ${min_price:.4f} - ${max_price:.4f}")
    print(f"  Precio probable: ${likely_price:.4f}")
    print(f"  Soporte: ${support:.4f}")
    print(f"  Resistencia: ${resistance:.4f}")
    print(f"  Comentarios: {comments}")
    
    # Print additional info for closed analyses
    if is_closed:
        closed_timestamp = datetime.fromisoformat(analysis["closed_timestamp"]).strftime("%Y-%m-%d %H:%M")
        actual_price = analysis["actual_price"]
        price_diff = analysis["price_diff"]
        price_diff_pct = analysis["price_diff_pct"]
        within_range = analysis["within_range"]
        precision = analysis["precision"]
        
        print("\nResultados:")
        print(f"  Fecha de cierre: {closed_timestamp}")
        print(f"  Precio actual: ${actual_price:.4f}")
        print(f"  Diferencia: ${price_diff:.4f} ({price_diff_pct:.2f}%)")
        print(f"  Dentro del rango: {'Sí' if within_range else 'No'}")
        print(f"  Precisión: {precision}")
    
    print("="*50 + "\n")

if __name__ == "__main__":
    sys.exit(main())
