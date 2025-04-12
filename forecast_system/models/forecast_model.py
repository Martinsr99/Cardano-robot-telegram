"""
Forecast Model - Modelo de IA para mejorar pronósticos basado en retroalimentación
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import joblib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import datetime
import json

class ForecastModel:
    """
    Modelo de IA para mejorar pronósticos basado en retroalimentación.
    """
    def __init__(self, model_dir: str = "forecast_system/models/saved"):
        """
        Inicializa el modelo de pronóstico.
        
        Args:
            model_dir: Directorio donde se guardarán los modelos entrenados
        """
        self.model_dir = model_dir
        
        # Crear directorio si no existe
        os.makedirs(model_dir, exist_ok=True)
        
        # Inicializar modelos
        self.short_term_model = None
        self.medium_term_model = None
        self.long_term_model = None
        
        # Cargar modelos si existen
        self._load_models()
    
    def _load_models(self):
        """Carga los modelos guardados si existen"""
        short_term_path = os.path.join(self.model_dir, "short_term_model.joblib")
        medium_term_path = os.path.join(self.model_dir, "medium_term_model.joblib")
        long_term_path = os.path.join(self.model_dir, "long_term_model.joblib")
        
        if os.path.exists(short_term_path):
            self.short_term_model = joblib.load(short_term_path)
        
        if os.path.exists(medium_term_path):
            self.medium_term_model = joblib.load(medium_term_path)
        
        if os.path.exists(long_term_path):
            self.long_term_model = joblib.load(long_term_path)
    
    def _save_models(self):
        """Guarda los modelos entrenados"""
        if self.short_term_model:
            joblib.dump(self.short_term_model, os.path.join(self.model_dir, "short_term_model.joblib"))
        
        if self.medium_term_model:
            joblib.dump(self.medium_term_model, os.path.join(self.model_dir, "medium_term_model.joblib"))
        
        if self.long_term_model:
            joblib.dump(self.long_term_model, os.path.join(self.model_dir, "long_term_model.joblib"))
    
    def prepare_training_data(self, forecasts: List[Dict[str, Any]], evaluations: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
        """
        Prepara los datos de entrenamiento a partir de pronósticos y evaluaciones.
        
        Args:
            forecasts: Lista de pronósticos
            evaluations: Lista de evaluaciones
            
        Returns:
            Diccionario con DataFrames para cada horizonte temporal
        """
        # Crear diccionario para mapear pronósticos por ID
        forecast_map = {f["id"]: f for f in forecasts}
        
        # Preparar datos para cada horizonte temporal
        short_term_data = []
        medium_term_data = []
        long_term_data = []
        
        for eval in evaluations:
            forecast_id = eval["forecast_id"]
            if forecast_id not in forecast_map:
                continue
            
            forecast = forecast_map[forecast_id]
            forecast_data = forecast["data"]
            
            # Extraer características comunes
            base_features = self._extract_base_features(forecast_data)
            
            # Procesar datos para cada horizonte temporal
            if "short_term" in eval["errors"]:
                short_term_features = base_features.copy()
                short_term_features.update({
                    "predicted_min": forecast_data["short_term"]["min"],
                    "predicted_max": forecast_data["short_term"]["max"],
                    "predicted_likely": forecast_data["short_term"]["likely"],
                    "actual": eval["errors"]["short_term"]["actual"],
                    "error_pct": eval["errors"]["short_term"]["error_pct"]
                })
                short_term_data.append(short_term_features)
            
            if "medium_term" in eval["errors"]:
                medium_term_features = base_features.copy()
                medium_term_features.update({
                    "predicted_min": forecast_data["medium_term"]["min"],
                    "predicted_max": forecast_data["medium_term"]["max"],
                    "predicted_likely": forecast_data["medium_term"]["likely"],
                    "actual": eval["errors"]["medium_term"]["actual"],
                    "error_pct": eval["errors"]["medium_term"]["error_pct"]
                })
                medium_term_data.append(medium_term_features)
            
            if "long_term" in eval["errors"]:
                long_term_features = base_features.copy()
                long_term_features.update({
                    "predicted_min": forecast_data["long_term"]["min"],
                    "predicted_max": forecast_data["long_term"]["max"],
                    "predicted_likely": forecast_data["long_term"]["likely"],
                    "actual": eval["errors"]["long_term"]["actual"],
                    "error_pct": eval["errors"]["long_term"]["error_pct"]
                })
                long_term_data.append(long_term_features)
        
        # Convertir a DataFrames
        dfs = {}
        if short_term_data:
            dfs["short_term"] = pd.DataFrame(short_term_data)
        if medium_term_data:
            dfs["medium_term"] = pd.DataFrame(medium_term_data)
        if long_term_data:
            dfs["long_term"] = pd.DataFrame(long_term_data)
        
        return dfs
    
    def _extract_base_features(self, forecast_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae características base de un pronóstico.
        
        Args:
            forecast_data: Datos del pronóstico
            
        Returns:
            Diccionario con características base
        """
        features = {}
        
        # Añadir características de tendencia
        if "trend_direction" in forecast_data:
            # Convertir dirección de tendencia a valor numérico
            trend_dir = forecast_data.get("trend_direction", "unknown")
            if trend_dir == "up":
                features["trend_direction"] = 1
            elif trend_dir == "down":
                features["trend_direction"] = -1
            else:
                features["trend_direction"] = 0
        
        # Añadir fuerza de tendencia
        features["trend_strength"] = forecast_data.get("trend_strength", 0)
        
        # Añadir volatilidad
        features["volatility"] = forecast_data.get("volatility", 0)
        
        # Añadir niveles de soporte y resistencia
        features["support_level"] = forecast_data.get("support", 0)
        features["resistance_level"] = forecast_data.get("resistance", 0)
        
        # Añadir confianza
        features["confidence"] = forecast_data.get("confidence", 0)
        
        return features
    
    def train(self, forecasts: List[Dict[str, Any]], evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Entrena modelos para mejorar pronósticos.
        
        Args:
            forecasts: Lista de pronósticos
            evaluations: Lista de evaluaciones
            
        Returns:
            Resultados del entrenamiento
        """
        # Preparar datos de entrenamiento
        data = self.prepare_training_data(forecasts, evaluations)
        
        results = {}
        
        # Entrenar modelo para pronósticos a corto plazo
        if "short_term" in data and len(data["short_term"]) >= 10:
            short_term_results = self._train_model(data["short_term"], "short_term")
            results["short_term"] = short_term_results
        
        # Entrenar modelo para pronósticos a medio plazo
        if "medium_term" in data and len(data["medium_term"]) >= 10:
            medium_term_results = self._train_model(data["medium_term"], "medium_term")
            results["medium_term"] = medium_term_results
        
        # Entrenar modelo para pronósticos a largo plazo
        if "long_term" in data and len(data["long_term"]) >= 10:
            long_term_results = self._train_model(data["long_term"], "long_term")
            results["long_term"] = long_term_results
        
        # Guardar modelos
        self._save_models()
        
        return results
    
    def _train_model(self, df: pd.DataFrame, horizon: str) -> Dict[str, Any]:
        """
        Entrena un modelo para un horizonte temporal específico.
        
        Args:
            df: DataFrame con datos de entrenamiento
            horizon: Horizonte temporal ('short_term', 'medium_term', 'long_term')
            
        Returns:
            Resultados del entrenamiento
        """
        # Preparar características y objetivo
        X = df.drop(["actual", "error_pct"], axis=1)
        y = df["actual"]
        
        # Dividir en conjuntos de entrenamiento y prueba
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Entrenar modelo
        model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluar modelo
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)
        
        # Guardar modelo
        if horizon == "short_term":
            self.short_term_model = model
        elif horizon == "medium_term":
            self.medium_term_model = model
        elif horizon == "long_term":
            self.long_term_model = model
        
        # Calcular importancia de características
        feature_importance = dict(zip(X.columns, model.feature_importances_))
        
        return {
            "mae": mae,
            "mse": mse,
            "rmse": rmse,
            "r2": r2,
            "feature_importance": feature_importance,
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
    
    def improve_forecast(self, forecast_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mejora un pronóstico utilizando los modelos entrenados.
        
        Args:
            forecast_data: Datos del pronóstico original
            
        Returns:
            Pronóstico mejorado
        """
        # Crear copia del pronóstico original
        improved_forecast = forecast_data.copy()
        
        # Extraer características base
        features = self._extract_base_features(forecast_data)
        
        # Mejorar pronóstico a corto plazo
        if self.short_term_model and "short_term" in forecast_data:
            short_term_features = features.copy()
            short_term_features.update({
                "predicted_min": forecast_data["short_term"]["min"],
                "predicted_max": forecast_data["short_term"]["max"],
                "predicted_likely": forecast_data["short_term"]["likely"]
            })
            
            # Convertir a DataFrame
            X = pd.DataFrame([short_term_features])
            
            # Predecir precio mejorado
            improved_price = self.short_term_model.predict(X)[0]
            
            # Actualizar pronóstico
            improved_forecast["short_term"]["likely"] = improved_price
            improved_forecast["short_term"]["ai_adjusted"] = True
        
        # Mejorar pronóstico a medio plazo
        if self.medium_term_model and "medium_term" in forecast_data:
            medium_term_features = features.copy()
            medium_term_features.update({
                "predicted_min": forecast_data["medium_term"]["min"],
                "predicted_max": forecast_data["medium_term"]["max"],
                "predicted_likely": forecast_data["medium_term"]["likely"]
            })
            
            # Convertir a DataFrame
            X = pd.DataFrame([medium_term_features])
            
            # Predecir precio mejorado
            improved_price = self.medium_term_model.predict(X)[0]
            
            # Actualizar pronóstico
            improved_forecast["medium_term"]["likely"] = improved_price
            improved_forecast["medium_term"]["ai_adjusted"] = True
        
        # Mejorar pronóstico a largo plazo
        if self.long_term_model and "long_term" in forecast_data:
            long_term_features = features.copy()
            long_term_features.update({
                "predicted_min": forecast_data["long_term"]["min"],
                "predicted_max": forecast_data["long_term"]["max"],
                "predicted_likely": forecast_data["long_term"]["likely"]
            })
            
            # Convertir a DataFrame
            X = pd.DataFrame([long_term_features])
            
            # Predecir precio mejorado
            improved_price = self.long_term_model.predict(X)[0]
            
            # Actualizar pronóstico
            improved_forecast["long_term"]["likely"] = improved_price
            improved_forecast["long_term"]["ai_adjusted"] = True
        
        # Añadir metadatos de mejora
        improved_forecast["ai_improved"] = True
        improved_forecast["ai_improvement_timestamp"] = datetime.datetime.now().isoformat()
        
        return improved_forecast
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre los modelos entrenados.
        
        Returns:
            Información sobre los modelos
        """
        info = {
            "short_term": {
                "trained": self.short_term_model is not None,
                "type": str(type(self.short_term_model).__name__) if self.short_term_model else None
            },
            "medium_term": {
                "trained": self.medium_term_model is not None,
                "type": str(type(self.medium_term_model).__name__) if self.medium_term_model else None
            },
            "long_term": {
                "trained": self.long_term_model is not None,
                "type": str(type(self.long_term_model).__name__) if self.long_term_model else None
            }
        }
        
        # Añadir información de características si los modelos están entrenados
        if self.short_term_model:
            info["short_term"]["feature_importance"] = dict(zip(
                self.short_term_model.feature_names_in_,
                self.short_term_model.feature_importances_
            ))
        
        if self.medium_term_model:
            info["medium_term"]["feature_importance"] = dict(zip(
                self.medium_term_model.feature_names_in_,
                self.medium_term_model.feature_importances_
            ))
        
        if self.long_term_model:
            info["long_term"]["feature_importance"] = dict(zip(
                self.long_term_model.feature_names_in_,
                self.long_term_model.feature_importances_
            ))
        
        return info
