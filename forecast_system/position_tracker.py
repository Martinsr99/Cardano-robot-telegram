"""
Position Tracker - Gestiona las posiciones abiertas basadas en alertas
"""

import os
import csv
import datetime
from typing import Dict, List, Any, Optional
from datetime import datetime

class PositionTracker:
    """
    Clase para gestionar posiciones abiertas basadas en alertas de pronóstico.
    Utiliza CSV para almacenar las posiciones para mayor simplicidad y compatibilidad.
    """
    def __init__(self, data_dir: str = "forecast_system/data"):
        """
        Inicializa el gestor de posiciones.
        
        Args:
            data_dir: Directorio donde se almacenarán los datos
        """
        self.data_dir = data_dir
        self.positions_file = os.path.join(data_dir, "open_positions.csv")
        self.closed_positions_file = os.path.join(data_dir, "closed_positions.csv")
        
        # Crear directorio si no existe
        os.makedirs(data_dir, exist_ok=True)
        
        # Crear archivos CSV si no existen
        self._initialize_csv_files()
        
        # Cargar posiciones existentes
        self.open_positions = self._load_open_positions()
        self.closed_positions = self._load_closed_positions()
    
    def _initialize_csv_files(self):
        """Inicializa los archivos CSV con encabezados si no existen"""
        # Archivo de posiciones abiertas
        if not os.path.exists(self.positions_file):
            with open(self.positions_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'id', 'alert_id', 'alert_type', 'symbol', 'entry_price', 
                    'entry_timestamp', 'horizon', 'expected_change_pct', 'status'
                ])
        
        # Archivo de posiciones cerradas
        if not os.path.exists(self.closed_positions_file):
            with open(self.closed_positions_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'id', 'alert_id', 'alert_type', 'symbol', 'entry_price', 
                    'entry_timestamp', 'exit_price', 'exit_timestamp', 
                    'horizon', 'expected_change_pct', 'actual_change_pct',
                    'profit_loss', 'status', 'result'
                ])
    
    def _load_open_positions(self) -> List[Dict[str, Any]]:
        """Carga las posiciones abiertas desde el archivo CSV"""
        positions = []
        if os.path.exists(self.positions_file):
            with open(self.positions_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    positions.append(row)
        return positions
    
    def _load_closed_positions(self) -> List[Dict[str, Any]]:
        """Carga las posiciones cerradas desde el archivo CSV"""
        positions = []
        if os.path.exists(self.closed_positions_file):
            with open(self.closed_positions_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    positions.append(row)
        return positions
    
    def _save_open_positions(self):
        """Guarda las posiciones abiertas en el archivo CSV"""
        with open(self.positions_file, 'w', newline='') as f:
            if self.open_positions:
                writer = csv.DictWriter(f, fieldnames=self.open_positions[0].keys())
                writer.writeheader()
                writer.writerows(self.open_positions)
            else:
                writer = csv.writer(f)
                writer.writerow([
                    'id', 'alert_id', 'alert_type', 'symbol', 'entry_price', 
                    'entry_timestamp', 'horizon', 'expected_change_pct', 'status'
                ])
    
    def _save_closed_positions(self):
        """Guarda las posiciones cerradas en el archivo CSV"""
        with open(self.closed_positions_file, 'w', newline='') as f:
            if self.closed_positions:
                writer = csv.DictWriter(f, fieldnames=self.closed_positions[0].keys())
                writer.writeheader()
                writer.writerows(self.closed_positions)
            else:
                writer = csv.writer(f)
                writer.writerow([
                    'id', 'alert_id', 'alert_type', 'symbol', 'entry_price', 
                    'entry_timestamp', 'exit_price', 'exit_timestamp', 
                    'horizon', 'expected_change_pct', 'actual_change_pct',
                    'profit_loss', 'status', 'result'
                ])
    
    def open_position_from_alert(self, alert_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Abre una nueva posición basada en una alerta.
        
        Args:
            alert_data: Datos de la alerta
            symbol: Símbolo del activo
            
        Returns:
            Datos de la posición abierta
        """
        # Generar ID único para la posición
        position_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Determinar tipo de alerta y cambio esperado
        alert_type = "rise" if "rise_pct" in alert_data else "drop"
        expected_change_pct = alert_data.get("rise_pct", alert_data.get("drop_pct", 0))
        horizon = alert_data.get("rise_horizon", alert_data.get("drop_horizon", "unknown"))
        
        # Crear entrada de posición
        position = {
            "id": position_id,
            "alert_id": alert_data["id"],
            "alert_type": alert_type,
            "symbol": symbol,
            "entry_price": alert_data["current_price"],
            "entry_timestamp": alert_data["timestamp"],
            "horizon": horizon,
            "expected_change_pct": str(expected_change_pct),
            "status": "open"
        }
        
        # Añadir a la lista de posiciones abiertas
        self.open_positions.append(position)
        
        # Guardar
        self._save_open_positions()
        
        return position
    
    def close_position(self, position_id: str, exit_price: float) -> Optional[Dict[str, Any]]:
        """
        Cierra una posición abierta.
        
        Args:
            position_id: ID de la posición a cerrar
            exit_price: Precio de salida
            
        Returns:
            Datos de la posición cerrada o None si no se encuentra
        """
        # Buscar la posición
        position = None
        position_index = -1
        
        for i, p in enumerate(self.open_positions):
            if p["id"] == position_id:
                position = p
                position_index = i
                break
        
        if position is None:
            return None
        
        # Calcular cambio real y ganancia/pérdida
        entry_price = float(position["entry_price"])
        actual_change_pct = (exit_price - entry_price) / entry_price * 100
        
        # Para posiciones de bajada, la ganancia es inversa
        if position["alert_type"] == "drop":
            profit_loss = -actual_change_pct
        else:
            profit_loss = actual_change_pct
        
        # Determinar resultado
        if profit_loss > 0:
            result = "profit"
        else:
            result = "loss"
        
        # Crear entrada de posición cerrada
        closed_position = position.copy()
        closed_position.update({
            "exit_price": str(exit_price),
            "exit_timestamp": datetime.now().isoformat(),
            "actual_change_pct": str(actual_change_pct),
            "profit_loss": str(profit_loss),
            "status": "closed",
            "result": result
        })
        
        # Añadir a la lista de posiciones cerradas
        self.closed_positions.append(closed_position)
        
        # Eliminar de la lista de posiciones abiertas
        self.open_positions.pop(position_index)
        
        # Guardar
        self._save_open_positions()
        self._save_closed_positions()
        
        return closed_position
    
    def close_positions_by_horizon(self, current_price: float) -> List[Dict[str, Any]]:
        """
        Cierra las posiciones cuyo horizonte temporal ha expirado.
        
        Args:
            current_price: Precio actual para el cierre
            
        Returns:
            Lista de posiciones cerradas
        """
        closed_positions = []
        now = datetime.now()
        
        # Copiar la lista para evitar problemas al modificarla durante la iteración
        positions_to_check = self.open_positions.copy()
        
        for position in positions_to_check:
            # Obtener timestamp de entrada
            entry_timestamp = datetime.fromisoformat(position["entry_timestamp"])
            
            # Determinar si ha pasado suficiente tiempo según el horizonte
            should_close = False
            
            if "corto plazo (24h)" in position["horizon"]:
                # Cerrar después de 24-30 horas
                hours_passed = (now - entry_timestamp).total_seconds() / 3600
                should_close = hours_passed >= 24
            
            elif "medio plazo (3-5 días)" in position["horizon"]:
                # Cerrar después de 4 días
                days_passed = (now - entry_timestamp).days
                should_close = days_passed >= 4
            
            elif "largo plazo (1-2 semanas)" in position["horizon"]:
                # Cerrar después de 10 días
                days_passed = (now - entry_timestamp).days
                should_close = days_passed >= 10
            
            # Cerrar la posición si es necesario
            if should_close:
                closed_position = self.close_position(position["id"], current_price)
                if closed_position:
                    closed_positions.append(closed_position)
        
        return closed_positions
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las posiciones abiertas.
        
        Returns:
            Lista de posiciones abiertas
        """
        return self.open_positions
    
    def get_closed_positions(self, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Obtiene las posiciones cerradas más recientes.
        
        Args:
            limit: Número máximo de posiciones a devolver (0 para todas)
            
        Returns:
            Lista de posiciones cerradas
        """
        # Ordenar por timestamp de salida (más reciente primero)
        sorted_positions = sorted(
            self.closed_positions,
            key=lambda x: x["exit_timestamp"],
            reverse=True
        )
        
        if limit > 0:
            return sorted_positions[:limit]
        else:
            return sorted_positions
    
    def get_position_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de las posiciones.
        
        Returns:
            Estadísticas de posiciones
        """
        if not self.closed_positions:
            return {"message": "No hay posiciones cerradas"}
        
        # Calcular estadísticas generales
        total_positions = len(self.closed_positions)
        profitable_positions = [p for p in self.closed_positions if p["result"] == "profit"]
        total_profitable = len(profitable_positions)
        win_rate = total_profitable / total_positions * 100 if total_positions > 0 else 0
        
        # Calcular ganancia/pérdida promedio
        profit_loss_values = [float(p["profit_loss"]) for p in self.closed_positions]
        avg_profit = sum(profit_loss_values) / len(profit_loss_values) if profit_loss_values else 0
        
        # Calcular ganancia/pérdida total
        total_profit = sum(profit_loss_values)
        
        # Calcular estadísticas por tipo de alerta
        rise_positions = [p for p in self.closed_positions if p["alert_type"] == "rise"]
        drop_positions = [p for p in self.closed_positions if p["alert_type"] == "drop"]
        
        rise_stats = {}
        if rise_positions:
            rise_profitable = [p for p in rise_positions if p["result"] == "profit"]
            rise_win_rate = len(rise_profitable) / len(rise_positions) * 100
            rise_profit_loss = [float(p["profit_loss"]) for p in rise_positions]
            rise_avg_profit = sum(rise_profit_loss) / len(rise_profit_loss)
            
            rise_stats = {
                "total": len(rise_positions),
                "profitable": len(rise_profitable),
                "win_rate": rise_win_rate,
                "avg_profit": rise_avg_profit
            }
        
        drop_stats = {}
        if drop_positions:
            drop_profitable = [p for p in drop_positions if p["result"] == "profit"]
            drop_win_rate = len(drop_profitable) / len(drop_positions) * 100
            drop_profit_loss = [float(p["profit_loss"]) for p in drop_positions]
            drop_avg_profit = sum(drop_profit_loss) / len(drop_profit_loss)
            
            drop_stats = {
                "total": len(drop_positions),
                "profitable": len(drop_profitable),
                "win_rate": drop_win_rate,
                "avg_profit": drop_avg_profit
            }
        
        return {
            "total_positions": total_positions,
            "open_positions": len(self.open_positions),
            "closed_positions": total_positions,
            "profitable_positions": total_profitable,
            "win_rate": win_rate,
            "avg_profit": avg_profit,
            "total_profit": total_profit,
            "rise_stats": rise_stats,
            "drop_stats": drop_stats
        }
    
    def calculate_current_position_status(self, position: Dict[str, Any], current_price: float) -> Dict[str, Any]:
        """
        Calcula el estado actual de una posición abierta.
        
        Args:
            position: Datos de la posición
            current_price: Precio actual
            
        Returns:
            Estado actual de la posición
        """
        entry_price = float(position["entry_price"])
        current_change_pct = (current_price - entry_price) / entry_price * 100
        
        # Para posiciones de bajada, la ganancia es inversa
        if position["alert_type"] == "drop":
            current_profit_loss = -current_change_pct
        else:
            current_profit_loss = current_change_pct
        
        # Determinar estado
        if current_profit_loss > 0:
            status = "profit"
        else:
            status = "loss"
        
        return {
            "current_price": current_price,
            "current_change_pct": current_change_pct,
            "current_profit_loss": current_profit_loss,
            "status": status
        }
