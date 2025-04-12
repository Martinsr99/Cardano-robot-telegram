"""
User interface for the trading bot.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font
import threading
import time
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
from config import SYMBOL, CHECK_INTERVAL, PROFIT_TARGET, STOP_LOSS
from utils import format_price, format_profit_loss

class TradingBotUI:
    """
    Graphical user interface for the trading bot.
    """
    def __init__(self, root, bot):
        """Initialize the UI"""
        self.root = root
        self.bot = bot
        self.update_interval = 10  # Update UI every 10 seconds
        self.is_running = False
        self.bot_thread = None
        
        # Register callbacks
        self.bot.register_callback('on_price_update', self.on_price_update)
        self.bot.register_callback('on_analysis_complete', self.on_analysis_complete)
        self.bot.register_callback('on_position_update', self.on_position_update)
        self.bot.register_callback('on_signal', self.on_signal)
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI components"""
        # Set theme and style
        self._setup_styles()
        
        self.root.title(f"Advanced Trading Bot - {SYMBOL}")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Set icon (if available)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass  # Icon not available, use default
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header frame
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Add logo/title
        title_label = ttk.Label(header_frame, text="Advanced Trading Bot", 
                               font=("Helvetica", 18, "bold"))
        title_label.pack(side=tk.LEFT, padx=5)
        
        symbol_label = ttk.Label(header_frame, text=f"({SYMBOL})", 
                               font=("Helvetica", 14))
        symbol_label.pack(side=tk.LEFT, padx=5)
        
        # Create top frame for current status
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Current price and status
        status_frame = ttk.LabelFrame(top_frame, text="Estado Actual", padding=15)
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Price label with larger font
        self.price_var = tk.StringVar(value="Precio: Cargando...")
        price_label = ttk.Label(status_frame, textvariable=self.price_var, 
                              font=("Helvetica", 18, "bold"), style="Price.TLabel")
        price_label.pack(anchor=tk.W, pady=5)
        
        # Create a frame for status indicators
        status_indicators_frame = ttk.Frame(status_frame)
        status_indicators_frame.pack(fill=tk.X, pady=5)
        
        # Last analysis label
        analysis_frame = ttk.Frame(status_indicators_frame)
        analysis_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        analysis_icon = ttk.Label(analysis_frame, text="🕒", font=("Helvetica", 12))
        analysis_icon.pack(side=tk.LEFT, padx=(0, 5))
        
        self.analysis_var = tk.StringVar(value="Último análisis: N/A")
        analysis_label = ttk.Label(analysis_frame, textvariable=self.analysis_var)
        analysis_label.pack(side=tk.LEFT, pady=2)
        
        # Position status with icon
        position_frame = ttk.Frame(status_indicators_frame)
        position_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        position_icon = ttk.Label(position_frame, text="📊", font=("Helvetica", 12))
        position_icon.pack(side=tk.LEFT, padx=(0, 5))
        
        self.position_var = tk.StringVar(value="Posición: No hay posición activa")
        position_label = ttk.Label(position_frame, textvariable=self.position_var)
        position_label.pack(side=tk.LEFT, pady=2)
        
        # Profit/Loss with icon and color
        pl_frame = ttk.Frame(status_frame)
        pl_frame.pack(fill=tk.X, pady=5)
        
        pl_icon = ttk.Label(pl_frame, text="💰", font=("Helvetica", 12))
        pl_icon.pack(side=tk.LEFT, padx=(0, 5))
        
        self.pl_var = tk.StringVar(value="P/L: N/A")
        self.pl_label = ttk.Label(pl_frame, textvariable=self.pl_var)
        self.pl_label.pack(side=tk.LEFT, pady=2)
        
        # Control frame
        control_frame = ttk.LabelFrame(top_frame, text="Control", padding=15, width=250)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))
        control_frame.pack_propagate(False)
        
        # Start/Stop button with icon
        self.start_button = ttk.Button(control_frame, text="▶️ Iniciar Bot", 
                                     command=self.toggle_bot, style="Action.TButton")
        self.start_button.pack(fill=tk.X, pady=5)
        
        # Force analysis button with icon
        self.analyze_button = ttk.Button(control_frame, text="🔄 Analizar Ahora", 
                                       command=self.force_analysis, style="Secondary.TButton")
        self.analyze_button.pack(fill=tk.X, pady=5)
        self.analyze_button.config(state=tk.DISABLED)
        
        # Add refresh data button
        self.refresh_button = ttk.Button(control_frame, text="📥 Actualizar Datos", 
                                       command=self.refresh_data, style="Secondary.TButton")
        self.refresh_button.pack(fill=tk.X, pady=5)
        
        # Create notebook for tabs with custom style
        notebook = ttk.Notebook(main_frame, style="Custom.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.history_tab = ttk.Frame(notebook, padding=10)
        self.signals_tab = ttk.Frame(notebook, padding=10)
        self.chart_tab = ttk.Frame(notebook, padding=10)
        self.log_tab = ttk.Frame(notebook, padding=10)
        
        notebook.add(self.history_tab, text="Historial")
        notebook.add(self.signals_tab, text="Señales")
        notebook.add(self.chart_tab, text="Gráfico")
        notebook.add(self.log_tab, text="Log")
        
        # Setup history tab
        self._setup_history_tab()
        
        # Setup signals tab
        self._setup_signals_tab()
        
        # Setup chart tab
        self._setup_chart_tab()
        
        # Setup log tab
        self._setup_log_tab()
        
        # Status bar
        status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(10, 5))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Listo")
        status_label = ttk.Label(status_bar, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT)
        
        # Add version info
        version_label = ttk.Label(status_bar, text="v1.0.0", anchor=tk.E)
        version_label.pack(side=tk.RIGHT)
        
        # Update UI
        self.update_ui()
    
    def _setup_styles(self):
        """Setup custom styles for the UI"""
        # Create custom style
        style = ttk.Style()
        
        # Configure colors
        bg_color = "#f5f5f5"
        accent_color = "#4a6fa5"
        success_color = "#28a745"
        danger_color = "#dc3545"
        warning_color = "#ffc107"
        
        # Configure fonts
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Helvetica", size=10)
        
        # Configure theme
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color)
        style.configure("TLabelframe", background=bg_color)
        style.configure("TLabelframe.Label", background=bg_color, font=("Helvetica", 11, "bold"))
        
        # Configure notebook
        style.configure("Custom.TNotebook", background=bg_color, tabmargins=[2, 5, 2, 0])
        style.configure("Custom.TNotebook.Tab", background="#e1e1e1", padding=[10, 5], font=("Helvetica", 10))
        style.map("Custom.TNotebook.Tab", background=[("selected", accent_color)], 
                 foreground=[("selected", "white")])
        
        # Configure buttons
        style.configure("TButton", font=("Helvetica", 10))
        style.configure("Action.TButton", font=("Helvetica", 11, "bold"))
        style.configure("Secondary.TButton", font=("Helvetica", 10))
        
        # Configure treeview
        style.configure("Treeview", 
                       background="white", 
                       fieldbackground="white",
                       font=("Helvetica", 10))
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        
        # Configure price label
        style.configure("Price.TLabel", foreground=accent_color)
        
        # Configure profit/loss labels
        style.configure("Profit.TLabel", foreground=success_color)
        style.configure("Loss.TLabel", foreground=danger_color)
    
    def _setup_history_tab(self):
        """Setup the history tab"""
        # Create frame for filters
        filter_frame = ttk.Frame(self.history_tab)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Add filter label
        filter_label = ttk.Label(filter_frame, text="Filtrar por:")
        filter_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Add filter options
        self.filter_var = tk.StringVar(value="Todos")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                  values=["Todos", "Cerradas", "Abiertas", "Ganancias", "Pérdidas"],
                                  width=15, state="readonly")
        filter_combo.pack(side=tk.LEFT)
        filter_combo.bind("<<ComboboxSelected>>", self.filter_history)
        
        # Add refresh button
        refresh_btn = ttk.Button(filter_frame, text="Actualizar", 
                               command=self.update_history_tab, width=10)
        refresh_btn.pack(side=tk.RIGHT)
        
        # Create treeview for trade history
        columns = ("date", "type", "price", "quantity", "profit", "reason", "duration")
        self.history_tree = ttk.Treeview(self.history_tab, columns=columns, show="headings", style="Treeview")
        
        # Define headings
        self.history_tree.heading("date", text="Fecha")
        self.history_tree.heading("type", text="Tipo")
        self.history_tree.heading("price", text="Precio")
        self.history_tree.heading("quantity", text="Cantidad")
        self.history_tree.heading("profit", text="Beneficio/Pérdida")
        self.history_tree.heading("reason", text="Razón")
        self.history_tree.heading("duration", text="Duración")
        
        # Define columns
        self.history_tree.column("date", width=150)
        self.history_tree.column("type", width=80)
        self.history_tree.column("price", width=100)
        self.history_tree.column("quantity", width=100)
        self.history_tree.column("profit", width=120)
        self.history_tree.column("reason", width=200)
        self.history_tree.column("duration", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.history_tab, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load initial data
        self.update_history_tab()
    
    def _setup_signals_tab(self):
        """Setup the signals tab"""
        # Create frame for filters
        filter_frame = ttk.Frame(self.signals_tab)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Add filter label
        filter_label = ttk.Label(filter_frame, text="Filtrar por:")
        filter_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Add filter options
        self.signal_filter_var = tk.StringVar(value="Todos")
        signal_filter_combo = ttk.Combobox(filter_frame, textvariable=self.signal_filter_var, 
                                         values=["Todos", "Compra", "Venta", "Error"],
                                         width=15, state="readonly")
        signal_filter_combo.pack(side=tk.LEFT)
        signal_filter_combo.bind("<<ComboboxSelected>>", self.filter_signals)
        
        # Add refresh button
        refresh_btn = ttk.Button(filter_frame, text="Actualizar", 
                               command=self.update_signals_tab, width=10)
        refresh_btn.pack(side=tk.RIGHT)
        
        # Create treeview for signals
        columns = ("date", "type", "price", "strength", "reason")
        self.signals_tree = ttk.Treeview(self.signals_tab, columns=columns, show="headings", style="Treeview")
        
        # Define headings
        self.signals_tree.heading("date", text="Fecha")
        self.signals_tree.heading("type", text="Tipo")
        self.signals_tree.heading("price", text="Precio")
        self.signals_tree.heading("strength", text="Fuerza")
        self.signals_tree.heading("reason", text="Razón")
        
        # Define columns
        self.signals_tree.column("date", width=150)
        self.signals_tree.column("type", width=80)
        self.signals_tree.column("price", width=100)
        self.signals_tree.column("strength", width=100)
        self.signals_tree.column("reason", width=400)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.signals_tab, orient=tk.VERTICAL, command=self.signals_tree.yview)
        self.signals_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.signals_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load initial data
        self.update_signals_tab()
    
    def _setup_chart_tab(self):
        """Setup the chart tab"""
        # Create control frame
        control_frame = ttk.Frame(self.chart_tab)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Add timeframe selector
        timeframe_label = ttk.Label(control_frame, text="Periodo:")
        timeframe_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.timeframe_var = tk.StringVar(value="Todo")
        timeframe_combo = ttk.Combobox(control_frame, textvariable=self.timeframe_var, 
                                     values=["Todo", "1 Semana", "1 Mes", "3 Meses"],
                                     width=15, state="readonly")
        timeframe_combo.pack(side=tk.LEFT)
        timeframe_combo.bind("<<ComboboxSelected>>", self.update_chart_timeframe)
        
        # Add indicator checkboxes
        self.show_sma_var = tk.BooleanVar(value=True)
        sma_check = ttk.Checkbutton(control_frame, text="SMA", variable=self.show_sma_var, 
                                  command=self.update_chart)
        sma_check.pack(side=tk.LEFT, padx=10)
        
        self.show_bb_var = tk.BooleanVar(value=False)
        bb_check = ttk.Checkbutton(control_frame, text="Bollinger", variable=self.show_bb_var, 
                                 command=self.update_chart)
        bb_check.pack(side=tk.LEFT, padx=10)
        
        # Create figure and canvas with improved styling
        self.figure = plt.Figure(figsize=(10, 6), dpi=100)
        self.figure.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.15)
        self.ax = self.figure.add_subplot(111)
        
        # Style the chart
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.tick_params(axis='both', which='major', labelsize=9)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self.chart_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar_frame = ttk.Frame(self.chart_tab)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        
        # Initial plot
        self.update_chart()
    
    def _setup_log_tab(self):
        """Setup the log tab"""
        # Create control frame
        control_frame = ttk.Frame(self.log_tab)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Add clear button
        clear_btn = ttk.Button(control_frame, text="Limpiar Log", 
                             command=self.clear_log, width=15)
        clear_btn.pack(side=tk.RIGHT)
        
        # Add log level filter
        level_label = ttk.Label(control_frame, text="Nivel:")
        level_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.log_level_var = tk.StringVar(value="Todo")
        level_combo = ttk.Combobox(control_frame, textvariable=self.log_level_var, 
                                 values=["Todo", "Info", "Error", "Señal"],
                                 width=15, state="readonly")
        level_combo.pack(side=tk.LEFT)
        level_combo.bind("<<ComboboxSelected>>", self.filter_log)
        
        # Create text widget with improved styling
        self.log_text = scrolledtext.ScrolledText(self.log_tab, wrap=tk.WORD, 
                                               font=("Consolas", 10),
                                               background="#f8f9fa",
                                               foreground="#212529")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Configure text tags for colored output
        self.log_text.tag_configure("error", foreground="#dc3545")
        self.log_text.tag_configure("warning", foreground="#ffc107")
        self.log_text.tag_configure("success", foreground="#28a745")
        self.log_text.tag_configure("info", foreground="#17a2b8")
        
        # Redirect stdout to log
        import sys
        self.original_stdout = sys.stdout
        sys.stdout = self
    
    def write(self, text):
        """Write to log (for stdout redirection)"""
        self.log_text.config(state=tk.NORMAL)
        
        # Apply tags based on content
        if "❌" in text or "Error" in text or "error" in text:
            self.log_text.insert(tk.END, text, "error")
        elif "⚠️" in text or "Warning" in text:
            self.log_text.insert(tk.END, text, "warning")
        elif "✅" in text or "éxito" in text:
            self.log_text.insert(tk.END, text, "success")
        elif "📊" in text or "📈" in text or "📉" in text:
            self.log_text.insert(tk.END, text, "info")
        else:
            self.log_text.insert(tk.END, text)
            
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Also write to original stdout
        self.original_stdout.write(text)
    
    def flush(self):
        """Flush (for stdout redirection)"""
        pass
    
    def update_ui(self):
        """Update the UI"""
        try:
            # Update price
            if self.bot.last_price:
                self.price_var.set(f"Precio: {format_price(self.bot.last_price)}")
            
            # Update last analysis
            if self.bot.last_analysis_time:
                time_str = self.bot.last_analysis_time.strftime("%H:%M:%S")
                self.analysis_var.set(f"Último análisis: {time_str}")
            
            # Update position
            if self.bot.position.active:
                self.position_var.set(f"Posición: {self.bot.position.symbol} a {format_price(self.bot.position.entry_price)}")
                
                # Update P/L
                if self.bot.last_price and self.bot.position.entry_price:
                    profit_pct = (self.bot.last_price - self.bot.position.entry_price) / self.bot.position.entry_price
                    profit_amount = self.bot.position.quantity * self.bot.position.entry_price * profit_pct
                    
                    # Update P/L with color
                    pl_text = f"P/L: {profit_pct:.2%} ({format_price(profit_amount)})"
                    self.pl_var.set(pl_text)
                    
                    # Set label style based on profit/loss
                    if profit_pct > 0:
                        self.pl_label.configure(style="Profit.TLabel")
                    else:
                        self.pl_label.configure(style="Loss.TLabel")
                    
                    # Update take profit and stop loss lines in chart
                    self.update_chart()
            else:
                self.position_var.set("Posición: No hay posición activa")
                self.pl_var.set("P/L: N/A")
            
            # Schedule next update
            self.root.after(1000, self.update_ui)
            
        except Exception as e:
            print(f"Error updating UI: {e}")
            # Schedule next update even if there's an error
            self.root.after(1000, self.update_ui)
    
    def filter_history(self, event=None):
        """Filter history based on selected filter"""
        self.update_history_tab()
    
    def filter_signals(self, event=None):
        """Filter signals based on selected filter"""
        self.update_signals_tab()
    
    def filter_log(self, event=None):
        """Filter log based on selected level"""
        # This would require storing the full log and re-displaying filtered content
        # For simplicity, we'll just clear and continue with filtered logging
        pass
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def refresh_data(self):
        """Refresh market data"""
        if not self.is_running:
            try:
                self.status_var.set("Actualizando datos del mercado...")
                success = self.bot.market_data.fetch_data()
                
                if success:
                    self.last_price = self.bot.market_data.get_latest_price()
                    self.price_var.set(f"Precio: {format_price(self.last_price)}")
                    self.update_chart()
                    self.status_var.set("Datos actualizados correctamente")
                    messagebox.showinfo("Actualización", "Datos de mercado actualizados correctamente")
                else:
                    self.status_var.set("Error al actualizar datos")
                    messagebox.showerror("Error", "No se pudieron actualizar los datos del mercado")
            except Exception as e:
                self.status_var.set(f"Error: {str(e)}")
                messagebox.showerror("Error", f"Error al actualizar datos: {str(e)}")
        else:
            messagebox.showinfo("Información", "El bot está en ejecución y actualizará los datos automáticamente")
    
    def update_chart_timeframe(self, event=None):
        """Update chart based on selected timeframe"""
        self.update_chart()
    
    def update_history_tab(self):
        """Update the history tab"""
        # Clear current items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Get trades from history
        trades = self.bot.history.trades
        
        # Add trades to treeview
        for trade in trades:
            # Skip trades without entry time
            if 'entry_time' not in trade:
                continue
            
            # Parse entry time
            try:
                entry_time = datetime.datetime.fromisoformat(trade['entry_time'])
                date_str = entry_time.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = "Unknown"
            
            # Determine type
            if trade.get('status') == 'closed':
                trade_type = "Cerrada"
                
                # Calculate profit
                profit_pct = trade.get('profit_pct', 0)
                profit_amount = trade.get('profit_amount', 0)
                profit_str = f"{profit_pct:.2%} ({format_price(profit_amount)})"
                
                # Format duration
                duration_seconds = trade.get('duration_seconds', 0)
                if duration_seconds:
                    hours, remainder = divmod(duration_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    duration = f"{int(hours)}h {int(minutes)}m"
                else:
                    duration = "N/A"
                
                # Format price
                price_str = f"{format_price(trade.get('entry_price', 0))} → {format_price(trade.get('exit_price', 0))}"
                
                # Get reason
                reason = trade.get('exit_reason', 'Unknown')
            else:
                trade_type = "Abierta"
                profit_str = "N/A"
                duration = "En curso"
                price_str = format_price(trade.get('entry_price', 0))
                reason = trade.get('entry_reason', 'Unknown')
            
            # Add to treeview
            self.history_tree.insert("", tk.END, values=(
                date_str,
                trade_type,
                price_str,
                f"{trade.get('quantity', 0):.6f}",
                profit_str,
                reason,
                duration
            ))
    
    def update_signals_tab(self):
        """Update the signals tab"""
        # Clear current items
        for item in self.signals_tree.get_children():
            self.signals_tree.delete(item)
        
        # Get alerts from history
        alerts = self.bot.history.alerts
        
        # Filter alerts based on selection
        filter_type = self.signal_filter_var.get()
        if filter_type != "Todos":
            if filter_type == "Compra":
                alerts = [a for a in alerts if a.get('type') == 'buy']
            elif filter_type == "Venta":
                alerts = [a for a in alerts if a.get('type') == 'sell']
            elif filter_type == "Error":
                alerts = [a for a in alerts if 'error' in a.get('type', '')]
        """Update the signals tab"""
        # Clear current items
        for item in self.signals_tree.get_children():
            self.signals_tree.delete(item)
        
        # Get alerts from history
        alerts = self.bot.history.alerts
        
        # Add alerts to treeview
        for alert in alerts:
            # Skip alerts without timestamp
            if 'timestamp' not in alert:
                continue
            
            # Parse timestamp
            try:
                timestamp = datetime.datetime.fromisoformat(alert['timestamp'])
                date_str = timestamp.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = "Unknown"
            
            # Get alert type
            alert_type = alert.get('type', 'Unknown')
            
            # Format based on type
            if alert_type == 'buy':
                type_str = "Compra"
                price = alert.get('data', {}).get('price', 0)
                price_str = format_price(price)
                strength = alert.get('data', {}).get('strength', 0)
                strength_str = f"{strength:.2f}"
                reason = alert.get('message', 'Unknown')
            elif alert_type == 'sell':
                type_str = "Venta"
                price = alert.get('data', {}).get('exit_price', 0)
                price_str = format_price(price)
                strength_str = "N/A"
                reason = alert.get('message', 'Unknown')
            else:
                type_str = alert_type
                price_str = "N/A"
                strength_str = "N/A"
                reason = alert.get('message', 'Unknown')
            
            # Add to treeview
            self.signals_tree.insert("", tk.END, values=(
                date_str,
                type_str,
                price_str,
                strength_str,
                reason
            ))
    
    def update_chart(self):
        """Update the chart"""
        """Update the chart"""
        try:
            # Clear previous plot
            self.ax.clear()
            
            # Get price data
            if not self.bot.market_data.data:
                self.ax.set_title("No hay datos disponibles")
                self.canvas.draw()
                return
            
            dates = self.bot.market_data.dates
            prices = self.bot.market_data.data['close']
            
            # Plot prices
            self.ax.plot(dates, prices, label='Precio')
            
            # Add moving averages if available
            if self.bot.market_data.indicators:
                sma_short = self.bot.market_data.indicators.get('sma_short')
                sma_long = self.bot.market_data.indicators.get('sma_long')
                
                if sma_short is not None and len(sma_short) == len(dates):
                    self.ax.plot(dates, sma_short, label='SMA Corta', linestyle='--')
                
                if sma_long is not None and len(sma_long) == len(dates):
                    self.ax.plot(dates, sma_long, label='SMA Larga', linestyle='-.')
            
            # Add entry/exit points from history
            for trade in self.bot.history.trades:
                if 'entry_time' in trade and 'entry_price' in trade:
                    try:
                        entry_time = datetime.datetime.fromisoformat(trade['entry_time'])
                        entry_price = trade['entry_price']
                        self.ax.scatter([entry_time], [entry_price], color='green', marker='^', s=100, label='_nolegend_')
                    except:
                        pass
                
                if 'exit_time' in trade and 'exit_price' in trade:
                    try:
                        exit_time = datetime.datetime.fromisoformat(trade['exit_time'])
                        exit_price = trade['exit_price']
                        self.ax.scatter([exit_time], [exit_price], color='red', marker='v', s=100, label='_nolegend_')
                    except:
                        pass
            
            # Add current position take profit and stop loss lines
            if self.bot.position.active and self.bot.position.entry_price:
                take_profit = self.bot.position.entry_price * (1 + PROFIT_TARGET)
                stop_loss = self.bot.position.entry_price * (1 - STOP_LOSS)
                
                self.ax.axhline(y=take_profit, color='g', linestyle='--', alpha=0.5, label=f'Take Profit ({PROFIT_TARGET:.1%})')
                self.ax.axhline(y=stop_loss, color='r', linestyle='--', alpha=0.5, label=f'Stop Loss ({STOP_LOSS:.1%})')
            
            # Apply timeframe filter
            timeframe = self.timeframe_var.get()
            if timeframe != "Todo":
                import pandas as pd
                end_date = dates[-1]
                
                if timeframe == "1 Semana":
                    start_date = end_date - pd.Timedelta(days=7)
                elif timeframe == "1 Mes":
                    start_date = end_date - pd.Timedelta(days=30)
                elif timeframe == "3 Meses":
                    start_date = end_date - pd.Timedelta(days=90)
                
                # Filter data by date
                mask = (dates >= start_date)
                dates_filtered = dates[mask]
                prices_filtered = prices[mask]
                
                # Update plot with filtered data
                self.ax.clear()
                self.ax.plot(dates_filtered, prices_filtered, label='Precio', linewidth=2)
                
                # Filter indicators if available
                if self.bot.market_data.indicators and self.show_sma_var.get():
                    sma_short = self.bot.market_data.indicators.get('sma_short')
                    sma_long = self.bot.market_data.indicators.get('sma_long')
                    
                    if sma_short is not None and len(sma_short) == len(dates):
                        sma_short_filtered = sma_short[mask]
                        self.ax.plot(dates_filtered, sma_short_filtered, label='SMA Corta', 
                                   linestyle='--', linewidth=1.5)
                    
                    if sma_long is not None and len(sma_long) == len(dates):
                        sma_long_filtered = sma_long[mask]
                        self.ax.plot(dates_filtered, sma_long_filtered, label='SMA Larga', 
                                   linestyle='-.', linewidth=1.5)
                
                # Add Bollinger Bands if selected
                if self.bot.market_data.indicators and self.show_bb_var.get():
                    bb_upper = self.bot.market_data.indicators.get('bb_upper')
                    bb_middle = self.bot.market_data.indicators.get('bb_middle')
                    bb_lower = self.bot.market_data.indicators.get('bb_lower')
                    
                    if bb_upper is not None and len(bb_upper) == len(dates):
                        bb_upper_filtered = bb_upper[mask]
                        bb_middle_filtered = bb_middle[mask]
                        bb_lower_filtered = bb_lower[mask]
                        
                        self.ax.plot(dates_filtered, bb_upper_filtered, 'k--', alpha=0.3, linewidth=1)
                        self.ax.plot(dates_filtered, bb_middle_filtered, 'k--', alpha=0.3, linewidth=1)
                        self.ax.plot(dates_filtered, bb_lower_filtered, 'k--', alpha=0.3, linewidth=1)
                        self.ax.fill_between(dates_filtered, bb_upper_filtered, bb_lower_filtered, 
                                          alpha=0.1, color='gray')
            
            # Format chart with improved styling
            self.ax.set_title(f"{SYMBOL} - Precio y Señales", fontsize=14, fontweight='bold')
            self.ax.set_xlabel("Fecha", fontsize=12)
            self.ax.set_ylabel("Precio (USD)", fontsize=12)
            self.ax.legend()
            
            # Format x-axis dates
            self.figure.autofmt_xdate()
            
            # Draw canvas
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating chart: {e}")
            import traceback
            traceback.print_exc()
    
    def toggle_bot(self):
        """Toggle bot running state"""
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()
    
    def start_bot(self):
        """Start the bot"""
        if not self.is_running:
            self.is_running = True
            self.start_button.config(text="Detener Bot")
            self.analyze_button.config(state=tk.NORMAL)
            self.status_var.set("Bot en ejecución...")
            
            # Start bot in a separate thread
            self.bot_thread = threading.Thread(target=self._run_bot)
            self.bot_thread.daemon = True
            self.bot_thread.start()
    
    def stop_bot(self):
        """Stop the bot"""
        if self.is_running:
            self.is_running = False
            self.start_button.config(text="Iniciar Bot")
            self.analyze_button.config(state=tk.DISABLED)
            self.status_var.set("Bot detenido")
    
    def _run_bot(self):
        """Run the bot in a separate thread"""
        try:
            # Initialize bot
            success = self.bot.initialize()
            
            if not success:
                self.status_var.set("Error al inicializar el bot")
                self.stop_bot()
                return
            
            # Update UI with initial data
            self.update_history_tab()
            self.update_signals_tab()
            self.update_chart()
            
            # Run continuously
            while self.is_running:
                # Analyze market
                self.bot.analyze_market()
                
                # Update UI
                self.root.after(0, self.update_history_tab)
                self.root.after(0, self.update_signals_tab)
                self.root.after(0, self.update_chart)
                
                # Wait for next update
                for _ in range(self.update_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
            
        except Exception as e:
            print(f"Error in bot thread: {e}")
            import traceback
            traceback.print_exc()
            
            # Update status
            self.status_var.set(f"Error: {str(e)}")
            
            # Stop bot
            self.root.after(0, self.stop_bot)
    
    def force_analysis(self):
        """Force an immediate analysis"""
        if self.is_running:
            threading.Thread(target=self.bot.analyze_market).start()
            self.status_var.set("Análisis forzado iniciado...")
    
    def on_price_update(self, price):
        """Callback for price updates"""
        self.price_var.set(f"Precio: {format_price(price)}")
    
    def on_analysis_complete(self, result):
        """Callback for analysis completion"""
        if result:
            time_str = result['time'].strftime("%H:%M:%S")
            self.analysis_var.set(f"Último análisis: {time_str}")
    
    def on_position_update(self, position):
        """Callback for position updates"""
        if position.active:
            self.position_var.set(f"Posición: {position.symbol} a {format_price(position.entry_price)}")
        else:
            self.position_var.set("Posición: No hay posición activa")
            self.pl_var.set("P/L: N/A")
        
        # Update history and chart
        self.root.after(0, self.update_history_tab)
        self.root.after(0, self.update_chart)
    
    def on_signal(self, signal):
        """Callback for signals"""
        # Update signals tab
        self.root.after(0, self.update_signals_tab)

def start_ui(bot):
    """Start the UI"""
    root = tk.Tk()
    app = TradingBotUI(root, bot)
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, app))
    root.mainloop()

def on_closing(root, app):
    """Handle window closing"""
    # Restore original stdout
    import sys
    sys.stdout = app.original_stdout
    
    # Stop bot
    app.stop_bot()
    
    # Destroy window
    root.destroy()

if __name__ == "__main__":
    # This allows running the UI directly for testing
    from main import TradingBot
    bot = TradingBot()
    start_ui(bot)
