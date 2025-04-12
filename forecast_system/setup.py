"""
Script de configuración para el sistema de pronóstico
"""

import os
import sys
import subprocess
import time

def print_step(step, message):
    """Imprime un paso de la instalación con formato"""
    print(f"\n[{step}] {message}")
    time.sleep(0.5)

def create_directories():
    """Crea los directorios necesarios para el sistema"""
    print_step(1, "Creando directorios del sistema...")
    
    directories = [
        "forecast_system/data",
        "forecast_system/models/saved",
        "forecast_system/visualization/output"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"  ✅ Creado: {directory}")
        else:
            print(f"  ℹ️ Ya existe: {directory}")

def install_dependencies():
    """Instala las dependencias necesarias"""
    print_step(2, "Instalando dependencias...")
    
    # Verificar si requirements.txt existe
    if not os.path.exists("requirements.txt"):
        print("  ❌ Error: No se encontró el archivo requirements.txt")
        return False
    
    # Instalar dependencias
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("  ✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error al instalar dependencias: {e}")
        return False

def initialize_data_files():
    """Inicializa los archivos de datos necesarios"""
    print_step(3, "Inicializando archivos de datos...")
    
    # Crear archivos JSON vacíos si no existen
    data_files = [
        ("forecast_system/data/forecasts_history.json", []),
        ("forecast_system/data/forecast_evaluations.json", [])
    ]
    
    for file_path, initial_content in data_files:
        if not os.path.exists(file_path):
            import json
            with open(file_path, 'w') as f:
                json.dump(initial_content, f)
            print(f"  ✅ Creado: {file_path}")
        else:
            print(f"  ℹ️ Ya existe: {file_path}")

def verify_installation():
    """Verifica que la instalación se haya completado correctamente"""
    print_step(4, "Verificando instalación...")
    
    # Verificar que los módulos necesarios se puedan importar
    try:
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        import joblib
        from sklearn.ensemble import GradientBoostingRegressor
        print("  ✅ Todas las dependencias están disponibles")
        
        # Verificar que los directorios existan
        all_dirs_exist = True
        for directory in ["forecast_system/data", "forecast_system/models/saved", "forecast_system/visualization/output"]:
            if not os.path.exists(directory):
                print(f"  ❌ Directorio no encontrado: {directory}")
                all_dirs_exist = False
        
        if all_dirs_exist:
            print("  ✅ Todos los directorios están creados")
        
        # Verificar que los archivos de datos existan
        all_files_exist = True
        for file_path in ["forecast_system/data/forecasts_history.json", "forecast_system/data/forecast_evaluations.json"]:
            if not os.path.exists(file_path):
                print(f"  ❌ Archivo no encontrado: {file_path}")
                all_files_exist = False
        
        if all_files_exist:
            print("  ✅ Todos los archivos de datos están creados")
        
        return all_dirs_exist and all_files_exist
    except ImportError as e:
        print(f"  ❌ Error al importar dependencias: {e}")
        return False

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("  CONFIGURACIÓN DEL SISTEMA DE PRONÓSTICO CON RETROALIMENTACIÓN")
    print("="*60)
    
    # Crear directorios
    create_directories()
    
    # Instalar dependencias
    if not install_dependencies():
        print("\n❌ La instalación de dependencias falló. Por favor, revise los errores e intente nuevamente.")
        return
    
    # Inicializar archivos de datos
    initialize_data_files()
    
    # Verificar instalación
    if verify_installation():
        print("\n" + "="*60)
        print("  ✅ INSTALACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        print("\nPuede ejecutar el bot con el sistema de pronóstico usando:")
        print("  python main.py --monitor  # Modo monitor")
        print("  python main.py --ui       # Modo interfaz gráfica")
    else:
        print("\n" + "="*60)
        print("  ⚠️ INSTALACIÓN COMPLETADA CON ADVERTENCIAS")
        print("="*60)
        print("\nAlgunos componentes pueden no funcionar correctamente.")
        print("Revise los mensajes anteriores para más detalles.")

if __name__ == "__main__":
    main()
